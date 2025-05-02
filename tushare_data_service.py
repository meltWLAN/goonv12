import tushare as ts
import pandas as pd
import time
from datetime import datetime, timedelta
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tushare_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TushareDataService")

class TushareDataService:
    """
    Tushare数据服务封装类
    负责从Tushare API获取各类金融数据，提供统一的数据获取接口
    """
    
    def __init__(self, token=None, cache_dir="./data_cache"):
        """
        初始化Tushare数据服务
        
        Args:
            token (str): Tushare API token
            cache_dir (str): 数据缓存目录
        """
        self.token = token or os.environ.get('TUSHARE_TOKEN', '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10')
        self.cache_dir = cache_dir
        self.api = None
        self._init_api()
        self._create_cache_dir()
        
    def _init_api(self):
        """初始化Tushare API连接"""
        try:
            ts.set_token(self.token)
            self.api = ts.pro_api()
            logger.info("Tushare API初始化成功")
        except Exception as e:
            logger.error(f"Tushare API初始化失败: {str(e)}")
            raise ConnectionError(f"无法连接到Tushare API: {str(e)}")
    
    def _create_cache_dir(self):
        """创建缓存目录"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"创建缓存目录: {self.cache_dir}")
    
    def _get_cache_path(self, data_type, params):
        """生成缓存文件路径"""
        param_str = "_".join([f"{k}={v}" for k, v in params.items()])
        return os.path.join(self.cache_dir, f"{data_type}_{param_str}.csv")
    
    def _load_from_cache(self, cache_path, expire_days=1):
        """从缓存加载数据"""
        if not os.path.exists(cache_path):
            return None
        
        # 检查缓存是否过期
        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - file_mtime > timedelta(days=expire_days):
            logger.info(f"缓存已过期: {cache_path}")
            return None
        
        try:
            df = pd.read_csv(cache_path)
            logger.info(f"从缓存加载数据: {cache_path}")
            return df
        except Exception as e:
            logger.error(f"读取缓存失败: {str(e)}")
            return None
    
    def _save_to_cache(self, df, cache_path):
        """保存数据到缓存"""
        try:
            df.to_csv(cache_path, index=False)
            logger.info(f"数据已缓存: {cache_path}")
        except Exception as e:
            logger.error(f"缓存数据失败: {str(e)}")
    
    def _handle_api_call(self, api_func, params, data_type, use_cache=True, expire_days=1):
        """处理API调用，支持缓存"""
        if use_cache:
            cache_path = self._get_cache_path(data_type, params)
            cached_data = self._load_from_cache(cache_path, expire_days)
            if cached_data is not None:
                return cached_data
        
        try:
            start_time = time.time()
            df = api_func(**params)
            end_time = time.time()
            
            if df is not None and not df.empty:
                logger.info(f"API调用成功: {data_type}, 获取到 {len(df)} 行数据, 耗时: {(end_time - start_time):.2f}秒")
                if use_cache:
                    self._save_to_cache(df, cache_path)
                return df
            else:
                logger.warning(f"API调用成功但无数据: {data_type}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"API调用失败: {data_type}, 错误: {str(e)}")
            raise

    # ===================== 市场数据接口 =====================
    
    def get_stock_daily(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """
        获取股票日线数据
        
        Args:
            ts_code (str): 股票代码，如 '000001.SZ'
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            use_cache (bool): 是否使用缓存
            
        Returns:
            pandas.DataFrame: 日线数据
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self._handle_api_call(
            self.api.daily,
            params,
            'daily',
            use_cache
        )
    
    def get_stock_weekly(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """获取股票周线数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self._handle_api_call(
            self.api.weekly,
            params,
            'weekly',
            use_cache
        )
    
    def get_stock_monthly(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """获取股票月线数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self._handle_api_call(
            self.api.monthly,
            params,
            'monthly',
            use_cache
        )
    
    def get_stock_list(self, exchange='', list_status='L', use_cache=True):
        """获取股票列表"""
        params = {
            'exchange': exchange,
            'list_status': list_status
        }
        
        return self._handle_api_call(
            self.api.stock_basic,
            params,
            'stock_list',
            use_cache,
            expire_days=7  # 股票列表缓存7天
        )
    
    def get_index_daily(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """获取指数日线数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self._handle_api_call(
            self.api.index_daily,
            params,
            'index_daily',
            use_cache
        )
    
    def get_index_components(self, index_code, date=None, use_cache=True):
        """获取指数成分股"""
        if not date:
            date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            
        params = {
            'index_code': index_code,
            'start_date': date,
            'end_date': date
        }
        
        return self._handle_api_call(
            self.api.index_weight,
            params,
            'index_weight',
            use_cache,
            expire_days=30  # 指数成分变化不频繁，缓存30天
        )
    
    def get_concept_list(self, use_cache=True):
        """获取概念股列表"""
        params = {}
        
        return self._handle_api_call(
            self.api.concept,
            params,
            'concept_list',
            use_cache,
            expire_days=30  # 概念列表变化不频繁，缓存30天
        )
    
    def get_concept_stocks(self, concept_id, use_cache=True):
        """获取概念成分股"""
        params = {
            'id': concept_id
        }
        
        return self._handle_api_call(
            self.api.concept_detail,
            params,
            f'concept_stocks_{concept_id}',
            use_cache,
            expire_days=30  # 概念成分变化不频繁，缓存30天
        )
    
    # ===================== 财务数据接口 =====================
    
    def get_income_statement(self, ts_code, period=None, use_cache=True):
        """获取利润表"""
        if not period:
            # 获取最近的年报
            year = datetime.now().year
            if datetime.now().month < 4:  # 4月前获取上上年年报
                year -= 2
            else:  # 4月后获取上年年报
                year -= 1
            period = f"{year}1231"
            
        params = {
            'ts_code': ts_code,
            'period': period
        }
        
        return self._handle_api_call(
            self.api.income,
            params,
            f'income_{ts_code}_{period}',
            use_cache,
            expire_days=90  # 财务数据变化不频繁，缓存90天
        )
    
    def get_balance_sheet(self, ts_code, period=None, use_cache=True):
        """获取资产负债表"""
        if not period:
            # 获取最近的年报
            year = datetime.now().year
            if datetime.now().month < 4:  # 4月前获取上上年年报
                year -= 2
            else:  # 4月后获取上年年报
                year -= 1
            period = f"{year}1231"
            
        params = {
            'ts_code': ts_code,
            'period': period
        }
        
        return self._handle_api_call(
            self.api.balancesheet,
            params,
            f'balancesheet_{ts_code}_{period}',
            use_cache,
            expire_days=90  # 财务数据变化不频繁，缓存90天
        )
    
    def get_cash_flow(self, ts_code, period=None, use_cache=True):
        """获取现金流量表"""
        if not period:
            # 获取最近的年报
            year = datetime.now().year
            if datetime.now().month < 4:  # 4月前获取上上年年报
                year -= 2
            else:  # 4月后获取上年年报
                year -= 1
            period = f"{year}1231"
            
        params = {
            'ts_code': ts_code,
            'period': period
        }
        
        return self._handle_api_call(
            self.api.cashflow,
            params,
            f'cashflow_{ts_code}_{period}',
            use_cache,
            expire_days=90  # 财务数据变化不频繁，缓存90天
        )
    
    def get_express_report(self, ts_code, period=None, use_cache=True):
        """获取业绩快报"""
        if not period:
            # 获取最近的年报
            year = datetime.now().year
            if datetime.now().month < 4:  # 4月前获取上上年年报
                year -= 2
            else:  # 4月后获取上年年报
                year -= 1
            period = f"{year}1231"
            
        params = {
            'ts_code': ts_code,
            'period': period
        }
        
        return self._handle_api_call(
            self.api.express,
            params,
            f'express_{ts_code}_{period}',
            use_cache,
            expire_days=30  # 业绩快报更新较频繁，缓存30天
        )
    
    # ===================== 市场交易数据接口 =====================
    
    def get_margin_data(self, ts_code=None, trade_date=None, start_date=None, end_date=None, use_cache=True):
        """获取融资融券数据"""
        params = {}
        
        if ts_code:
            params['ts_code'] = ts_code
        
        if trade_date:
            params['trade_date'] = trade_date
        else:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            params['start_date'] = start_date
            params['end_date'] = end_date
        
        return self._handle_api_call(
            self.api.margin,
            params,
            'margin',
            use_cache,
            expire_days=1  # 融资融券数据每日更新，缓存1天
        )
    
    def get_top_list(self, trade_date=None, ts_code=None, use_cache=True):
        """获取龙虎榜数据"""
        if not trade_date:
            # 获取60天内的交易日，避免非交易日无数据
            trade_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
            
        params = {'trade_date': trade_date}
        if ts_code:
            params['ts_code'] = ts_code
        
        return self._handle_api_call(
            self.api.top_list,
            params,
            f'top_list_{trade_date}',
            use_cache,
            expire_days=30  # 龙虎榜数据变化不频繁，缓存30天
        )
    
    def get_daily_basic(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """获取每日指标"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self._handle_api_call(
            self.api.daily_basic,
            params,
            f'daily_basic_{ts_code}',
            use_cache,
            expire_days=1  # 每日指标每日更新，缓存1天
        )
    
    def get_adj_factor(self, ts_code, start_date=None, end_date=None, use_cache=True):
        """获取复权因子"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self._handle_api_call(
            self.api.adj_factor,
            params,
            f'adj_factor_{ts_code}',
            use_cache,
            expire_days=7  # 复权因子变化不频繁，缓存7天
        )
    
    # ===================== 公司信息接口 =====================
    
    def get_company_info(self, ts_code, use_cache=True):
        """获取公司基本信息"""
        params = {
            'ts_code': ts_code
        }
        
        return self._handle_api_call(
            self.api.stock_company,
            params,
            f'company_info_{ts_code}',
            use_cache,
            expire_days=90  # 公司信息变化不频繁，缓存90天
        )
    
    def get_holder_number(self, ts_code, use_cache=True):
        """获取股东人数"""
        params = {
            'ts_code': ts_code
        }
        
        return self._handle_api_call(
            self.api.stk_holdernumber,
            params,
            f'holder_number_{ts_code}',
            use_cache,
            expire_days=30  # 股东人数季度更新，缓存30天
        )
    
    def get_holder_trade(self, ts_code, use_cache=True):
        """获取股东增减持"""
        params = {
            'ts_code': ts_code
        }
        
        return self._handle_api_call(
            self.api.stk_holdertrade,
            params,
            f'holder_trade_{ts_code}',
            use_cache,
            expire_days=7  # 股东增减持频繁更新，缓存7天
        )
    
    def get_institution_survey(self, ts_code, use_cache=True):
        """获取机构调研"""
        params = {
            'ts_code': ts_code
        }
        
        return self._handle_api_call(
            self.api.stk_surv,
            params,
            f'institution_survey_{ts_code}',
            use_cache,
            expire_days=7  # 机构调研频繁更新，缓存7天
        )

    # ===================== 辅助方法 =====================
    
    def calculate_ma(self, df, periods=[5, 10, 20, 30, 60]):
        """计算移动平均线"""
        if df.empty:
            return df
        
        if 'close' not in df.columns:
            logger.error("数据中没有'close'列，无法计算MA")
            return df
        
        for period in periods:
            df[f'ma{period}'] = df['close'].rolling(window=period).mean()
        
        return df
    
    def calculate_macd(self, df, short_period=12, long_period=26, signal_period=9):
        """计算MACD指标"""
        if df.empty:
            return df
        
        if 'close' not in df.columns:
            logger.error("数据中没有'close'列，无法计算MACD")
            return df
        
        # 计算短期EMA
        df['ema_short'] = df['close'].ewm(span=short_period, adjust=False).mean()
        # 计算长期EMA
        df['ema_long'] = df['close'].ewm(span=long_period, adjust=False).mean()
        # 计算DIF
        df['macd_dif'] = df['ema_short'] - df['ema_long']
        # 计算DEA
        df['macd_dea'] = df['macd_dif'].ewm(span=signal_period, adjust=False).mean()
        # 计算MACD柱状
        df['macd'] = (df['macd_dif'] - df['macd_dea']) * 2
        
        # 删除中间计算结果
        df.drop(['ema_short', 'ema_long'], axis=1, inplace=True)
        
        return df
    
    def calculate_kdj(self, df, n=9, m1=3, m2=3):
        """计算KDJ指标"""
        if df.empty:
            return df
        
        if not all(col in df.columns for col in ['high', 'low', 'close']):
            logger.error("数据中缺少'high'、'low'或'close'列，无法计算KDJ")
            return df
        
        df['low_n'] = df['low'].rolling(window=n).min()
        df['high_n'] = df['high'].rolling(window=n).max()
        df['rsv'] = (df['close'] - df['low_n']) / (df['high_n'] - df['low_n']) * 100
        
        # 初始化K、D值
        df['kdj_k'] = df['rsv'].ewm(com=m1-1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        # 计算J值
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        # 删除中间计算结果
        df.drop(['low_n', 'high_n', 'rsv'], axis=1, inplace=True)
        
        return df
    
    def calculate_boll(self, df, n=20, std_dev=2):
        """计算布林带指标"""
        if df.empty:
            return df
        
        if 'close' not in df.columns:
            logger.error("数据中没有'close'列，无法计算BOLL")
            return df
        
        df['boll_mid'] = df['close'].rolling(window=n).mean()
        df['std'] = df['close'].rolling(window=n).std()
        df['boll_upper'] = df['boll_mid'] + std_dev * df['std']
        df['boll_lower'] = df['boll_mid'] - std_dev * df['std']
        
        # 删除中间计算结果
        df.drop(['std'], axis=1, inplace=True)
        
        return df
    
    def calculate_rsi(self, df, periods=[6, 12, 24]):
        """计算RSI指标"""
        if df.empty:
            return df
        
        if 'close' not in df.columns:
            logger.error("数据中没有'close'列，无法计算RSI")
            return df
        
        # 计算价格变化
        df['diff'] = df['close'].diff()
        
        for period in periods:
            # 分别计算涨跌幅
            df['up'] = df['diff'].clip(lower=0)
            df['down'] = -df['diff'].clip(upper=0)
            
            # 计算涨跌幅的移动平均
            df['avg_up'] = df['up'].rolling(window=period).mean()
            df['avg_down'] = df['down'].rolling(window=period).mean()
            
            # 计算相对强度
            df['rs'] = df['avg_up'] / df['avg_down']
            
            # 计算RSI
            df[f'rsi_{period}'] = 100 - (100 / (1 + df['rs']))
        
        # 删除中间计算结果
        df.drop(['diff', 'up', 'down', 'avg_up', 'avg_down', 'rs'], axis=1, inplace=True)
        
        return df
    
    def calculate_all_indicators(self, df):
        """计算所有技术指标"""
        if df.empty:
            return df
        
        # 确保日期降序排列
        df = df.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # 计算各项指标
        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_kdj(df)
        df = self.calculate_boll(df)
        df = self.calculate_rsi(df)
        
        return df


# 使用示例
if __name__ == "__main__":
    # 初始化服务
    tushare_service = TushareDataService()
    
    # 获取股票列表
    stock_list = tushare_service.get_stock_list()
    print(f"共获取到 {len(stock_list)} 支股票")
    
    # 获取某只股票的日线数据
    daily_data = tushare_service.get_stock_daily('000001.SZ')
    print(f"获取到 {len(daily_data)} 条日线数据")
    
    # 计算技术指标
    with_indicators = tushare_service.calculate_all_indicators(daily_data)
    print(f"计算完成，共 {len(with_indicators.columns)} 个指标")
    print(with_indicators.columns.tolist())
    
    # 获取财务数据
    income = tushare_service.get_income_statement('000001.SZ')
    print(f"获取到利润表数据 {len(income)} 条")
    
    # 获取股东人数
    holders = tushare_service.get_holder_number('000001.SZ')
    print(f"获取到股东人数数据 {len(holders)} 条") 