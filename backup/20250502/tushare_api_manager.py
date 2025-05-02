import tushare as ts
import pandas as pd
import time
import logging
import os
from datetime import datetime, timedelta
import json
import requests
from functools import wraps

class TushareAPIManager:
    """
    A utility class to manage Tushare API connections and requests.
    Includes features like rate limiting, caching, and error handling.
    """
    
    def __init__(self, token=None, cache_dir='./cache', log_level=logging.INFO):
        """
        Initialize the Tushare API Manager.
        
        Args:
            token (str): Tushare API token. If None, will attempt to load from environment.
            cache_dir (str): Directory to store cached data.
            log_level: Logging level.
        """
        # Setup logging
        self.logger = logging.getLogger('TushareAPIManager')
        self.logger.setLevel(log_level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Get token
        self.token = token or os.environ.get('TUSHARE_TOKEN')
        if not self.token:
            self.logger.warning("No Tushare token provided. Please set via init or TUSHARE_TOKEN environment variable.")
        else:
            self.logger.info(f"Initializing with token: {self.token[:4]}...{self.token[-4:]}")
            ts.set_token(self.token)
            
        self.pro = ts.pro_api()
        
        # Cache settings
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        
        # API endpoints we support with their cache settings (in seconds)
        self.api_endpoints = {
            'daily': {'cache_duration': 86400},  # 1 day
            'weekly': {'cache_duration': 604800},  # 1 week
            'monthly': {'cache_duration': 2592000},  # 30 days
            'stock_basic': {'cache_duration': 86400},  # 1 day
            'stk_factor': {'cache_duration': 86400},  # 1 day
            'trade_cal': {'cache_duration': 604800},  # 1 week
            'index_daily': {'cache_duration': 86400},  # 1 day
        }
    
    def rate_limit(func):
        """Decorator to handle rate limiting between API calls"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
            return func(self, *args, **kwargs)
        return wrapper
    
    def get_cache_path(self, endpoint, **params):
        """Generate a cache file path based on endpoint and parameters"""
        # Create a cache key from the parameters
        params_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()) if k not in ['fields'])
        filename = f"{endpoint}_{params_str}.json"
        # Replace any invalid characters
        filename = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
        return os.path.join(self.cache_dir, filename)
    
    def is_cache_valid(self, cache_path, endpoint):
        """Check if cache file exists and is not expired"""
        if not os.path.exists(cache_path):
            return False
            
        # Check file modification time
        file_mtime = os.path.getmtime(cache_path)
        cache_age = time.time() - file_mtime
        
        # Get cache duration for this endpoint
        cache_duration = self.api_endpoints.get(endpoint, {}).get('cache_duration', 86400)
        
        return cache_age < cache_duration
    
    def load_from_cache(self, cache_path):
        """Load data from cache file"""
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Convert back to DataFrame
            if data:
                df = pd.DataFrame(data)
                self.logger.debug(f"Loaded {len(df)} rows from cache: {cache_path}")
                return df
        except Exception as e:
            self.logger.warning(f"Error loading from cache: {e}")
        
        return None
    
    def save_to_cache(self, cache_path, df):
        """Save data to cache file"""
        if df is None or df.empty:
            self.logger.debug("No data to cache")
            return
            
        try:
            # Convert DataFrame to list of dicts for JSON serialization
            data = df.to_dict('records')
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            
            self.logger.debug(f"Cached {len(df)} rows to: {cache_path}")
        except Exception as e:
            self.logger.warning(f"Error saving to cache: {e}")
    
    @rate_limit
    def call_api(self, endpoint, use_cache=True, **params):
        """
        Call Tushare API with built-in caching and rate limiting.
        
        Args:
            endpoint (str): The Tushare API endpoint to call
            use_cache (bool): Whether to use and update cache
            **params: Parameters to pass to the Tushare API
            
        Returns:
            pandas.DataFrame: The API response data
        """
        # Check if endpoint is supported
        if endpoint not in self.api_endpoints:
            self.logger.warning(f"Unsupported endpoint: {endpoint}")
        
        # Handle caching
        cache_path = None
        if use_cache:
            cache_path = self.get_cache_path(endpoint, **params)
            if self.is_cache_valid(cache_path, endpoint):
                cached_data = self.load_from_cache(cache_path)
                if cached_data is not None:
                    self.logger.info(f"Using cached data for {endpoint}")
                    return cached_data
        
        # Make API call
        try:
            self.logger.info(f"Calling Tushare API: {endpoint} with params: {params}")
            api_method = getattr(self.pro, endpoint)
            df = api_method(**params)
            
            # Cache the result if requested
            if use_cache and cache_path and df is not None and not df.empty:
                self.save_to_cache(cache_path, df)
                
            return df
        except Exception as e:
            self.logger.error(f"API call failed: {endpoint}, error: {str(e)}")
            return None
    
    def get_daily_data(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """Get daily stock data"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        return self.call_api('daily', ts_code=ts_code, 
                             start_date=start_date, end_date=end_date, 
                             use_cache=use_cache)
    
    def get_stk_factor(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """Get stock factor data with technical indicators"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        return self.call_api('stk_factor', ts_code=ts_code, 
                             start_date=start_date, end_date=end_date, 
                             use_cache=use_cache)
    
    def get_stock_basic(self, market=None):
        """Get basic information about stocks"""
        params = {}
        if market:
            params['market'] = market
            
        return self.call_api('stock_basic', **params)
    
    def get_index_daily(self, ts_code, start_date=None, end_date=None):
        """Get daily index data"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        return self.call_api('index_daily', ts_code=ts_code,
                             start_date=start_date, end_date=end_date)
    
    def get_trade_cal(self, exchange='SSE', start_date=None, end_date=None):
        """Get trade calendar"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y%m%d')
            
        return self.call_api('trade_cal', exchange=exchange,
                             start_date=start_date, end_date=end_date)
    
    def validate_token(self):
        """Validate if the token is working by making a simple API call"""
        try:
            # Try to get just 1 row of stock basics
            df = self.pro.stock_basic(limit=1)
            if df is not None and not df.empty:
                self.logger.info("Token validation: SUCCESS")
                return True
            else:
                self.logger.warning("Token validation: FAILED - Empty response")
                return False
        except Exception as e:
            self.logger.error(f"Token validation: FAILED - {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Tushare API Manager')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--ts_code', type=str, default='000001.SZ', help='Stock code')
    args = parser.parse_args()
    
    # Initialize with logging
    logging.basicConfig(level=logging.INFO)
    
    # Create API manager
    api = TushareAPIManager(token=args.token)
    
    # Validate token
    if api.validate_token():
        print(f"Token valid, proceeding with tests for {args.ts_code}")
        
        # Test basic stock info
        stock_info = api.get_stock_basic()
        if stock_info is not None:
            print(f"Retrieved {len(stock_info)} stocks basic info")
            if not stock_info.empty:
                print(stock_info[stock_info['ts_code'] == args.ts_code][['ts_code', 'name', 'industry']].iloc[0])
        
        # Test stock factors
        factors = api.get_stk_factor(ts_code=args.ts_code, start_date='20240301')
        if factors is not None and not factors.empty:
            print(f"Retrieved {len(factors)} days of factor data")
            print(factors[['trade_date', 'close', 'macd', 'rsi_6']].head())
    else:
        print("Token validation failed, please check your token") 