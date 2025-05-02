import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import time
import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Mock PyQt5 before importing the system
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtWidgets'] = MagicMock()
sys.modules['PyQt5.QtGui'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()

from visual_stock_system import VisualStockSystem

# Mock akshare globally for tests that need it
mock_ak = MagicMock()
sys.modules['akshare'] = mock_ak

class TestVisualStockSystemData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the VisualStockSystem instance once for all tests in this class."""
        # We don't need a real Qt application for these tests
        cls.system = VisualStockSystem()

    def setUp(self):
        """Reset mocks and caches before each test."""
        mock_ak.reset_mock()
        # Clear caches if necessary
        self.system._stock_data_cache.clear()
        self.system._stock_names_cache.clear()
        self.system._last_api_call = 0 # Reset API call timer

    @patch('visual_stock_system.ak.stock_zh_a_hist')
    def test_get_stock_data_success(self, mock_get_hist):
        """Test successful data retrieval for a valid symbol."""
        # Arrange: Mock the akshare function to return sample data
        sample_data = pd.DataFrame({
            '日期': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            '开盘': [10.0, 10.2, 10.5],
            '收盘': [10.1, 10.4, 10.6],
            '最高': [10.3, 10.5, 10.7],
            '最低': [9.9, 10.1, 10.4],
            '成交量': [10000, 12000, 11000],
            '成交额': [100000, 124000, 115000],
            '振幅': [4.0, 3.9, 2.9],
            '涨跌幅': [1.0, 2.97, 1.92],
            '涨跌额': [0.1, 0.3, 0.2],
            '换手率': [1.0, 1.2, 1.1]
        })
        mock_get_hist.return_value = sample_data.copy() # Return a copy to avoid modification issues

        # Act: Call the function under test
        df = self.system.get_stock_data('600000.SH', start_date='20230101', end_date='20230103')

        # Assert: Check if the data is processed correctly
        self.assertIsNotNone(df)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        # Corrected expected column names based on the function's renaming logic
        self.assertListEqual(list(df.columns), ['trade_date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_chg', 'change'])
        # Corrected expected date format
        self.assertEqual(df['trade_date'].iloc[0], '20230101')
        self.assertEqual(df['close'].iloc[-1], 10.6)
        mock_get_hist.assert_called_once_with(symbol='600000', period='daily', start_date='20230101', end_date='20230103', adjust='qfq')

        # Test caching
        mock_get_hist.reset_mock()
        df_cached = self.system.get_stock_data('600000.SH', start_date='20230101', end_date='20230103')
        self.assertIsNotNone(df_cached)
        pd.testing.assert_frame_equal(df, df_cached)
        mock_get_hist.assert_not_called() # Should not call API again due to cache

    def test_get_stock_data_invalid_symbol_format(self):
        """Test data retrieval with an invalid symbol format."""
        with self.assertRaisesRegex(ValueError, "股票代码格式错误：12345\n正确格式示例"):
            self.system.get_stock_data('12345')
        with self.assertRaisesRegex(ValueError, "股票代码格式错误：ABCDEF.XYZ\n正确格式示例"):
            self.system.get_stock_data('ABCDEF.XYZ')

    def test_get_stock_data_invalid_date_format(self):
        """Test data retrieval with invalid date formats."""
        with self.assertRaisesRegex(ValueError, "起始日期格式错误.*支持的格式：YYYYMMDD或YYYY-MM-DD"):
            self.system.get_stock_data('000001.SZ', start_date='2023/01/01')
        with self.assertRaisesRegex(ValueError, "结束日期格式错误.*支持的格式：YYYYMMDD或YYYY-MM-DD"):
            self.system.get_stock_data('000001.SZ', end_date='01-01-2023')

    def test_get_stock_data_start_after_end_date(self):
        """Test data retrieval when start date is after end date."""
        with self.assertRaisesRegex(ValueError, "起始日期不能晚于结束日期"):
            self.system.get_stock_data('000001.SZ', start_date='20230105', end_date='20230101')

    @patch('visual_stock_system.ak.stock_zh_a_hist')
    def test_get_stock_data_api_failure(self, mock_get_hist):
        """Test data retrieval when the primary API call fails."""
        # Arrange: Mock the API to raise an exception
        mock_get_hist.side_effect = Exception("API Error")

        # Act: Call the function
        # Expecting it to print an error and return None (or handle fallback)
        # For now, let's assume it returns None after failure
        result = self.system.get_stock_data('000001.SZ')

        # Assert
        self.assertIsNone(result) # Or check for specific fallback behavior if implemented
        mock_get_hist.assert_called_once()

    @patch('visual_stock_system.ak.stock_zh_a_hist')
    def test_get_stock_data_empty_result(self, mock_get_hist):
        """Test data retrieval when the API returns an empty DataFrame."""
        # Arrange: Mock the API to return an empty DataFrame
        mock_get_hist.return_value = pd.DataFrame()

        # Act & Assert: Expect a ValueError indicating no data
        with self.assertRaisesRegex(ValueError, "未能获取到000001.SZ的交易数据"):
            self.system.get_stock_data('000001.SZ')
        mock_get_hist.assert_called_once()

    def test_get_stock_data_numeric_symbol_conversion(self):
        """Test automatic conversion of 6-digit numeric symbols."""
        with patch.object(self.system, 'get_stock_data', wraps=self.system.get_stock_data) as spy_get_data:
            try:
                self.system.get_stock_data('600000') # SH
                spy_get_data.assert_called_with('600000.SH', start_date=None, end_date=None, limit=None)
            except ValueError: # Ignore ValueErrors from potential API failures in this test
                pass
            spy_get_data.reset_mock()
            try:
                self.system.get_stock_data('000001') # SZ
                spy_get_data.assert_called_with('000001.SZ', start_date=None, end_date=None, limit=None)
            except ValueError:
                pass
            spy_get_data.reset_mock()
            try:
                self.system.get_stock_data('300001') # SZVENTA
                spy_get_data.assert_called_with('300001.SZ', start_date=None, end_date=None, limit=None)
            except ValueError:
                pass
            spy_get_data.reset_mock()
            try:
                self.system.get_stock_data('830001') # BJ
                spy_get_data.assert_called_with('830001.BJ', start_date=None, end_date=None, limit=None)
            except ValueError:
                pass

    @patch('visual_stock_system.ak.stock_individual_info_em')
    def test_get_stock_name_success(self, mock_get_info):
        """Test successful retrieval of stock name."""
        # Arrange
        mock_get_info.return_value = pd.DataFrame({'名称': ['测试股票']})
        symbol = '600000.SH'

        # Act
        name = self.system.get_stock_name(symbol)

        # Assert
        self.assertEqual(name, '测试股票')
        mock_get_info.assert_called_once_with(symbol='600000')
        # Check cache
        self.assertIn(symbol, self.system._stock_names_cache)
        self.assertEqual(self.system._stock_names_cache[symbol][1], '测试股票')

    @patch('visual_stock_system.ak.stock_individual_info_em')
    def test_get_stock_name_caching(self, mock_get_info):
        """Test caching mechanism for stock names."""
        # Arrange
        mock_get_info.return_value = pd.DataFrame({'名称': ['缓存测试']})
        symbol = '000001.SZ'

        # Act: First call - should call API and cache
        name1 = self.system.get_stock_name(symbol)

        # Assert first call
        self.assertEqual(name1, '缓存测试')
        mock_get_info.assert_called_once_with(symbol='000001')

        # Act: Second call - should use cache
        mock_get_info.reset_mock() # Reset mock before second call
        name2 = self.system.get_stock_name(symbol)

        # Assert second call
        self.assertEqual(name2, '缓存测试')
        mock_get_info.assert_not_called() # API should not be called again

    @patch('visual_stock_system.ak.stock_individual_info_em')
    def test_get_stock_name_api_failure(self, mock_get_info):
        """Test behavior when akshare API fails to get stock name."""
        # Arrange
        mock_get_info.side_effect = Exception("API Error")
        symbol = '300001.SZ'

        # Act
        name = self.system.get_stock_name(symbol)

        # Assert: Should return the original symbol on failure after retries
        self.assertEqual(name, symbol)
        self.assertEqual(mock_get_info.call_count, 3) # Check if retries happened

    @patch('visual_stock_system.ak.stock_individual_info_em')
    def test_get_stock_name_empty_result(self, mock_get_info):
        """Test behavior when akshare API returns empty info."""
        # Arrange
        mock_get_info.return_value = pd.DataFrame() # Empty result
        symbol = '688001.SH'

        # Act
        name = self.system.get_stock_name(symbol)

        # Assert: Should return the original symbol if no name found
        self.assertEqual(name, symbol)
        mock_get_info.assert_called_once_with(symbol='688001')

    def test_analyze_momentum_success(self):
        """Test momentum analysis with sufficient valid data."""
        # Arrange: Create sample DataFrame with enough data for EMA21 and MACD
        dates = pd.date_range(start='2023-01-01', periods=35, freq='D') # Need more than 21 for EMA, more for MACD
        data = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'open': np.random.rand(35) * 10 + 10,
            'high': np.random.rand(35) * 2 + 11,
            'low': np.random.rand(35) * 2 + 9,
            'close': np.linspace(10, 15, 35), # Simple linear trend for predictability
            'volume': np.random.randint(10000, 50000, 35)
        })
        data = data.set_index('trade_date') # Set index for talib

        # Act
        analyzed_df = self.system.analyze_momentum(data.copy()) # Pass a copy

        # Assert
        self.assertIsNotNone(analyzed_df)
        self.assertIn('EMA21', analyzed_df.columns)
        self.assertIn('MACD', analyzed_df.columns)
        self.assertIn('MACD_Signal', analyzed_df.columns)
        self.assertIn('MACD_Hist', analyzed_df.columns)
        self.assertFalse(analyzed_df['EMA21'].isnull().all()) # Check EMA is calculated
        self.assertFalse(analyzed_df['MACD'].isnull().all())   # Check MACD is calculated

    def test_analyze_momentum_insufficient_data(self):
        """Test momentum analysis with insufficient data."""
        # Arrange: Create sample DataFrame with less than 21 data points
        dates = pd.date_range(start='2023-01-01', periods=15, freq='D')
        data = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'close': np.linspace(10, 12, 15)
        })
        data = data.set_index('trade_date')

        # Act
        analyzed_df = self.system.analyze_momentum(data.copy())

        # Assert: Should return None or original df without indicators
        # Based on current implementation, it returns the original df without indicators
        # Let's refine this test based on expected behavior (e.g., return None or raise error)
        # Assuming it should return the original df for now, but add indicators as NaN
        self.assertIsNotNone(analyzed_df)
        self.assertNotIn('EMA21', analyzed_df.columns) # Or check if all NaNs if column is added
        self.assertNotIn('MACD', analyzed_df.columns)

    def test_analyze_momentum_with_nan(self):
        """Test momentum analysis when input data contains NaN values."""
        # Arrange: Create data with NaNs
        dates = pd.date_range(start='2023-01-01', periods=35, freq='D')
        close_prices = np.linspace(10, 15, 35)
        close_prices[5] = np.nan # Introduce a NaN
        data = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'close': close_prices
        })
        data = data.set_index('trade_date')

        # Act
        analyzed_df = self.system.analyze_momentum(data.copy())

        # Assert: TA-Lib should handle NaNs gracefully (propagate them)
        self.assertIsNotNone(analyzed_df)
        self.assertTrue(analyzed_df['EMA21'].isnull().any())
        self.assertTrue(analyzed_df['MACD'].isnull().any())

    # TODO: Add tests for analyze_volume_price
    # TODO: Add tests for check_trend
    # TODO: Add tests for analyze_stock (integration)
    # TODO: Add tests for plot_stock_chart (might need visual inspection or mocking plotly)

if __name__ == '__main__':
    unittest.main()