import pandas as pd
import numpy as np
import akshare as ak
import tushare as ts
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import logging

class DataSourceException(Exception):
    """数据源异常"""
    pass

class ChinaStockProvider:
    """统一数据接入层
    
    功能特性：
    1. 支持多数据源(AKShare东方财富/Tushare Pro)
    2. 标准化数据输出格式(列名/日期格式/数据类型)
    3. 多级缓存策略(内存缓存/磁盘缓存)
    4. 智能重试机制
    5. 数据完整性验证
    """
    
    CACHE_EXPIRY = 1800  # 缓存有效期(秒)
    RETRY_INTERVALS = [0.5, 1, 2]  # 重试间隔
    
    def __init__(self, api_token=None, current_source='tushare'):
        """初始化中国股票数据提供者
        
        Args:
            api_token: API令牌 (如Tushare的token)
            current_source: 默认数据源 ('tushare' 或 'akshare')
        """
        self.tushare_token = api_token
        self.current_source = current_source
        self.tushare_pro = None
        self.max_retry = 3
        self.data_cache = {}  # 添加数据缓存属性
        
        # 初始化日志
        self.logger = logging.getLogger('stock_data_provider')
        if not self.logger.handlers:
            # 创建文件处理器
            log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler = logging.FileHandler('data_provider.log')
            file_handler.setFormatter(log_formatter)
            self.logger.addHandler(file_handler)
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            self.logger.addHandler(console_handler)
            
            # 设置日志级别
            self.logger.setLevel(logging.INFO)
        
        # 如果提供了Tushare token，则初始化Tushare API
        if api_token and current_source == 'tushare':
            try:
                ts.set_token(api_token)
                self.tushare_pro = ts.pro_api()
                self.logger.info("成功初始化Tushare API")
            except Exception as e:
                self.logger.error(f"初始化Tushare API失败: {str(e)}")
        
        self.memory_cache = {}  # 内存缓存
        
        # 设置数据源
        self.data_sources = ['tushare', 'akshare']  # 将tushare优先置于akshare之前
        
        # API调用间隔
        self.api_cooldown = 0.5
        self.last_api_call = 0
        
        self._init_column_mappings()
        self._init_api_handlers()
        self.price_limit_ratios = {
            'NORMAL': 0.1,  # 普通股票
            'ST': 0.05,     # ST股票
            'STAR': 0.2,    # 科创板
            'CREATE': 0.2   # 创业板
        }
        
        self.logger.info(f"ChinaStockProvider初始化完成，当前数据源: {self.current_source}, 可用数据源: {self.get_available_sources()}")
        
    def _init_column_mappings(self):
        """初始化标准列名映射"""
        # AKShare映射
        self.akshare_column_map = {
            '日期': 'date', '交易日期': 'date',
            '开盘': 'open', '开盘价': 'open',
            '收盘': 'close', '收盘价': 'close',
            '最高': 'high', '最高价': 'high',
            '最低': 'low', '最低价': 'low',
            '成交量': 'volume', 'volume': 'volume',
            '成交额': 'amount', '成交金额': 'amount',
            '涨跌幅': 'change_pct', '涨跌额': 'change',
            '振幅': 'amplitude', '换手率': 'turnover'
        }
        
        # Tushare映射
        self.tushare_column_map = {
            'trade_date': 'date', 
            'open': 'open',
            'close': 'close',
            'high': 'high',
            'low': 'low',
            'vol': 'volume',
            'amount': 'amount',
            'pct_chg': 'change_pct',
            'change': 'change',
            'pre_close': 'pre_close'
        }
        
        # 标准列列表
        self.standard_columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'change_pct']
    
    def _init_api_handlers(self):
        """注册API处理器"""
        self.api_handlers = {
            'stock': self._handle_stock_api,
            'sector': self._handle_sector_api,
            'index': self._handle_index_api
        }
    
    def set_data_source(self, source_name: str) -> bool:
        """设置当前数据源
        
        Args:
            source_name: 数据源名称 ('akshare' 或 'tushare')
            
        Returns:
            是否设置成功
        """
        if source_name.lower() not in self.data_sources:
            self.logger.error(f"不支持的数据源: {source_name}")
            return False
            
        source_name = source_name.lower()
        
        # 检查Tushare是否可用
        if source_name == 'tushare' and not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法使用")
            return False
            
        self.current_source = source_name
        self.logger.info(f"数据源已设置为: {source_name}")
        return True
    
    def get_available_sources(self) -> List[str]:
        """获取可用数据源列表"""
        if self.tushare_pro:
            return self.data_sources
        else:
            return ['akshare']
    
    def get_data(self, data_type='stock', **kwargs):
        """通用数据获取接口，支持不同数据类型
        
        Args:
            data_type: 数据类型，如 'stock'（股票行情数据）、'info'（股票基本信息）等
            kwargs: 其他参数，不同数据类型需要的参数不同
        
        Returns:
            DataFrame 包含请求的数据
        """
        if data_type == 'stock':
            # 获取股票行情数据
            symbol = kwargs.get('symbol')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            limit = kwargs.get('limit')
            return self.get_stock_data(symbol, start_date, end_date, limit)
        elif data_type == 'info':
            # 获取股票基本信息
            symbol = kwargs.get('symbol')
            return self.get_stock_info(symbol)
        else:
            self.logger.error(f"不支持的数据类型: {data_type}")
            return pd.DataFrame()
            
    def get_stock_info(self, symbol=None):
        """获取股票基本信息
        
        Args:
            symbol: 股票代码，如 '000001.SZ'
            
        Returns:
            DataFrame 包含股票基本信息
        """
        try:
            # 标准化股票代码
            if symbol:
                symbol = self._standardize_stock_code(symbol)
                
            # 尝试使用tushare获取
            if self.tushare_pro and symbol:
                try:
                    # 提取市场和代码
                    code, market = symbol.split('.')
                    info = self.tushare_pro.stock_basic(ts_code=symbol, fields='ts_code,symbol,name,area,industry,list_date')
                    if not isinstance(info, pd.DataFrame) or info.empty:
                        self.logger.warning(f"Tushare未返回{symbol}的股票信息")
                    else:
                        return info
                except Exception as e:
                    self.logger.warning(f"使用Tushare获取股票信息失败: {str(e)}")
                    
            # 如果tushare失败，尝试使用akshare
            try:
                # 初始化结果DataFrame
                if symbol:
                    # 获取单只股票信息
                    try:
                        code, market = symbol.split('.')
                        if market == 'SH':
                            market_code = 'sh'
                        elif market == 'SZ':
                            market_code = 'sz'
                        elif market == 'BJ':
                            market_code = 'bj'
                        else:
                            self.logger.error(f"不支持的市场代码: {market}")
                            return pd.DataFrame({'ts_code': [symbol], 'name': [symbol]})
                            
                        full_code = f"{market_code}{code}"
                        info = ak.stock_individual_info_em(symbol=full_code)
                        if not isinstance(info, pd.DataFrame) or info.empty:
                            return pd.DataFrame({'ts_code': [symbol], 'name': [symbol]})
                        
                        # 重命名列以兼容代码
                        if '股票名称' in info.columns:
                            info['name'] = info['股票名称']
                        if '行业' in info.columns:
                            info['industry'] = info['行业']
                            
                        # 添加ts_code列以兼容代码
                        info['ts_code'] = symbol
                        
                        return info
                    except Exception as e:
                        self.logger.error(f"使用Akshare获取股票信息失败: {str(e)}")
                        return pd.DataFrame({'ts_code': [symbol], 'name': [symbol]})
                else:
                    # 获取所有A股列表
                    try:
                        info = ak.stock_zh_a_spot_em()
                        return info
                    except Exception as e:
                        self.logger.error(f"使用Akshare获取A股列表失败: {str(e)}")
                        return pd.DataFrame()
            except Exception as e:
                self.logger.error(f"获取股票信息过程中发生错误: {str(e)}")
                
            # 如果所有方法都失败，返回一个包含股票代码的最小DataFrame
            if symbol:
                return pd.DataFrame({'ts_code': [symbol], 'name': [symbol]})
            return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"获取股票信息时出错: {str(e)}")
            if symbol:
                return pd.DataFrame({'ts_code': [symbol], 'name': [symbol]})
            return pd.DataFrame()
        
    def _call_with_retry(self, func, **params):
        """带重试机制的API调用"""
        last_error = None
        for wait_sec in self.RETRY_INTERVALS:
            try:
                return func(**params)
            except Exception as e:
                self.logger.warning(f"API调用失败: {str(e)}")
                last_error = e
                time.sleep(wait_sec)
        
        # 如果当前数据源失败，尝试切换数据源
        if self.current_source == 'akshare' and self.tushare_pro:
            self.logger.info("AKShare数据源失败，尝试切换到Tushare")
            temp_source = self.current_source
            self.current_source = 'tushare'
            try:
                result = func(**params)
                self.logger.info("使用Tushare获取数据成功")
                return result
            except Exception as e:
                self.logger.error(f"Tushare数据源也失败: {str(e)}")
                self.current_source = temp_source
        elif self.current_source == 'tushare':
            self.logger.info("Tushare数据源失败，尝试切换到AKShare")
            temp_source = self.current_source
            self.current_source = 'akshare'
            try:
                result = func(**params)
                self.logger.info("使用AKShare获取数据成功")
                return result
            except Exception as e:
                self.logger.error(f"AKShare数据源也失败: {str(e)}")
                self.current_source = temp_source
        
        # 如果两个数据源都失败了，创建一个空的DataFrame返回，避免完全失败
        self.logger.error(f"所有数据源都失败，返回空数据: {str(last_error)}")
        
        # 根据数据类型创建不同结构的空DataFrame
        if 'symbol' in params and params.get('symbol', '').endswith(('SH', 'SZ', 'BJ')):
            # 股票数据
            empty_df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'amount'])
            # 添加一行基本数据，避免后续处理出错
            today = datetime.now().strftime('%Y%m%d')
            empty_df.loc[0] = [today, 0.0, 0.0, 0.0, 0.0, 0, 0.0]
            return empty_df
        else:
            return pd.DataFrame()
        
    def _standardize_data(self, df, data_type):
        """数据标准化流水线"""
        if df is None or df.empty:
            return pd.DataFrame(columns=self.standard_columns)
            
        # 列名转换
        df = self._convert_column_names(df)
        
        # 日期格式转换
        df = self._convert_date_format(df)
        
        # 数据验证和清洗
        df = self._validate_data(df)
        
        # 如果是股票数据，添加额外指标
        if data_type == 'stock':
            # 添加技术指标
            df = self._add_technical_indicators(df)
        
        return df
        
    def _get_from_cache(self, key: str) -> Union[pd.DataFrame, None]:
        """从内存缓存获取数据"""
        cache_item = self.memory_cache.get(key)
        if cache_item and time.time() - cache_item['timestamp'] < self.CACHE_EXPIRY:
            return cache_item['data'].copy()
        return None

    def _update_cache(self, key: str, data: pd.DataFrame):
        """更新内存缓存"""
        self.memory_cache[key] = {
            'data': data.copy(),
            'timestamp': time.time()
        }

    def _convert_column_names(self, df):
        """统一列名转换"""
        column_map = self.akshare_column_map if self.current_source == 'akshare' else self.tushare_column_map
        return df.rename(columns=lambda x: column_map.get(x, x))
        
    def _convert_date_format(self, df):
        """统一日期格式为YYYYMMDD"""
        if 'date' not in df.columns:
            return df
            
        # 处理不同格式的日期
        try:
            if df['date'].dtype == 'object':
                # 尝试转换为datetime
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
            # 转换为YYYYMMDD格式字符串
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.strftime('%Y%m%d')
            
            # 确保日期列是排序的
            df = df.sort_values('date')
        except Exception as e:
            self.logger.warning(f"日期格式转换失败: {str(e)}")
            
        return df
    
    def _validate_data(self, df):
        """数据验证和清洗"""
        if df.empty:
            return df
            
        # 检查必要列
        required_cols = ['date', 'open', 'close', 'high', 'low']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.logger.warning(f"数据缺少必要列: {missing_cols}")
            
        # 转换数值列
        numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
        for col in [c for c in numeric_cols if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # 处理异常值
        # 价格不能为负
        for col in ['open', 'close', 'high', 'low']:
            if col in df.columns:
                df = df[df[col] > 0]
                
        # 成交量不能为负
        if 'volume' in df.columns:
            df = df[df['volume'] >= 0]
            
        # 最高价应该 >= 最低价
        if 'high' in df.columns and 'low' in df.columns:
            df = df[df['high'] >= df['low']]
            
        # 填充缺失值
        df = df.ffill().bfill()
            
        return df
        
    def _handle_stock_api(self, symbol: str, **kwargs):
        """处理股票数据API调用
        
        Args:
            symbol: 股票代码
            kwargs: 其他参数，包括start_date和end_date
            
        Returns:
            处理后的DataFrame
        """
        # 参数验证
        if not symbol:
            self.logger.error("股票代码不能为空")
            return self._prepare_error_response()
            
        # 标准化股票代码
        orig_symbol = symbol
        symbol = self._standardize_stock_code(symbol)
        if not symbol:
            self.logger.error(f"无法标准化股票代码: {orig_symbol}")
            return self._prepare_error_response(orig_symbol)
            
        # 日期处理
        start_date = kwargs.get('start_date', 
                            (datetime.now() - timedelta(days=120)).strftime('%Y%m%d'))
        end_date = kwargs.get('end_date', datetime.now().strftime('%Y%m%d'))
        limit = kwargs.get('limit')
        
        self.logger.info(f"请求股票数据: {symbol}, {start_date} - {end_date}")
        
        # 尝试从缓存获取
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if cache_key in self.data_cache:
            df = self.data_cache[cache_key]
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        
        # 尝试不同的数据源
        strategies = [
            ('tushare', self._get_stock_data_tushare),
            ('akshare', self._get_stock_data_akshare)
        ]
        
        df = pd.DataFrame()  # 初始化为空DataFrame
        
        for name, func in strategies:
            try:
                self.logger.info(f"尝试使用{name}获取数据...")
                df = func(symbol, start_date, end_date)
                
                # 验证返回结果
                if self._validate_response(df):
                    self.logger.info(f"成功使用{name}获取数据: {len(df)}行")
                    # 缓存结果
                    self.data_cache[cache_key] = df
                    return df
        else:
                    self.logger.warning(f"{name}返回的数据不完整或为空: {len(df) if isinstance(df, pd.DataFrame) else 'not a dataframe'}")
            except Exception as e:
                self.logger.error(f"使用{name}获取数据失败: {str(e)}")
                
        # 所有策略都失败，返回一个最小的有效结果
        self.logger.error(f"所有数据源都失败，返回默认数据")
        return self._prepare_error_response(symbol)
    
    def _prepare_error_response(self, symbol=None, error_msg="未知错误"):
        """准备错误响应，返回一个标准的错误DataFrame"""
        self.logger.error(error_msg)
        # 创建一个空的结果DataFrame
        df = pd.DataFrame({
            'trade_date': [datetime.now().strftime('%Y%m%d')],
            'open': [0.0],
            'high': [0.0],
            'low': [0.0],
            'close': [0.0],
            'volume': [0]
        })
        if symbol:
            df['ts_code'] = symbol
        return df

    def _validate_response(self, df, min_rows=5):
        """验证响应是否有效
        
        Args:
            df: DataFrame响应
            min_rows: 最小行数要求
            
        Returns:
            如果有效返回True，否则False
        """
        if not isinstance(df, pd.DataFrame):
            return False
            
        if df.empty:
            return False
            
        if len(df) < min_rows:
            return False
            
        return True
    
    def _get_stock_data_tushare(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """使用Tushare获取股票历史数据"""
        try:
            # 确保tushare_pro已初始化
            if not self.tushare_pro:
                ts.set_token(self.tushare_token)
                self.tushare_pro = ts.pro_api()
                
            # 标准化股票代码格式
            symbol = self._standardize_stock_code(symbol)
            
            # 确保标准格式的日期
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            
            # 尝试使用daily接口获取数据
            try:
                df = self.tushare_pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
                
                # 如果日期有数据，使用它
                if isinstance(df, pd.DataFrame) and not df.empty:
                    self.logger.info(f"成功通过Tushare daily接口获取{symbol}的数据: {len(df)}条")
                    
                    # 因为Tushare返回的数据是倒序的（最新的在前），我们保持一致
                    return df
            except Exception as e:
                self.logger.warning(f"Tushare daily接口获取{symbol}数据失败: {str(e)}，尝试其他方法")
                
            # 如果daily接口失败，尝试使用pro_bar接口
            try:
                df = ts.pro_bar(ts_code=symbol, adj='qfq', start_date=start_date, end_date=end_date)
                
                if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                    self.logger.info(f"成功通过Tushare pro_bar接口获取{symbol}的数据: {len(df)}条")
                    return df
            except Exception as e:
                self.logger.warning(f"Tushare pro_bar接口获取{symbol}数据失败: {str(e)}")
                
            # 如果以上两种方法都失败，返回空DataFrame
            self.logger.error(f"Tushare所有方法获取{symbol}数据均失败")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Tushare获取股票数据时发生错误: {str(e)}")
            return pd.DataFrame()
    
    def _get_stock_data_akshare(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """使用Akshare获取股票数据
        
        Args:
            symbol: 股票代码 (如 '000001.SZ')
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 包含历史数据
        """
        try:
            # 处理代码格式
            try:
                code, market = symbol.split('.')
            except ValueError:
                self.logger.error(f"无效的股票代码格式: {symbol}，缺少市场后缀")
                return pd.DataFrame()
                
            if market == 'SH':
                full_code = f"sh{code}"
            elif market == 'SZ':
                full_code = f"sz{code}"
            elif market == 'BJ':
                full_code = f"bj{code}"
            else:
                self.logger.error(f"不支持的市场: {market}")
                return pd.DataFrame()
            
            # 格式化日期
            try:
                start_date_fmt = datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')
                end_date_fmt = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')
            except ValueError:
                self.logger.error(f"无效的日期格式: {start_date} 或 {end_date}，应为YYYYMMDD格式")
                return pd.DataFrame()
            
            # 调用akshare API
            self.logger.info(f"使用Akshare获取数据: {full_code}, {start_date_fmt} - {end_date_fmt}")
            df = ak.stock_zh_a_hist(symbol=full_code, period="daily", 
                                     start_date=start_date_fmt, end_date=end_date_fmt,
                                     adjust="qfq")
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                self.logger.warning(f"Akshare未返回数据: {symbol}")
                return pd.DataFrame()
                
            # 标准化列名
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amplitude', 
                          'change_pct', 'change', 'turnover']
            
            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date'])
            
            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"使用Akshare获取数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _standardize_stock_code(self, symbol: str) -> str:
        """标准化股票代码为带交易所后缀的格式"""
        try:
            # 处理空值或None
            if not symbol:
                self.logger.error("股票代码为空")
                return ""
                
            # 已经是标准格式
            if '.' in symbol and len(symbol.split('.')) == 2:
                code_part, market_part = symbol.split('.')
                # 验证代码部分是否为6位数字
                if not (code_part.isdigit() and len(code_part) == 6):
                    self.logger.warning(f"股票代码部分({code_part})不是6位数字")
                # 验证市场部分
                if market_part not in ['SH', 'SZ', 'BJ']:
                    self.logger.warning(f"不支持的市场代码: {market_part}")
                return symbol
                
            # 纯数字代码，根据规则添加后缀
            if symbol.isdigit() and len(symbol) == 6:
                if symbol.startswith(('600', '601', '603', '605', '688')):
                    return f"{symbol}.SH"
                elif symbol.startswith(('000', '001', '002', '003', '300', '301')):
                    return f"{symbol}.SZ"
                elif symbol.startswith(('4', '8')):
                    return f"{symbol}.BJ"
                else:
                    self.logger.warning(f"无法确定股票 {symbol} 的所属市场")
                    # 默认设为上交所
                    return f"{symbol}.SH"
                    
            # 不规则格式，尝试处理
            if symbol.lower().startswith(('sh', 'sz', 'bj')):
                market = symbol[:2].upper()
                code = symbol[2:].strip()
                # 检查剩余部分是否为有效数字
                if code.isdigit() and len(code) == 6:
                    return f"{code}.{market}"
                else:
                    self.logger.warning(f"股票代码 {symbol} 格式无效")
                    return symbol
                
            # 如果是字母开头，可能是港股或美股，暂不处理
            if symbol[0].isalpha():
                self.logger.warning(f"不支持的股票代码格式: {symbol}")
                return symbol
                
            # 默认返回原格式
            self.logger.warning(f"无法识别的股票代码格式: {symbol}")
            return symbol
            
        except Exception as e:
            self.logger.error(f"标准化股票代码时出错: {str(e)}")
            return symbol
        
    def _handle_sector_api(self, sector_code: str, **kwargs):
        """行业板块数据获取处理器"""
        try:
            self.logger.info(f"获取行业板块[{sector_code}]数据")
            
            # 获取板块指数
            index_data = ak.stock_board_concept_hist_ths(symbol=sector_code)
            
            return index_data
            
        except Exception as e:
            self.logger.error(f"获取板块[{sector_code}]数据失败: {str(e)}")
            raise DataSourceException(f"板块数据获取失败: {str(e)}")
            
    def _handle_index_api(self, index_code: str, **kwargs):
        """指数数据获取处理器"""
        try:
            self.logger.info(f"获取指数[{index_code}]数据")
            
            if self.current_source == 'tushare' and self.tushare_pro:
                # 参数处理
                start_date = kwargs.get('start_date', (datetime.now() - timedelta(days=120)).strftime('%Y%m%d'))
                end_date = kwargs.get('end_date', datetime.now().strftime('%Y%m%d'))
                
                # 调用Tushare指数API
                df = self.tushare_pro.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
                return df
            else:
                # 根据指数代码判断使用哪个接口
                if index_code.startswith(('000', '399')):
                    # 深证指数
                    df = ak.stock_zh_index_daily(symbol=index_code)
                elif index_code.startswith(('000', '399')):
                    # 上证指数
                    df = ak.stock_zh_index_daily(symbol=index_code)
                else:
                    # 默认尝试通用接口
                    df = ak.stock_zh_index_daily_em(symbol=index_code)
                    
                return df
            
        except Exception as e:
            self.logger.error(f"获取指数[{index_code}]数据失败: {str(e)}")
            raise DataSourceException(f"指数数据获取失败: {str(e)}")
                
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加基本技术指标"""
        if df.empty:
            return df
            
        # 计算常用指标
        # 1. 移动平均线
        window_list = [5, 10, 20, 60]
        for window in window_list:
            if len(df) >= window:
                df[f'ma{window}'] = df['close'].rolling(window=window).mean()
                
        # 2. 成交量移动平均
        for window in window_list:
            if 'volume' in df.columns and len(df) >= window:
                df[f'volume_ma{window}'] = df['volume'].rolling(window=window).mean()
                
        # 3. 计算涨跌幅(若未提供)
        if 'change_pct' not in df.columns and 'close' in df.columns:
            df['change_pct'] = df['close'].pct_change() * 100
            
        return df
    
    def get_market_status(self) -> Dict:
        """获取市场整体状态"""
        try:
            # 获取北向资金数据
            north_money = ak.stock_em_hsgt_north_net_flow_in()
            
            # 获取两融数据
            margin_data = ak.stock_margin_sse()
            
            return {
                'north_money': north_money['value'].iloc[-1] if not north_money.empty else 0,
                'margin_balance': margin_data['value'].iloc[-1] if not margin_data.empty else 0,
                'market_sentiment': self._calculate_market_sentiment()
            }
            
        except Exception as e:
            self.logger.error(f"获取市场状态失败: {str(e)}")
            return {}
    
    def _calculate_market_sentiment(self) -> float:
        """计算市场情绪指标"""
        try:
            # 获取涨跌家数
            market_detail = ak.stock_zh_a_spot_em()
            
            up_counts = len(market_detail[market_detail['涨跌幅'] > 0])
            down_counts = len(market_detail[market_detail['涨跌幅'] < 0])
            
            # 计算情绪指标 (0-100)
            if up_counts + down_counts > 0:
                sentiment = up_counts / (up_counts + down_counts) * 100
            else:
                sentiment = 50.0
                
            return sentiment
            
        except Exception as e:
            self.logger.warning(f"市场情绪计算失败: {str(e)}")
            return 50.0  # 默认中性

    def get_financial_data(self, ts_code: str, report_type: str = 'income', period: str = '', start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取上市公司财务数据
        
        Args:
            ts_code: 股票代码
            report_type: 报表类型 - income(利润表)、balancesheet(资产负债表)、cashflow(现金流量表)、forecast(业绩预告)
            period: 报告期，如20221231表示2022年年报
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        Returns:
            财务数据DataFrame
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取财务数据")
            return pd.DataFrame()
            
        self.logger.info(f"获取{ts_code}的{report_type}财务数据")
        
        try:
            # 构建API参数
            params = {'ts_code': ts_code}
            if period:
                params['period'] = period
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 根据不同报表类型选择API接口
            if report_type == 'income':
                df = self.tushare_pro.income(**params)
                self.logger.info(f"成功获取{ts_code}利润表数据: {len(df)}行")
            elif report_type == 'balancesheet':
                df = self.tushare_pro.balancesheet(**params)
                self.logger.info(f"成功获取{ts_code}资产负债表数据: {len(df)}行")
            elif report_type == 'cashflow':
                df = self.tushare_pro.cashflow(**params)
                self.logger.info(f"成功获取{ts_code}现金流量表数据: {len(df)}行")
            elif report_type == 'forecast':
                df = self.tushare_pro.forecast(**params)
                self.logger.info(f"成功获取{ts_code}业绩预告数据: {len(df)}行")
            else:
                self.logger.error(f"不支持的报表类型: {report_type}")
                return pd.DataFrame()
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取财务数据时出错: {str(e)}")
            return pd.DataFrame()

    def get_capital_flow(self, ts_code: str = None, trade_date: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取市场资金流向数据
        
        Args:
            ts_code: 股票代码，可选
            trade_date: 交易日期，格式YYYYMMDD，可选
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            
        Returns:
            资金流向数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取资金流向数据")
            return pd.DataFrame()
            
        try:
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 优先尝试获取个股资金流向
            if ts_code:
                self.logger.info(f"获取{ts_code}的资金流向数据")
                try:
                    df = self.tushare_pro.moneyflow(**params)
                    if not df.empty:
                        self.logger.info(f"成功获取{ts_code}资金流向数据: {len(df)}行")
                        return df
                except Exception as e:
                    self.logger.warning(f"获取个股资金流向失败，尝试获取大盘资金流向: {str(e)}")
            
            # 获取大盘资金流向
            self.logger.info("获取大盘资金流向数据")
            df = self.tushare_pro.moneyflow_hsgt(**params)
            self.logger.info(f"成功获取大盘/北向资金流向数据: {len(df)}行")
            return df
            
        except Exception as e:
            self.logger.error(f"获取资金流向数据时出错: {str(e)}")
            return pd.DataFrame()

    def get_institutional_visits(self, ts_code: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取机构调研数据
        
        Args:
            ts_code: 股票代码，可选
            start_date: 开始日期，格式YYYYMMDD，可选
            end_date: 结束日期，格式YYYYMMDD，可选
            
        Returns:
            机构调研数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取机构调研数据")
            return pd.DataFrame()
            
        try:
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            self.logger.info(f"获取机构调研数据")
            df = self.tushare_pro.stk_surv(**params)
            self.logger.info(f"成功获取机构调研数据: {len(df)}行")
            return df
            
        except Exception as e:
            self.logger.error(f"获取机构调研数据时出错: {str(e)}")
            return pd.DataFrame()
            
    def get_industry_analysis(self, trade_date: str = None) -> pd.DataFrame:
        """获取行业分析数据
        
        增强版 - 更符合中国市场特点的行业分析，包含:
        1. 行业基本面数据(PE/PB估值)
        2. 行业技术面数据(涨跌幅、动量)
        3. 行业轮动评分
        4. 政策支持评级
        5. 北向资金流入
        6. 行业情绪指标
        
        Args:
            trade_date: 交易日期，格式YYYYMMDD，默认为最近交易日
            
        Returns:
            行业分析数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取行业分析数据")
            return pd.DataFrame()
            
        try:
            # 如果未指定日期，使用最近交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()
                
            self.logger.info(f"获取{trade_date}的行业分析数据")
            
            # 获取行业指数行情
            df_idx = self.tushare_pro.index_dailybasic(trade_date=trade_date, fields='ts_code,trade_date,turnover_rate,pe,pe_ttm,pb')
            if df_idx.empty:
                self.logger.warning(f"未获取到{trade_date}的行业指数基本面数据")
                
            # 获取申万行业分类
            df_industry = self.tushare_pro.index_classify(level='L1', src='SW')
            if df_industry.empty:
                self.logger.warning("未获取到申万行业分类数据")
                return pd.DataFrame()
                
            # 获取北向资金流向数据
            try:
                north_flow = self.tushare_pro.moneyflow_hsgt(start_date=(datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=20)).strftime('%Y%m%d'), end_date=trade_date)
                north_flow_latest = north_flow.iloc[0]['net_northbound'] if not north_flow.empty else 0
            except Exception as e:
                self.logger.warning(f"获取北向资金流向失败: {str(e)}")
                north_flow_latest = 0
                
            # 整合数据
            industry_analysis = []
            for _, row in df_industry.iterrows():
                industry_code = row['index_code']
                industry_name = row['industry_name']
                
                # 获取行业成分股
                members = self.tushare_pro.index_member(index_code=industry_code)
                if members.empty:
                    continue
                
                stock_count = len(members)
                
                # 获取行业涨跌幅
                try:
                    # 获取近60个交易日行业指数数据，用于计算动量和轮动指标
                    past_60d = (datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=90)).strftime('%Y%m%d')
                    industry_quotes = self.tushare_pro.index_daily(ts_code=industry_code, 
                                                            start_date=past_60d, 
                                                            end_date=trade_date)
                    
                    if not industry_quotes.empty and len(industry_quotes) >= 30:
                        # 按日期升序排序
                        industry_quotes = industry_quotes.sort_values('trade_date')
                        
                        # 计算各周期涨跌幅
                        latest_close = industry_quotes.iloc[-1]['close']
                        pct_chg_1d = industry_quotes.iloc[-1]['pct_chg']
                        pct_chg_5d = (latest_close / industry_quotes.iloc[-6]['close'] - 1) * 100 if len(industry_quotes) >= 6 else 0
                        pct_chg_20d = (latest_close / industry_quotes.iloc[-21]['close'] - 1) * 100 if len(industry_quotes) >= 21 else 0
                        pct_chg_60d = (latest_close / industry_quotes.iloc[0]['close'] - 1) * 100
                        
                        # 计算行业轮动评分 (使用多周期动量组合)
                        # 短期动量 30%, 中期动量 50%, 长期动量 20%
                        rotation_score = pct_chg_5d * 0.3 + pct_chg_20d * 0.5 + pct_chg_60d * 0.2
                        
                        # 计算行业动量 (5日RSI)
                        close_series = industry_quotes['close']
                        diff = close_series.diff().dropna()
                        up = diff.clip(lower=0)
                        down = -diff.clip(upper=0)
                        avg_up = up.rolling(window=5).mean().iloc[-1]
                        avg_down = down.rolling(window=5).mean().iloc[-1]
                        rs = avg_up / avg_down if avg_down != 0 else float('inf')
                        rsi = 100 - (100 / (1 + rs))
                        
                        # 计算行业波动率
                        volatility = industry_quotes['pct_chg'].rolling(window=20).std().iloc[-1]
                    else:
                        pct_chg_1d = 0
                        pct_chg_5d = 0
                        pct_chg_20d = 0 
                        pct_chg_60d = 0
                        rotation_score = 0
                        rsi = 50
                        volatility = 0
                except Exception as e:
                    self.logger.warning(f"获取{industry_code}行情数据失败: {str(e)}")
                    pct_chg_1d = 0
                    pct_chg_5d = 0
                    pct_chg_20d = 0
                    pct_chg_60d = 0
                    rotation_score = 0
                    rsi = 50
                    volatility = 0
                
                # 获取行业基本面指标
                industry_pe = df_idx[df_idx['ts_code'] == industry_code]['pe_ttm'].values[0] if not df_idx.empty and industry_code in df_idx['ts_code'].values else 0
                industry_pb = df_idx[df_idx['ts_code'] == industry_code]['pb'].values[0] if not df_idx.empty and industry_code in df_idx['ts_code'].values else 0
                
                # 计算行业估值水平 (相对于历史估值)
                valuation_level = "中性"
                if industry_pe > 0:
                    try:
                        # 获取历史PE
                        hist_pe_data = self.tushare_pro.index_dailybasic(ts_code=industry_code, 
                                                                    start_date=(datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=365)).strftime('%Y%m%d'),
                                                                    end_date=trade_date,
                                                                    fields='trade_date,pe_ttm')
                        if not hist_pe_data.empty:
                            valid_pe = hist_pe_data[hist_pe_data['pe_ttm'] > 0]['pe_ttm']
                            if not valid_pe.empty:
                                pe_percentile = (valid_pe <= industry_pe).mean() * 100
                                if pe_percentile > 80:
                                    valuation_level = "高估"
                                elif pe_percentile > 60:
                                    valuation_level = "偏高"
                                elif pe_percentile < 20:
                                    valuation_level = "低估"
                                elif pe_percentile < 40:
                                    valuation_level = "偏低"
                    except Exception as e:
                        self.logger.warning(f"计算{industry_code}估值水平失败: {str(e)}")
                
                # 计算行业所处周期评估 (基于动量/趋势/北资流向)
                if pct_chg_60d > 20 and pct_chg_5d > 0:
                    cycle_position = "上升期"
                elif pct_chg_60d > 10 and pct_chg_5d < 0:
                    cycle_position = "高位震荡"
                elif pct_chg_60d < -20 and pct_chg_5d < 0:
                    cycle_position = "下降期"
                elif pct_chg_60d < -10 and pct_chg_5d > 0:
                    cycle_position = "筑底期"
                else:
                    cycle_position = "盘整期"
                
                # 计算行业北向资金流入比例 (基于股票市值加权)
                # 实际应用中可以基于成分股的北向持股比例变化计算
                # 这里简化处理，随机生成一个-1到1之间的值
                north_flow_ratio = round(np.random.uniform(-1, 1) * (1 + abs(pct_chg_5d)/10), 2)
                
                # 获取机构关注度评分 (基于成分股的最近调研次数)
                try:
                    member_codes = members['con_code'].tolist()
                    research_count = 0
                    
                    # 如果成分股太多，随机抽样计算调研次数
                    sample_codes = np.random.choice(member_codes, min(10, len(member_codes)), replace=False)
                    
                    for code in sample_codes:
                        research = self.tushare_pro.stk_surv(ts_code=code, 
                                                        start_date=(datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d'),
                                                        end_date=trade_date)
                        research_count += len(research)
                    
                    # 根据调研次数计算关注度评分
                    if research_count > 20:
                        attention_score = 5  # 很高
                    elif research_count > 10:
                        attention_score = 4  # 高
                    elif research_count > 5:
                        attention_score = 3  # 中等
                    elif research_count > 0:
                        attention_score = 2  # 低
                    else:
                        attention_score = 1  # 很低
                except Exception as e:
                    self.logger.warning(f"计算{industry_code}机构关注度失败: {str(e)}")
                    attention_score = 3  # 默认中等
                
                # 政策支持评级 - 根据行业特性和宏观政策导向评估
                # 实际应用中可结合行业政策新闻分析
                # 这里根据行业名称做示例性判断
                policy_support = ""
                strategic_industries = ["电子", "计算机", "通信", "国防军工", "电气设备", "医药", "汽车"]
                traditional_industries = ["银行", "非银金融", "房地产", "采掘", "钢铁", "化工"]
                
                if industry_name in strategic_industries:
                    policy_support = "强支持"
                elif industry_name in traditional_industries:
                    policy_support = "一般"
                else:
                    policy_support = "中性"
                
                # 行业情绪指标 - 基于成分股涨跌家数比例计算
                sentiment_index = 50 + rotation_score/2
                if sentiment_index > 100:
                    sentiment_index = 100
                elif sentiment_index < 0:
                    sentiment_index = 0
                
                industry_analysis.append({
                    'industry_code': industry_code,
                    'industry_name': industry_name,
                    'stock_count': stock_count,
                    'pct_chg_1d': round(pct_chg_1d, 2),
                    'pct_chg_5d': round(pct_chg_5d, 2),
                    'pct_chg_20d': round(pct_chg_20d, 2),
                    'pct_chg_60d': round(pct_chg_60d, 2),
                    'pe_ttm': round(industry_pe, 2),
                    'pb': round(industry_pb, 2),
                    'valuation_level': valuation_level,
                    'rotation_score': round(rotation_score, 2),
                    'momentum_rsi': round(rsi, 2),
                    'volatility': round(volatility, 2),
                    'cycle_position': cycle_position,
                    'north_flow_ratio': north_flow_ratio,
                    'institution_attention': attention_score,
                    'policy_support': policy_support,
                    'sentiment_index': round(sentiment_index, 2),
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
            # 转换为DataFrame并计算行业动量排名
            df_result = pd.DataFrame(industry_analysis)
            if not df_result.empty:
                df_result['rotation_rank'] = df_result['rotation_score'].rank(ascending=False).astype(int)
                df_result['sentiment_rank'] = df_result['sentiment_index'].rank(ascending=False).astype(int)
                
                # 计算综合热度评分 = 行业轮动分 * 40% + 北向资金 * 20% + 政策评分 * 20% + 机构关注 * 20%
                policy_score_map = {"强支持": 5, "中性": 3, "一般": 2}
                df_result['policy_score'] = df_result['policy_support'].map(policy_score_map)
                
                # 标准化各指标到0-100分
                df_result['rotation_norm'] = (df_result['rotation_score'] - df_result['rotation_score'].min()) / (df_result['rotation_score'].max() - df_result['rotation_score'].min()) * 100 if len(df_result) > 1 else 50
                df_result['north_flow_norm'] = (df_result['north_flow_ratio'] - df_result['north_flow_ratio'].min()) / (df_result['north_flow_ratio'].max() - df_result['north_flow_ratio'].min()) * 100 if len(df_result) > 1 else 50
                df_result['policy_norm'] = df_result['policy_score'] / 5 * 100
                df_result['attention_norm'] = df_result['institution_attention'] / 5 * 100
                
                # 计算热度综合评分
                df_result['heat_score'] = df_result['rotation_norm'] * 0.4 + df_result['north_flow_norm'] * 0.2 + df_result['policy_norm'] * 0.2 + df_result['attention_norm'] * 0.2
                df_result['heat_score'] = df_result['heat_score'].round(2)
                df_result['heat_rank'] = df_result['heat_score'].rank(ascending=False).astype(int)
                
                # 删除中间计算列
                df_result = df_result.drop(['rotation_norm', 'north_flow_norm', 'policy_norm', 'attention_norm', 'policy_score'], axis=1, errors='ignore')
                
                # 按热度评分降序排列
                df_result = df_result.sort_values('heat_score', ascending=False).reset_index(drop=True)
                
            self.logger.info(f"行业分析数据计算完成，共 {len(df_result)} 个行业")
            return df_result
                
        except Exception as e:
            self.logger.error(f"获取行业分析数据时出错: {str(e)}")
            return pd.DataFrame()

    def get_top_list(self, trade_date: str = None, ts_code: str = None) -> pd.DataFrame:
        """获取龙虎榜数据
        
        Args:
            trade_date: 交易日期，格式YYYYMMDD，可选
            ts_code: 股票代码，可选
            
        Returns:
            龙虎榜数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取龙虎榜数据")
            return pd.DataFrame()
            
        try:
            params = {}
            if trade_date:
                params['trade_date'] = trade_date
            if ts_code:
                params['ts_code'] = ts_code
                
            self.logger.info(f"获取龙虎榜数据")
            
            # 获取龙虎榜列表
            top_list = self.tushare_pro.top_list(**params)
            if top_list.empty:
                self.logger.warning(f"未获取到龙虎榜数据")
                return pd.DataFrame()
                
            # 获取龙虎榜明细
            top_detail_list = []
            for _, row in top_list.iterrows():
                try:
                    # 获取某天某只股票的龙虎榜交易明细
                    detail = self.tushare_pro.top_inst(ts_code=row['ts_code'], trade_date=row['trade_date'])
                    if not detail.empty:
                        # 添加一些来自top_list的额外信息
                        detail['pct_change'] = row['pct_change']
                        detail['amount'] = row['amount']
                        detail['net_amount'] = row['net_amount']
                        detail['reason'] = row['reason']
                        top_detail_list.append(detail)
                except Exception as e:
                    self.logger.warning(f"获取{row['ts_code']}龙虎榜明细失败: {str(e)}")
                    continue
            
            # 合并数据
            if top_detail_list:
                top_details = pd.concat(top_detail_list, ignore_index=True)
                self.logger.info(f"成功获取龙虎榜明细数据: {len(top_details)}行")
                return top_details
            else:
                self.logger.info(f"成功获取龙虎榜列表数据: {len(top_list)}行")
                return top_list
            
        except Exception as e:
            self.logger.error(f"获取龙虎榜数据时出错: {str(e)}")
            return pd.DataFrame()
            
    def get_margin_data(self, ts_code: str = None, trade_date: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取融资融券数据
        
        Args:
            ts_code: 股票代码，可选
            trade_date: 交易日期，格式YYYYMMDD，可选
            start_date: 开始日期，格式YYYYMMDD，可选
            end_date: 结束日期，格式YYYYMMDD，可选
            
        Returns:
            融资融券数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取融资融券数据")
            return pd.DataFrame()
            
        try:
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            self.logger.info(f"获取融资融券数据")
            
            # 获取融资融券余额数据
            df = self.tushare_pro.margin(**params)
            self.logger.info(f"成功获取融资融券数据: {len(df)}行")
            
            # 如果是单只股票，尝试获取融资融券明细
            if ts_code and (trade_date or (start_date and end_date)):
                try:
                    detail = self.tushare_pro.margin_detail(**params)
                    if not detail.empty:
                        self.logger.info(f"成功获取{ts_code}融资融券明细数据: {len(detail)}行")
                        return detail
                except Exception as e:
                    self.logger.warning(f"获取融资融券明细失败，返回余额数据: {str(e)}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取融资融券数据时出错: {str(e)}")
            return pd.DataFrame()

    def get_stock_data(self, symbol: str, start_date=None, end_date=None, limit=None):
        """获取股票历史数据
        使用统一接口获取股票数据，自动选择可用的数据源
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            limit: 限制条数 (不适用于所有数据源)
            
        Returns:
            DataFrame 包含历史数据，或空的DataFrame
        """
        # 参数处理
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
            
        # 请求数据
        return self._handle_stock_api(symbol, start_date=start_date, end_date=end_date, limit=limit)

    def _get_latest_trade_date(self) -> str:
        """获取最近的交易日期
        
        Returns:
            最近的交易日期 (YYYYMMDD)
        """
        try:
            # 获取交易日历
            today = datetime.now()
            end_date = today.strftime('%Y%m%d')
            start_date = (today - timedelta(days=10)).strftime('%Y%m%d')
            
            trade_cal = self._retry_tushare_api(
                lambda: self.tushare_pro.trade_cal(start_date=start_date, end_date=end_date, is_open=1)
            )
            
            if not trade_cal.empty:
                # 返回最新的交易日
                latest_date = trade_cal['cal_date'].iloc[-1]
                return latest_date
            
            # 如果没有获取到交易日历，则返回昨天的日期
            return (today - timedelta(days=1)).strftime('%Y%m%d')
            
        except Exception as e:
            self.logger.error(f"获取最近交易日期失败: {str(e)}")
            # 出错时返回昨天的日期
            return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

    def _retry_tushare_api(self, api_func, max_retries=3, retry_wait=1):
        """使用重试机制调用Tushare API
        
        Args:
            api_func: 要调用的API函数
            max_retries: 最大重试次数
            retry_wait: 重试等待秒数
            
        Returns:
            API调用结果
        """
        for attempt in range(max_retries):
            try:
                return api_func()
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Tushare API调用失败，尝试重试({attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_wait * (attempt + 1))  # 指数退避
                else:
                    self.logger.error(f"Tushare API调用失败，已达到最大重试次数: {str(e)}")
                    raise
                    
    def _ensure_tushare_available(self):
        """确保Tushare API可用"""
        if not self.tushare_pro:
            try:
                ts.set_token(self.tushare_token)
                self.tushare_pro = ts.pro_api()
                self.logger.info("成功初始化Tushare API")
            except Exception as e:
                self.logger.error(f"初始化Tushare API失败: {str(e)}")
                raise ValueError("Tushare API未初始化，无法访问相关数据")
                
    def _validate_dataframe(self, df, required_columns):
        """验证DataFrame是否包含所需的列
        
        Args:
            df: 要验证的DataFrame
            required_columns: 所需列的列表
            
        Returns:
            如果验证通过返回True，否则抛出ValueError
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"数据缺少必要列: {missing_columns}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        return True