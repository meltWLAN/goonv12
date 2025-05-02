import logging
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time
import os

class SimpleStockProvider:
    """
    A simplified stock data provider using Tushare
    """
    
    def __init__(self, token=None):
        """
        Initialize the provider with Tushare token
        
        Args:
            token: Tushare API token
        """
        self.logger = logging.getLogger('SimpleStockProvider')
        self.token = token or os.environ.get('TUSHARE_TOKEN')
        self.cache = {}
        
        # Initialize Tushare
        try:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            self.logger.info("Tushare API initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Tushare API: {str(e)}")
            self.pro = None
        
    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """
        Get historical stock data
        
        Args:
            symbol: Stock symbol with market suffix (e.g., '000001.SZ')
            start_date: Start date (YYYYMMDD format)
            end_date: End date (YYYYMMDD format)
            
        Returns:
            DataFrame of stock data
        """
        # Calculate default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
        # Check cache
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if cache_key in self.cache:
            self.logger.info(f"Using cached data for {symbol}")
            return self.cache[cache_key]
            
        if not self.pro:
            self.logger.error("Tushare API not initialized")
            return pd.DataFrame()
            
        try:
            # Get stock data with technical indicators
            self.logger.info(f"Retrieving data for {symbol} from {start_date} to {end_date}")
            df = self.pro.stk_factor(ts_code=symbol, start_date=start_date, end_date=end_date)
            
            if df is not None and not df.empty:
                self.logger.info(f"Retrieved {len(df)} rows of data")
                self.cache[cache_key] = df
                return df
                
            # Fall back to daily data if stk_factor doesn't return data
            self.logger.info("Falling back to daily data")
            df = self.pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            
            if df is not None and not df.empty:
                self.logger.info(f"Retrieved {len(df)} rows of daily data")
                self.cache[cache_key] = df
                return df
                
            self.logger.warning(f"No data available for {symbol}")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error retrieving data: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol=None):
        """
        Get basic stock information
        
        Args:
            symbol: Stock symbol (optional, if None returns all stocks)
            
        Returns:
            DataFrame with stock information
        """
        try:
            if symbol:
                info = self.pro.stock_basic(ts_code=symbol)
            else:
                info = self.pro.stock_basic()
                
            return info
            
        except Exception as e:
            self.logger.error(f"Error retrieving stock info: {str(e)}")
            return pd.DataFrame()
    
    def get_technical_indicators(self, df):
        """
        Calculate technical indicators for a stock
        
        Args:
            df: DataFrame with stock data
            
        Returns:
            DataFrame with added technical indicators
        """
        if df is None or df.empty:
            return df
            
        # Check if we already have indicators from stk_factor
        if 'macd' in df.columns and 'rsi_6' in df.columns:
            return df
            
        # Otherwise, we need to calculate them
        # This would be a simplified implementation
        # In a real system, you would use proper technical analysis libraries
        
        return df


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Simple Stock Provider')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--symbol', type=str, default='000001.SZ', help='Stock symbol')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create provider
    provider = SimpleStockProvider(token=args.token)
    
    # Get stock info
    info = provider.get_stock_info(args.symbol)
    if not info.empty:
        print(f"\nStock Info for {args.symbol}:")
        print(info)
    
    # Get stock data
    data = provider.get_stock_data(args.symbol)
    if not data.empty:
        print(f"\nStock Data for {args.symbol}:")
        print(f"Shape: {data.shape}")
        print("\nFirst 5 rows:")
        print(data.head())
        
        print("\nAvailable columns:")
        for col in data.columns:
            print(f"  - {col}")
        
        if 'close' in data.columns:
            recent_prices = data.sort_values('trade_date', ascending=False)[['trade_date', 'close']].head(5)
            print("\nMost recent prices:")
            print(recent_prices)
            
        if 'macd' in data.columns and 'rsi_6' in data.columns:
            indicators = data.sort_values('trade_date', ascending=False)[['trade_date', 'macd', 'rsi_6', 'kdj_k']].head(5)
            print("\nTechnical indicators:")
            print(indicators)