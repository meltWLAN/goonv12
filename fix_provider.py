import os
import re
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_provider')

def main():
    """
    Fix the initialization issue in the ChinaStockProvider class by directly
    editing the file and replacing the __init__ method.
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'china_stock_provider.py')
    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    
    # Create backup
    logger.info(f"Creating backup at {backup_path}")
    try:
        with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return 1
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define the new __init__ method
    new_init = '''    def __init__(self, tushare_token=None, use_disk_cache=True):
        """初始化数据提供者
        
        Args:
            tushare_token: Tushare API令牌
            use_disk_cache: 是否使用磁盘缓存
        """
        self.logger = logging.getLogger('ChinaStockProvider')
        self.memory_cache = {}  # 内存缓存
        
        # 设置数据源
        self.data_sources = ['tushare', 'akshare']  # 将tushare优先置于akshare之前
        
        # API调用间隔
        self.api_cooldown = 0.5
        self.last_api_call = 0
        
        # 初始化Tushare
        self.tushare_token = tushare_token or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.tushare_pro = None
        try:
            ts.set_token(self.tushare_token)
            self.tushare_pro = ts.pro_api()
            self.logger.info("Tushare API初始化成功")
            self.current_source = 'tushare'  # 默认使用tushare
            
            # Initialize the TushareAPIManager for improved API handling
            try:
                from tushare_api_manager import TushareAPIManager
                self.tushare_manager = TushareAPIManager(token=self.tushare_token, cache_dir='./cache/tushare')
                self.logger.info("TushareAPIManager initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize TushareAPIManager: {str(e)}")
                self.tushare_manager = None
                
        except Exception as e:
            self.logger.error(f"Tushare API初始化失败: {str(e)}")
            self.current_source = 'akshare'  # 如果Tushare失败，使用akshare作为备选
            self.tushare_manager = None
        
        self._init_column_mappings()
        self._init_api_handlers()
        self.price_limit_ratios = {
            'NORMAL': 0.1,  # 普通股票
            'ST': 0.05,     # ST股票
            'STAR': 0.2,    # 科创板
            'CREATE': 0.2   # 创业板
        }
        
        self.logger.info(f"ChinaStockProvider初始化完成，当前数据源: {self.current_source}, 可用数据源: {self.get_available_sources()}")'''
    
    # Find and replace the __init__ method
    init_pattern = re.compile(r'    def __init__\([^)]*\):[^\n]*\n(?:\s+[^\n]*\n)*?(?=\s{4}def|\s*$)', re.MULTILINE)
    match = init_pattern.search(content)
    
    if match:
        # Replace the __init__ method
        new_content = content[:match.start()] + new_init + content[match.end():]
        
        # Write the modified content back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully replaced the __init__ method")
        
        # Also fix _get_stock_data_tushare method to handle missing tushare_manager
        # New method implementation
        new_tushare_method = '''    def _get_stock_data_tushare(self, symbol, start_date, end_date):
        # Use the TushareAPIManager for better caching and error handling if available
        if hasattr(self, 'tushare_manager') and self.tushare_manager is not None:
            try:
                # Get stock data with technical indicators
                df = self.tushare_manager.get_stk_factor(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is not None and not df.empty:
                    self.logger.info(f"Retrieved {len(df)} days of data from Tushare for {symbol}")
                    return df
                
                # Fallback to basic daily data if stk_factor is unavailable
                df = self.tushare_manager.get_daily_data(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is not None and not df.empty:
                    self.logger.info(f"Retrieved {len(df)} days of basic data from Tushare for {symbol}")
                    return df
            except Exception as e:
                self.logger.error(f"Error using TushareAPIManager: {str(e)}")
                self.logger.info("Falling back to legacy Tushare method")
        
        # Fallback to old method if TushareAPIManager is not available or failed
        return self._get_stock_data_tushare_old(symbol, start_date, end_date)'''
        
        # Find and replace the _get_stock_data_tushare method
        tushare_pattern = re.compile(r'    def _get_stock_data_tushare\([^)]*\):[^\n]*\n(?:\s+[^\n]*\n)*?(?=\s{4}def|\s*$)', re.MULTILINE)
        tushare_match = tushare_pattern.search(new_content)
        
        if tushare_match:
            # Replace the method
            newer_content = new_content[:tushare_match.start()] + new_tushare_method + new_content[tushare_match.end():]
            
            # Write the modified content back to the file
            with open(file_path, 'w') as f:
                f.write(newer_content)
            
            logger.info("Successfully replaced the _get_stock_data_tushare method")
        else:
            logger.error("Could not find the _get_stock_data_tushare method")
            
        return 0
    else:
        logger.error("Could not find the __init__ method")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 