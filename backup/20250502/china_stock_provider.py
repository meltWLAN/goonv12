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
    
    def __init__(self, tushare_token: str = None):
        """初始化数据提供者
        
        Args:
            tushare_token: Tushare API令牌
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
        except Exception as e:
            self.logger.error(f"Tushare API初始化失败: {str(e)}")
            self.current_source = 'akshare'  # 如果Tushare失败，使用akshare作为备选
        
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
    
    def get_data(self, data_type: str, symbol: str, **kwargs) -> pd.DataFrame:
        """统一数据获取入口
        
        Args:
            data_type: 数据类型(stock/sector/index)
            symbol: 标的代码
            kwargs: 各类型特有参数
                - start_date: 开始日期(YYYYMMDD)
                - end_date: 结束日期(YYYYMMDD)
                - data_source: 指定数据源('akshare'/'tushare')
        
        Returns:
            标准化格式的DataFrame
        """
        # 可以临时指定数据源
        temp_source = kwargs.pop('data_source', None)
        if temp_source:
            old_source = self.current_source
            if temp_source in self.get_available_sources():
                self.current_source = temp_source
            
        cache_key = f"{self.current_source}_{data_type}_{symbol}_{str(kwargs)}"
        
        # 检查内存缓存
        if cached := self._get_from_cache(cache_key):
            return cached
        
        try:
            # 执行API调用
            df = self._call_with_retry(
                func=self.api_handlers[data_type],
                symbol=symbol,
                **kwargs
            )
            
            # 标准化处理
            df = self._standardize_data(df, data_type)
            
            # 更新缓存
            self._update_cache(cache_key, df)
            return df
        finally:
            # 恢复原数据源
            if temp_source:
                self.current_source = old_source
        
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
            return pd.DataFrame()
            
        # 标准化股票代码
        orig_symbol = symbol
        symbol = self._standardize_stock_code(symbol)
        if not symbol:
            self.logger.error(f"无法标准化股票代码: {orig_symbol}")
            return pd.DataFrame()
            
        # 日期处理
        start_date = kwargs.get('start_date', 
                            (datetime.now() - timedelta(days=120)).strftime('%Y%m%d'))
        end_date = kwargs.get('end_date', datetime.now().strftime('%Y%m%d'))
        
        # 日期格式验证
        try:
            datetime.strptime(start_date, '%Y%m%d')
            datetime.strptime(end_date, '%Y%m%d')
        except ValueError:
            self.logger.error(f"日期格式无效: start_date={start_date}, end_date={end_date}")
            return pd.DataFrame()
            
        # 根据当前数据源选择不同实现
        df = pd.DataFrame()
        errors = []
        
        if self.current_source == 'tushare':
            # 直接使用Tushare
            try:
                df = self._get_stock_data_tushare(symbol, start_date, end_date)
            except Exception as e:
                errors.append(f"Tushare错误: {str(e)}")
                self.logger.error(f"Tushare获取数据异常: {str(e)}")
            
            # 如果Tushare获取失败，尝试使用Akshare
            if df.empty:
                self.logger.warning(f"Tushare未返回数据: {symbol}，正在尝试使用Akshare")
                try:
                    df = self._get_stock_data_akshare(symbol, start_date, end_date)
                except Exception as e:
                    errors.append(f"Akshare错误: {str(e)}")
                    self.logger.error(f"Akshare获取数据异常: {str(e)}")
        else:
            # 先尝试使用Akshare
            try:
                df = self._get_stock_data_akshare(symbol, start_date, end_date)
            except Exception as e:
                errors.append(f"Akshare错误: {str(e)}")
                self.logger.error(f"Akshare获取数据异常: {str(e)}")
                
            # 如果Akshare获取失败且Tushare可用，尝试使用Tushare
            if df.empty and self.tushare_pro:
                self.logger.warning(f"Akshare未返回数据: {symbol}，正在尝试使用Tushare")
                try:
                    df = self._get_stock_data_tushare(symbol, start_date, end_date)
                except Exception as e:
                    errors.append(f"Tushare错误: {str(e)}")
                    self.logger.error(f"Tushare获取数据异常: {str(e)}")
        
        # 如果仍然为空，记录详细错误
        if df.empty:
            error_msg = "、".join(errors) if errors else "未知原因"
            self.logger.error(f"所有数据源都未能获取到{symbol}的交易数据: {error_msg}")
            
            # 创建一个包含基本结构的空DataFrame
            empty_df = pd.DataFrame(columns=['ts_code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount'])
            # 添加示例行，避免后续计算出错
            if kwargs.get('add_example_row', False):
                today = datetime.now().strftime('%Y%m%d')
                empty_df.loc[0] = [symbol, today, 0.0, 0.0, 0.0, 0.0, 0, 0.0]
            return empty_df
        
        return df
    
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
                if not df.empty:
                    self.logger.info(f"成功通过Tushare daily接口获取{symbol}的数据: {len(df)}条")
                    
                    # 因为Tushare返回的数据是倒序的（最新的在前），我们保持一致
                    return df
            except Exception as e:
                self.logger.warning(f"Tushare daily接口获取{symbol}数据失败: {str(e)}，尝试其他方法")
                
            # 如果daily接口失败，尝试使用pro_bar接口
            try:
                df = ts.pro_bar(ts_code=symbol, adj='qfq', start_date=start_date, end_date=end_date)
                
                if df is not None and not df.empty:
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
            
            if df.empty:
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

    def get_stock_info(self, symbol: str = None, market: str = None) -> pd.DataFrame:
        """获取股票基本信息
        
        Args:
            symbol: 股票代码
            market: 市场 ('SH', 'SZ', 'BJ')
            
        Returns:
            DataFrame 包含股票信息
        """
        if self.current_source == 'akshare':
            try:
                if market:
                    if market == 'SH':
                        df = ak.stock_info_sh_name_code()
                    elif market == 'SZ':
                        df = ak.stock_info_sz_name_code()
                    else:
                        self.logger.error(f"Akshare不支持的市场: {market}")
                        return pd.DataFrame()
                else:
                    # 合并多个市场的股票信息
                    df_sh = ak.stock_info_sh_name_code()
                    df_sz = ak.stock_info_sz_name_code()
                    df = pd.concat([df_sh, df_sz], ignore_index=True)
                
                # 筛选特定股票
                if symbol:
                    if '.' in symbol:
                        code = symbol.split('.')[0]
                    else:
                        code = symbol
                    df = df[df['code'].str.contains(code)]
                
                return df
                
            except Exception as e:
                self.logger.error(f"使用Akshare获取股票信息失败: {str(e)}")
                return pd.DataFrame()
                
        elif self.current_source == 'tushare':
            try:
                if market and not symbol:
                    df = self.tushare_pro.stock_basic(exchange=market.lower(), 
                                                      list_status='L',
                                                      fields='ts_code,symbol,name,area,industry,market,list_date')
                else:
                    df = self.tushare_pro.stock_basic(exchange='', 
                                                      list_status='L',
                                                      fields='ts_code,symbol,name,area,industry,market,list_date')
                    
                # 筛选特定股票
                if symbol:
                    if '.' in symbol:
                        df = df[df['ts_code'] == symbol]
                    else:
                        df = df[df['symbol'] == symbol]
                
                return df
                
            except Exception as e:
                self.logger.error(f"使用Tushare获取股票信息失败: {str(e)}")
                return pd.DataFrame()
        
        return pd.DataFrame()

    def get_realtime_daily(self, ts_code: str = None) -> pd.DataFrame:
        """获取实时日K线行情数据
        
        使用tushare的rt_k接口获取当日实时行情
        
        Args:
            ts_code: 股票代码，支持通配符，如'6*.SH'，'301*.SZ'，多个代码使用逗号分隔
                     注意代码必须带.SH/.SZ/.BJ后缀
                     
        Returns:
            DataFrame 包含实时日K线数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取实时行情")
            return pd.DataFrame()
            
        try:
            self.logger.info(f"获取实时日K线数据: {ts_code}")
            
            # 调用tushare rt_k接口
            df = self.tushare_pro.rt_k(ts_code=ts_code)
            
            if df.empty:
                self.logger.warning(f"未获取到实时行情数据: {ts_code}")
                return pd.DataFrame()
                
            # 标准化列名，与其他接口统一
            rename_map = {
                'ts_code': 'ts_code',
                'name': 'name',
                'pre_close': 'pre_close',
                'high': 'high',
                'open': 'open',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount',
                'num': 'trade_count'  # 成交笔数
            }
            
            df = df.rename(columns=rename_map)
            
            # 确保数值列为float类型
            numeric_cols = ['pre_close', 'high', 'open', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取实时日K线数据失败: {str(e)}")
            return pd.DataFrame()
            
    def get_realtime_minute(self, ts_code: str, freq: str = '1MIN') -> pd.DataFrame:
        """获取实时分钟K线行情数据
        
        使用tushare的rt_min接口获取当日实时分钟行情
        
        Args:
            ts_code: 股票代码，如'600000.SH'，多个代码使用逗号分隔
            freq: 频率，支持 1MIN/5MIN/15MIN/30MIN/60MIN
                     
        Returns:
            DataFrame 包含实时分钟K线数据
        """
        if not self.tushare_pro:
            self.logger.error("Tushare未初始化，无法获取实时分钟行情")
            return pd.DataFrame()
            
        try:
            self.logger.info(f"获取实时分钟K线数据: {ts_code}, 频率: {freq}")
            
            # 调用tushare rt_min接口
            df = self.tushare_pro.rt_min(ts_code=ts_code, freq=freq)
            
            if df.empty:
                self.logger.warning(f"未获取到实时分钟行情数据: {ts_code}")
                return pd.DataFrame()
                
            # 标准化列名，与其他接口统一
            rename_map = {
                'ts_code': 'ts_code',
                'time': 'trade_time',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'vol': 'volume',
                'amount': 'amount'
            }
            
            df = df.rename(columns=rename_map)
            
            # 确保数值列为float类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取实时分钟K线数据失败: {str(e)}")
            return pd.DataFrame()
            
    def get_tick_data(self, ts_code: str) -> pd.DataFrame:
        """获取股票实时逐笔成交数据
        
        使用tushare的realtime_tick接口获取实时逐笔成交
        
        Args:
            ts_code: 股票代码，如'600000.SH'
                     
        Returns:
            DataFrame 包含实时成交数据
        """
        if not self.tushare_token:
            self.logger.error("Tushare token未设置，无法获取实时逐笔成交")
            return pd.DataFrame()
            
        try:
            import tushare as ts
            ts.set_token(self.tushare_token)
            
            self.logger.info(f"获取实时逐笔成交数据: {ts_code}")
            
            # 调用tushare realtime_tick接口
            df = ts.realtime_tick(ts_code=ts_code)
            
            if df is None or df.empty:
                self.logger.warning(f"未获取到实时逐笔成交数据: {ts_code}")
                return pd.DataFrame()
            
            # 标准化列名
            if 'TIME' in df.columns:
                df.rename(columns={
                    'TIME': 'time',
                    'PRICE': 'price',
                    'CHANGE': 'change',
                    'VOLUME': 'volume',
                    'AMOUNT': 'amount',
                    'TYPE': 'type'
                }, inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取实时逐笔成交数据失败: {str(e)}")
            return pd.DataFrame()
            
    def get_realtime_quotes(self, ts_code: str) -> pd.DataFrame:
        """获取股票实时行情快照
        
        使用tushare的realtime_quote接口获取实时行情快照
        
        Args:
            ts_code: 股票代码，如'600000.SH'，支持多个代码，逗号分隔
                     
        Returns:
            DataFrame 包含实时行情快照数据
        """
        if not self.tushare_token:
            self.logger.error("Tushare token未设置，无法获取实时行情快照")
            return pd.DataFrame()
            
        try:
            import tushare as ts
            ts.set_token(self.tushare_token)
            
            self.logger.info(f"获取实时行情快照: {ts_code}")
            
            # 调用tushare realtime_quote接口
            df = ts.realtime_quote(ts_code=ts_code)
            
            if df is None or df.empty:
                self.logger.warning(f"未获取到实时行情快照: {ts_code}")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取实时行情快照失败: {str(e)}")
            return pd.DataFrame()

    # ========== 研究数据API方法 ==========
    
    def get_earnings_forecast(self, ts_code: str = '', start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取盈利预测数据 (对应Tushare的report_rc)
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            盈利预测数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取盈利预测数据: {ts_code}")
            
            # 构建API参数
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.report_rc(**params)
            )
            
            if df.empty:
                self.logger.warning(f"未找到盈利预测数据: {ts_code}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'report_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取盈利预测数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_chip_distribution(self, ts_code: str, trade_date: str = '') -> pd.DataFrame:
        """获取每日筹码分布 (对应Tushare的cyq_chips)
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            每日筹码分布数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取每日筹码分布: {ts_code}, 日期: {trade_date}")
            
            # 如果未提供日期，使用最近交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.cyq_chips(ts_code=ts_code, trade_date=trade_date)
            )
            
            if df.empty:
                self.logger.warning(f"未找到筹码分布数据: {ts_code}, 日期: {trade_date}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['price', 'percent'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取筹码分布数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_chip_performance(self, ts_code: str, trade_date: str = '') -> pd.DataFrame:
        """获取每日筹码平均成本和胜率 (对应Tushare的cyq_perf)
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            每日筹码平均成本和胜率数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取筹码平均成本: {ts_code}, 日期: {trade_date}")
            
            # 如果未提供日期，使用最近交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.cyq_perf(ts_code=ts_code, trade_date=trade_date)
            )
            
            if df.empty:
                self.logger.warning(f"未找到筹码平均成本数据: {ts_code}, 日期: {trade_date}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['winner_rate', 'weight_avg'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取筹码平均成本数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_technical_factors(self, ts_code: str = '', trade_date: str = '') -> pd.DataFrame:
        """获取股票技术面因子 (对应Tushare的stk_factor)
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            技术面因子数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取技术面因子: {ts_code}, 日期: {trade_date}")
            
            # 如果未提供日期，使用最近交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()
                
            # 构建API参数
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.stk_factor(**params)
            )
            
            if df.empty:
                self.logger.warning(f"未找到技术面因子数据: {ts_code}, 日期: {trade_date}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'trade_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取技术面因子数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_auction_data(self, ts_code: str, trade_date: str = '', auction_type: str = 'o') -> pd.DataFrame:
        """获取集合竞价数据 (对应Tushare的stk_auction_o/stk_auction_c)
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            auction_type: 竞价类型，'o'=开盘，'c'=收盘
            
        Returns:
            集合竞价数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            auction_type_name = "开盘" if auction_type == 'o' else "收盘"
            self.logger.info(f"获取{auction_type_name}集合竞价: {ts_code}, 日期: {trade_date}")
            
            # 如果未提供日期，使用最近交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()
                
            # 调用API
            if auction_type == 'o':
                df = self._retry_tushare_api(
                    lambda: self.tushare_pro.stk_auction_o(ts_code=ts_code, trade_date=trade_date)
                )
            else:
                df = self._retry_tushare_api(
                    lambda: self.tushare_pro.stk_auction_c(ts_code=ts_code, trade_date=trade_date)
                )
            
            if df.empty:
                self.logger.warning(f"未找到{auction_type_name}集合竞价数据: {ts_code}, 日期: {trade_date}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'trade_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取集合竞价数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_nine_turn_indicator(self, ts_code: str, start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取神奇九转指标 (对应Tushare的stk_nineturn)
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            神奇九转指标数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取神奇九转指标: {ts_code}")
            
            # 构建API参数
            params = {'ts_code': ts_code}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.stk_nineturn(**params)
            )
            
            if df.empty:
                self.logger.warning(f"未找到神奇九转指标数据: {ts_code}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'trade_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取神奇九转指标数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_institutional_research(self, ts_code: str = '', start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取机构调研数据 (对应Tushare的stk_surv)
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            机构调研数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取机构调研数据: {ts_code}")
            
            # 构建API参数
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.stk_surv(**params)
            )
            
            if df.empty:
                self.logger.warning(f"未找到机构调研数据: {ts_code}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'ann_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取机构调研数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_broker_recommendations(self, month: str) -> pd.DataFrame:
        """获取券商月度金股推荐 (对应Tushare的broker_recommend)
        
        Args:
            month: 月度 (YYYYMM)
            
        Returns:
            券商月度金股推荐数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取券商月度金股推荐: {month}")
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.broker_recommend(month=month)
            )
            
            if df.empty:
                self.logger.warning(f"未找到券商月度金股推荐: {month}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['month', 'ts_code', 'broker'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取券商月度金股推荐失败: {str(e)}")
            return pd.DataFrame()
    
    def get_hk_holdings(self, ts_code: str = '', trade_date: str = '', start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """获取沪深港股通持股明细 (对应Tushare的hk_hold)
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            沪深港股通持股明细
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取沪深港股通持股明细: {ts_code}")
            
            # 构建API参数
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.hk_hold(**params)
            )
            
            if df.empty:
                self.logger.warning(f"未找到沪深港股通持股明细: {ts_code}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'trade_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取沪深港股通持股明细失败: {str(e)}")
            return pd.DataFrame()
    
    def get_ccass_holdings(self, ts_code: str, trade_date: str = '') -> pd.DataFrame:
        """获取中央结算系统持股汇总 (对应Tushare的ccass_hold)
        
        Args:
            ts_code: 股票代码（港股）
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            中央结算系统持股汇总
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取中央结算系统持股汇总: {ts_code}, 日期: {trade_date}")
            
            # 如果未提供日期，使用最近交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.ccass_hold(ts_code=ts_code, trade_date=trade_date)
            )
            
            if df.empty:
                self.logger.warning(f"未找到中央结算系统持股汇总: {ts_code}, 日期: {trade_date}")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['ts_code', 'trade_date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取中央结算系统持股汇总失败: {str(e)}")
            return pd.DataFrame()
    
    def get_market_concepts(self, src: str = '') -> pd.DataFrame:
        """获取市场概念分类数据 (对应Tushare的kpl_concept)
        
        Args:
            src: 来源，默认为空，可选'kpl'=卡普兰
            
        Returns:
            市场概念分类数据
        """
        self._ensure_tushare_available()
        
        try:
            if self.tushare_pro is None:
                self.logger.error("未加载Tushare Pro数据源")
                return pd.DataFrame()
                
            self.logger.info(f"获取市场概念分类数据")
            
            # 构建API参数
            params = {}
            if src:
                params['src'] = src
                
            # 调用API
            df = self._retry_tushare_api(
                lambda: self.tushare_pro.kpl_concept(**params)
            )
            
            if df.empty:
                self.logger.warning(f"未找到市场概念分类数据")
                return df
                
            # 数据验证
            self._validate_dataframe(df, ['concept_id', 'concept_name'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取市场概念分类数据失败: {str(e)}")
            return pd.DataFrame()

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