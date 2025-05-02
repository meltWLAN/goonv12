import tushare as ts
import pandas as pd
import numpy as np
import os
import time
import logging
import json
from datetime import datetime, timedelta
from functools import wraps
from tushare_api_manager import TushareAPIManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TushareDataCenter:
    """
    全面的Tushare数据中心，整合所有Tushare接口
    提供统一的数据访问接口，处理缓存、错误和API限制
    """
    
    def __init__(self, token=None, cache_dir='./data_cache'):
        """
        初始化数据中心
        
        Args:
            token: Tushare API token
            cache_dir: 缓存目录
        """
        self.logger = logging.getLogger('TushareDataCenter')
        self.token = token or os.environ.get('TUSHARE_TOKEN')
        
        if not self.token:
            self.logger.error("未提供Tushare token。请通过参数或环境变量设置token。")
            raise ValueError("未提供Tushare token")
            
        # 初始化API管理器
        self.api_manager = TushareAPIManager(token=self.token, cache_dir=cache_dir)
        self.logger.info(f"初始化Tushare数据中心，使用token: {self.token[:4]}...{self.token[-4:]}")
        
        # 验证token
        if not self.api_manager.validate_token():
            self.logger.error("Token验证失败！请检查您的token是否有效。")
            raise ValueError("Token验证失败")
            
        # 初始化缓存目录
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 设置API调用间隔（毫秒）
        self.api_call_interval = 500
        self.last_api_call = 0
        
        # 数据类型映射表
        self._init_data_type_map()
        
    def _init_data_type_map(self):
        """初始化数据类型映射表"""
        self.data_type_map = {
            # 基础数据
            'stock_basic': {'func': self.api_manager.call_api, 'endpoint': 'stock_basic'},
            'trade_cal': {'func': self.api_manager.call_api, 'endpoint': 'trade_cal'},
            'namechange': {'func': self.api_manager.call_api, 'endpoint': 'namechange'},
            'hs_const': {'func': self.api_manager.call_api, 'endpoint': 'hs_const'},
            'stock_company': {'func': self.api_manager.call_api, 'endpoint': 'stock_company'},
            'stk_managers': {'func': self.api_manager.call_api, 'endpoint': 'stk_managers'},
            'stk_rewards': {'func': self.api_manager.call_api, 'endpoint': 'stk_rewards'},
            'new_share': {'func': self.api_manager.call_api, 'endpoint': 'new_share'},
            
            # 行情数据
            'daily': {'func': self.api_manager.call_api, 'endpoint': 'daily'},
            'weekly': {'func': self.api_manager.call_api, 'endpoint': 'weekly'},
            'monthly': {'func': self.api_manager.call_api, 'endpoint': 'monthly'},
            'adj_factor': {'func': self.api_manager.call_api, 'endpoint': 'adj_factor'},
            'suspend_d': {'func': self.api_manager.call_api, 'endpoint': 'suspend_d'},
            'daily_basic': {'func': self.api_manager.call_api, 'endpoint': 'daily_basic'},
            'stk_limit': {'func': self.api_manager.call_api, 'endpoint': 'stk_limit'},
            'stk_mins': {'func': self.api_manager.call_api, 'endpoint': 'stk_mins'},
            
            # 财务数据
            'income': {'func': self.api_manager.call_api, 'endpoint': 'income'},
            'balancesheet': {'func': self.api_manager.call_api, 'endpoint': 'balancesheet'},
            'cashflow': {'func': self.api_manager.call_api, 'endpoint': 'cashflow'},
            'forecast': {'func': self.api_manager.call_api, 'endpoint': 'forecast'},
            'express': {'func': self.api_manager.call_api, 'endpoint': 'express'},
            'dividend': {'func': self.api_manager.call_api, 'endpoint': 'dividend'},
            'fina_indicator': {'func': self.api_manager.call_api, 'endpoint': 'fina_indicator'},
            'disclosure_date': {'func': self.api_manager.call_api, 'endpoint': 'disclosure_date'},
            
            # 市场参考数据
            'hsgt_top10': {'func': self.api_manager.call_api, 'endpoint': 'hsgt_top10'},
            'ggt_top10': {'func': self.api_manager.call_api, 'endpoint': 'ggt_top10'},
            'ggt_daily': {'func': self.api_manager.call_api, 'endpoint': 'ggt_daily'},
            'ggt_monthly': {'func': self.api_manager.call_api, 'endpoint': 'ggt_monthly'},
            
            # 特殊处理的接口
            'pro_bar': {'func': self._handle_pro_bar, 'endpoint': 'pro_bar'},
        }
        
    def _rate_limit(func):
        """装饰器，用于限制API调用频率"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            now = time.time() * 1000
            elapsed = now - self.last_api_call
            
            if elapsed < self.api_call_interval:
                sleep_time = (self.api_call_interval - elapsed) / 1000
                time.sleep(sleep_time)
                
            self.last_api_call = time.time() * 1000
            return func(self, *args, **kwargs)
        return wrapper
    
    @_rate_limit
    def get_data(self, data_type, **params):
        """
        获取数据的统一接口
        
        Args:
            data_type: 数据类型，如'stock_basic', 'daily', 'income'等
            **params: 特定数据类型的参数
            
        Returns:
            pandas.DataFrame: 获取的数据
        """
        if data_type not in self.data_type_map:
            self.logger.error(f"不支持的数据类型: {data_type}")
            return pd.DataFrame()
            
        try:
            handler = self.data_type_map[data_type]
            if data_type == 'pro_bar':
                return handler['func'](**params)
            else:
                return handler['func'](endpoint=handler['endpoint'], **params)
        except Exception as e:
            self.logger.error(f"获取{data_type}数据时出错: {str(e)}")
            return pd.DataFrame()
    
    def _handle_pro_bar(self, **params):
        """特殊处理pro_bar接口"""
        try:
            # 确保ts_code参数存在
            if 'ts_code' not in params:
                self.logger.error("缺少必要参数ts_code")
                return pd.DataFrame()
                
            # 使用tushare直接调用pro_bar
            pro = ts.pro_api(self.token)
            return ts.pro_bar(**params)
        except Exception as e:
            self.logger.error(f"调用pro_bar接口出错: {str(e)}")
            return pd.DataFrame()
    
    # 便捷方法 - 基础信息
    def get_stock_list(self, market=None, list_status='L'):
        """获取股票列表"""
        params = {'list_status': list_status}
        if market:
            params['market'] = market
        return self.get_data('stock_basic', **params)
    
    def get_trade_calendar(self, exchange='SSE', start_date=None, end_date=None):
        """获取交易日历"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        return self.get_data('trade_cal', exchange=exchange, start_date=start_date, end_date=end_date)
    
    def is_trade_date(self, date=None):
        """判断是否为交易日"""
        if not date:
            date = datetime.now().strftime('%Y%m%d')
            
        calendar = self.get_trade_calendar(start_date=date, end_date=date)
        if not calendar.empty:
            return calendar.iloc[0]['is_open'] == 1
        return False
    
    def get_stock_company(self, ts_code=None):
        """获取上市公司信息"""
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        return self.get_data('stock_company', **params)
    
    # 便捷方法 - 行情数据
    def get_daily_data(self, ts_code, start_date=None, end_date=None, adj=None):
        """
        获取日线行情数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adj: 复权类型，None不复权，qfq前复权，hfq后复权
        """
        if adj is None:
            # 使用daily接口
            params = {'ts_code': ts_code}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            return self.get_data('daily', **params)
        else:
            # 使用pro_bar接口
            params = {
                'ts_code': ts_code,
                'adj': adj,
                'asset': 'E'
            }
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            return self.get_data('pro_bar', **params)
    
    def get_minute_data(self, ts_code, freq='1min', start_date=None, end_date=None):
        """获取分钟线数据"""
        params = {'ts_code': ts_code, 'freq': freq}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get_data('stk_mins', **params)
    
    def get_daily_basic(self, ts_code=None, trade_date=None, start_date=None, end_date=None):
        """获取每日指标"""
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get_data('daily_basic', **params)
    
    # 便捷方法 - 财务数据
    def get_income(self, ts_code, period=None, start_date=None, end_date=None):
        """获取利润表"""
        params = {'ts_code': ts_code}
        if period:
            params['period'] = period
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get_data('income', **params)
    
    def get_balance(self, ts_code, period=None, start_date=None, end_date=None):
        """获取资产负债表"""
        params = {'ts_code': ts_code}
        if period:
            params['period'] = period
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get_data('balancesheet', **params)
    
    def get_cashflow(self, ts_code, period=None, start_date=None, end_date=None):
        """获取现金流量表"""
        params = {'ts_code': ts_code}
        if period:
            params['period'] = period
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get_data('cashflow', **params)
    
    def get_financial_indicator(self, ts_code, period=None, start_date=None, end_date=None):
        """获取财务指标数据"""
        params = {'ts_code': ts_code}
        if period:
            params['period'] = period
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get_data('fina_indicator', **params)
    
    def get_dividend(self, ts_code=None, ann_date=None, ex_date=None):
        """获取分红送股信息"""
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if ann_date:
            params['ann_date'] = ann_date
        if ex_date:
            params['ex_date'] = ex_date
        return self.get_data('dividend', **params)
    
    # 便捷方法 - 市场参考
    def get_hsgt_top10(self, trade_date=None, ts_code=None, start_date=None, end_date=None, market_type=None):
        """获取沪深股通十大成交股"""
        params = {}
        if trade_date:
            params['trade_date'] = trade_date
        if ts_code:
            params['ts_code'] = ts_code
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if market_type:
            params['market_type'] = market_type
        return self.get_data('hsgt_top10', **params)
    
    # 高级数据处理方法
    def get_full_financial_data(self, ts_code, start_date=None, end_date=None):
        """
        获取完整的财务数据，包括利润表、资产负债表、现金流量表和财务指标
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 包含各类财务数据的字典
        """
        income = self.get_income(ts_code, start_date=start_date, end_date=end_date)
        balance = self.get_balance(ts_code, start_date=start_date, end_date=end_date)
        cashflow = self.get_cashflow(ts_code, start_date=start_date, end_date=end_date)
        indicator = self.get_financial_indicator(ts_code, start_date=start_date, end_date=end_date)
        
        return {
            'income': income,
            'balance': balance,
            'cashflow': cashflow,
            'indicator': indicator
        }
    
    def get_stock_profile(self, ts_code):
        """
        获取股票完整画像，包括基本信息、公司信息、最新行情、财务指标等
        
        Args:
            ts_code: 股票代码
            
        Returns:
            dict: 股票画像数据
        """
        # 获取基本信息
        basic_info = self.get_data('stock_basic', ts_code=ts_code)
        if basic_info.empty:
            self.logger.error(f"未找到股票 {ts_code} 的基本信息")
            return {}
            
        # 获取公司信息
        company_info = self.get_stock_company(ts_code)
        
        # 获取最新行情
        latest_date = datetime.now().strftime('%Y%m%d')
        daily_data = self.get_daily_data(ts_code, start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'))
        daily_basic = self.get_daily_basic(ts_code=ts_code, start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'))
        
        # 获取最新财务指标
        financial = self.get_financial_indicator(ts_code)
        
        # 获取分红信息
        dividend = self.get_dividend(ts_code=ts_code)
        
        return {
            'basic_info': basic_info.iloc[0].to_dict() if not basic_info.empty else {},
            'company_info': company_info.iloc[0].to_dict() if not company_info.empty else {},
            'latest_quote': daily_data.iloc[-1].to_dict() if not daily_data.empty else {},
            'latest_basic': daily_basic.iloc[-1].to_dict() if not daily_basic.empty else {},
            'financial': financial.iloc[0].to_dict() if not financial.empty else {},
            'dividend': dividend.to_dict('records') if not dividend.empty else []
        }


# 使用示例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tushare_data_center.py <tushare_token> [ts_code]")
        sys.exit(1)
        
    token = sys.argv[1]
    ts_code = sys.argv[2] if len(sys.argv) > 2 else '000001.SZ'
    
    # 初始化数据中心
    data_center = TushareDataCenter(token=token)
    
    # 获取股票列表
    stock_list = data_center.get_stock_list()
    print(f"获取到 {len(stock_list)} 只股票")
    
    # 获取股票行情
    daily_data = data_center.get_daily_data(ts_code, start_date='20230101')
    print(f"获取到 {len(daily_data)} 条日线数据")
    
    # 获取股票画像
    profile = data_center.get_stock_profile(ts_code)
    print(f"股票名称: {profile.get('basic_info', {}).get('name')}")
    print(f"所属行业: {profile.get('basic_info', {}).get('industry')}")
    print(f"最新收盘价: {profile.get('latest_quote', {}).get('close')}") 