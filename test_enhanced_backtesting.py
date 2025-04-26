import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock

# 导入被测试的模块
from enhanced_backtesting import EnhancedBacktester, BacktestResult, TradeRecord

class TestEnhancedBacktester(unittest.TestCase):
    """测试增强版回测系统的核心功能"""
    
    def setUp(self):
        """每个测试前设置回测环境"""
        self.backtester = EnhancedBacktester(initial_capital=1000000.0)
        # 生成测试数据
        self.test_data = self._generate_test_data()
        
    def _generate_test_data(self, days=60):
        """生成模拟股票数据用于测试"""
        dates = pd.date_range(end=datetime.now(), periods=days)
        # 创建一个有趋势的价格序列
        base_price = 100
        noise = np.random.normal(0, 1, days)
        trend = np.linspace(0, 15, days)  # 上升趋势
        prices = base_price + trend + noise.cumsum()
        
        # 创建交易量数据
        volume_base = 10000
        volume = volume_base + np.random.randint(0, 5000, days)
        volume_spikes = np.random.randint(0, 10, days)  # 随机生成量能放大点
        volume[volume_spikes > 8] *= 2  # 10%的天数交易量翻倍
        
        # 构建DataFrame
        df = pd.DataFrame({
            '日期': dates,
            '开盘': prices * 0.995,
            '收盘': prices,
            '最高': prices * 1.01,
            '最低': prices * 0.99,
            '成交量': volume,
        })
        
        # 计算技术指标
        close = df['收盘']
        df['RSI'] = self._calculate_rsi(close)
        df['ATR'] = self._calculate_atr(df)
        df['Volume_MA'] = df['成交量'].rolling(20).mean()
        
        return df
        
    def _calculate_rsi(self, prices, period=14):
        """计算RSI技术指标"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            up = (up * (period-1) + upval) / period
            down = (down * (period-1) + downval) / period
            rs = up/down if down != 0 else 0
            rsi[i] = 100. - 100./(1. + rs)
        return rsi
    
    def _calculate_atr(self, data, period=14):
        """计算ATR技术指标"""
        high = data['最高']
        low = data['最低']
        close = data['收盘']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
        
    def test_initialization(self):
        """测试回测系统初始化"""
        self.assertEqual(self.backtester.initial_capital, 1000000.0)
        self.assertEqual(self.backtester.current_capital, 1000000.0)
        self.assertEqual(len(self.backtester.positions), 0)
        self.assertEqual(len(self.backtester.trades), 0)
        
    def test_execute_trade_buy(self):
        """测试买入交易执行"""
        timestamp = datetime.now()
        symbol = "TEST"
        action = "buy"
        price = 100.0
        volume = 1000
        
        # 执行买入交易
        trade = self.backtester.execute_trade(
            timestamp, symbol, action, price, volume,
            signal_quality=0.8, market_condition="normal"
        )
        
        # 验证交易记录
        self.assertIsNotNone(trade)
        self.assertEqual(trade.action, "buy")
        self.assertEqual(trade.symbol, symbol)
        self.assertEqual(trade.price, price)
        self.assertEqual(trade.volume, volume)
        
        # 验证持仓更新
        self.assertIn(symbol, self.backtester.positions)
        self.assertEqual(self.backtester.positions[symbol]["volume"], volume)
        
        # 验证资金变动
        expected_capital = 1000000.0 - (price * volume)
        self.assertAlmostEqual(self.backtester.current_capital, expected_capital, delta=0.01)
    
    def test_execute_trade_sell(self):
        """测试卖出交易执行"""
        # 先买入股票
        timestamp = datetime.now()
        symbol = "TEST"
        buy_price = 100.0
        volume = 1000
        
        self.backtester.execute_trade(
            timestamp, symbol, "buy", buy_price, volume,
            signal_quality=0.8, market_condition="normal"
        )
        
        # 然后卖出
        sell_price = 110.0
        sell_timestamp = timestamp + timedelta(days=5)
        
        trade = self.backtester.execute_trade(
            sell_timestamp, symbol, "sell", sell_price, volume,
            signal_quality=0.8, market_condition="normal"
        )
        
        # 验证交易记录
        self.assertIsNotNone(trade)
        self.assertEqual(trade.action, "sell")
        self.assertEqual(trade.symbol, symbol)
        self.assertEqual(trade.price, sell_price)
        self.assertEqual(trade.volume, volume)
        
        # 验证持仓更新 (应该为空)
        self.assertIn(symbol, self.backtester.positions)
        self.assertEqual(self.backtester.positions[symbol]["volume"], 0)
        
        # 验证资金变动和利润
        expected_profit = (sell_price - buy_price) * volume
        expected_capital = 1000000.0 + expected_profit
        self.assertAlmostEqual(self.backtester.current_capital, expected_capital, delta=0.01)
        self.assertAlmostEqual(self.backtester.total_profit, expected_profit, delta=0.01)
    
    def test_calculate_metrics(self):
        """测试回测指标计算"""
        # 执行一系列交易
        symbol = "TEST"
        self.backtester.execute_trade(datetime.now(), symbol, "buy", 100.0, 1000)
        self.backtester.execute_trade(datetime.now() + timedelta(days=5), symbol, "sell", 110.0, 1000)
        self.backtester.execute_trade(datetime.now() + timedelta(days=10), symbol, "buy", 105.0, 1000)
        self.backtester.execute_trade(datetime.now() + timedelta(days=15), symbol, "sell", 95.0, 1000)
        
        # 计算指标
        results = self.backtester.calculate_metrics()
        
        # 验证结果是否符合预期
        self.assertIsInstance(results, BacktestResult)
        self.assertEqual(results.trade_count, 4)
        self.assertEqual(results.win_count, 1)  # 1次盈利
        self.assertEqual(results.loss_count, 1)  # 1次亏损
        self.assertAlmostEqual(results.win_rate, 0.5, delta=0.01)  # 胜率50%
        
        # 验证总收益
        expected_profit = (110.0 - 100.0) * 1000 + (95.0 - 105.0) * 1000
        self.assertAlmostEqual(results.total_profit, expected_profit, delta=0.01)
    
    def test_dynamic_position_sizing(self):
        """测试动态仓位管理"""
        symbol = "TEST"
        price = 100.0
        
        # 高质量信号应该有较大仓位
        position_high = self.backtester.calculate_position_size(price, 0.9, "bullish")
        
        # 低质量信号应该有较小仓位
        position_low = self.backtester.calculate_position_size(price, 0.3, "neutral")
        
        # 验证高质量信号的仓位大于低质量信号
        self.assertGreater(position_high, position_low)
        
        # 熊市环境应该有更小的仓位
        position_bearish = self.backtester.calculate_position_size(price, 0.9, "bearish")
        self.assertLess(position_bearish, position_high)
    
    def test_trailing_stop(self):
        """测试移动止损功能"""
        symbol = "TEST"
        buy_price = 100.0
        
        # 买入股票
        self.backtester.execute_trade(datetime.now(), symbol, "buy", buy_price, 1000)
        
        # 设置移动止损
        self.backtester.active_trailing_stops[symbol] = buy_price * 0.95
        
        # 测试止损更新 - 价格上涨时
        current_price = 110.0
        new_stop = self.backtester.update_trailing_stop(symbol, current_price)
        expected_stop = 110.0 * 0.95  # 95%的当前价格
        self.assertAlmostEqual(new_stop, expected_stop, delta=0.01)
        
        # 测试止损触发 - 价格下跌到止损以下
        # 注意：实际交易执行由较高级别的方法处理，这里只测试止损点计算
        current_price = 103.0  # 低于上一个止损位
        is_triggered = current_price < new_stop
        self.assertFalse(is_triggered)  # 还未触发
        
        current_price = 102.0
        is_triggered = current_price < new_stop
        self.assertTrue(is_triggered)  # 已触发
    
    def test_kdj_strategy(self):
        """测试KDJ策略回测功能"""
        # 执行KDJ策略回测
        symbol = "TEST_STOCK"
        result = self.backtester.backtest_kdj_strategy(self.test_data, symbol)
        
        # 验证回测结果
        self.assertIsNotNone(result)
        self.assertIsInstance(result, BacktestResult)
        self.assertGreater(len(result.trades), 0, "策略应该产生至少一笔交易")

# 入口点
if __name__ == "__main__":
    unittest.main() 