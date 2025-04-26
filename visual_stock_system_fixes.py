"""
股票系统修复模块 - 包含对visual_stock_system.py中已识别bug的修复

此模块主要用于修复以下问题：
1. analyze_momentum方法无法处理NaN值
2. get_stock_data方法对股票代码和日期格式检查不严格
3. get_stock_name方法缓存机制存在问题
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import re
import time
import types

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fixes.log'
)
logger = logging.getLogger('VisualSystemFixes')

def fixed_analyze_momentum(self, df):
    """
    修复了的动量分析方法，能够处理NaN值和不同列名的情况
    
    修复问题:
    1. 处理数据中的NaN值
    2. 支持不同列名格式
    3. 处理数据行数不足的情况
    
    参数:
        df (DataFrame): 包含价格数据的DataFrame
        
    返回:
        dict: 包含动量分析结果的字典
    """
    try:
        # 确保数据至少有21行以计算EMA21
        if len(df) < 21:
            logger.warning("数据行数不足，无法计算EMA21")
            return {'direction': 'neutral', 'strength': 0.0, 'trend': 'sideways'}
        
        # 确保关键列存在
        if 'close' not in df.columns:
            if 'Close' in df.columns:
                df['close'] = df['Close']
            elif '收盘' in df.columns:
                df['close'] = df['收盘']
            else:
                logger.warning("找不到收盘价列")
                return {'direction': 'neutral', 'strength': 0.0, 'trend': 'sideways'}
        
        # 处理NaN值 - 使用前向和后向填充
        df = df.copy()
        df['close'] = df['close'].ffill().bfill()
        
        # 计算技术指标
        df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA9_21'] = df['EMA9'] - df['EMA21']
        
        # 计算MACD
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']
        
        # 分析动量强度和方向
        current_ema9_21 = df['EMA9_21'].iloc[-1]
        prev_ema9_21 = df['EMA9_21'].iloc[-2]
        
        current_hist = df['Histogram'].iloc[-1]
        prev_hist = df['Histogram'].iloc[-2]
        
        # 确定方向
        if current_ema9_21 > 0 and current_hist > 0:
            direction = 'up'
        elif current_ema9_21 < 0 and current_hist < 0:
            direction = 'down'
        else:
            direction = 'neutral'
        
        # 计算强度（百分比）
        strength = min(abs(current_ema9_21 / df['close'].iloc[-1] * 100), 100)
        
        # 确定趋势
        if strength > 5 and direction == 'up':
            trend = 'uptrend'
        elif strength > 5 and direction == 'down':
            trend = 'downtrend'
        else:
            trend = 'sideways'
        
        result = {
            'direction': direction,
            'strength': round(strength, 2),
            'trend': trend
        }
        
        return result
    except Exception as e:
        logger.error(f"动量分析失败: {str(e)}")
        return {'direction': 'neutral', 'strength': 0.0, 'trend': 'sideways'}

def fixed_get_stock_data(self, symbol, start_date=None, end_date=None, limit=None):
    """
    修复了的获取股票数据方法，增强了对输入参数的验证
    
    修复问题:
    1. 更严格的股票代码格式验证
    2. 更严格的日期格式验证
    3. 改进错误处理逻辑
    
    参数:
        symbol (str): 股票代码，如"000001.SZ"
        start_date (str, 可选): 开始日期，格式为YYYYMMDD或YYYY-MM-DD
        end_date (str, 可选): 结束日期，格式为YYYYMMDD或YYYY-MM-DD
        limit (int, 可选): 返回的最大数据条数
        
    返回:
        DataFrame: 股票历史数据
    """
    try:
        # 验证并格式化股票代码
        if not isinstance(symbol, str):
            raise ValueError("股票代码必须是字符串类型")
            
        # 处理纯数字代码，自动添加交易所后缀
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('600', '601', '603', '605', '688', '689')):
                symbol = f"{symbol}.SH"
            elif symbol.startswith(('000', '001', '002', '003', '300', '301', '430')):
                symbol = f"{symbol}.SZ"
            elif symbol.startswith(('82', '83', '87', '88')):
                symbol = f"{symbol}.BJ"
            elif symbol.startswith('4') or (symbol.startswith('8') and len(symbol) == 6):
                symbol = f"{symbol}.BJ"
            else:
                if symbol.startswith('8') and len(symbol) == 6:
                    symbol = f"{symbol}.BJ"
                else:
                    raise ValueError(f"无法识别的股票代码：{symbol}\n支持的代码类型：\n1. 上海主板：600/601/603/605\n2. 上海科创板：688/689\n3. 深圳主板：000/001\n4. 深圳创业板：300/301\n5. 中小板：002/003\n6. 新三板：430/4开头/8开头\n7. 北交所：82/83/87/88")
        elif len(symbol.split('.')) != 2:
            raise ValueError(f"股票代码格式错误：{symbol}\n正确格式示例：\n1. 直接输入6位数字代码：000001\n2. 带交易所后缀：000001.SZ")
        
        # 设置日期范围
        if start_date is not None:
            try:
                pd.to_datetime(start_date, format='%Y%m%d')
            except ValueError:
                try:
                    pd.to_datetime(start_date, format='%Y-%m-%d')
                except ValueError:
                    raise ValueError(f"起始日期格式错误，支持的格式：YYYYMMDD或YYYY-MM-DD")
        
        if end_date is not None:
            try:
                pd.to_datetime(end_date, format='%Y%m%d')
            except ValueError:
                try:
                    pd.to_datetime(end_date, format='%Y-%m-%d')
                except ValueError:
                    raise ValueError(f"结束日期格式错误，支持的格式：YYYYMMDD或YYYY-MM-DD")
        
        if start_date is not None and end_date is not None:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            if start_dt > end_dt:
                raise ValueError("起始日期不能晚于结束日期")
            if end_dt > datetime.now():
                end_date = datetime.now().strftime('%Y%m%d')
                logger.warning(f"结束日期超过今天，已自动调整为今天: {end_date}")
        
        # 调用原始方法获取数据
        # 在这里我们假设继续调用原始实现的剩余部分
        # 注意：在实际应用中，这里应该保留原始函数的核心数据获取逻辑
        original_get_stock_data = self.__class__.__bases__[0].get_stock_data.__func__
        df = original_get_stock_data(self, symbol, start_date, end_date, limit)
        
        # 验证返回的数据
        if df is None or df.empty:
            raise ValueError(f"未能获取到{symbol}的交易数据")
            
        return df
        
    except Exception as e:
        logger.error(f"获取股票{symbol}数据时出错: {str(e)}")
        if any(keyword in str(e) for keyword in ["格式错误", "无法识别", "不能晚于"]):
            raise  # 重新抛出格式验证错误，让调用者处理
        return None  # 对于其他错误，返回None

def fixed_get_stock_name(self, symbol):
    """
    修复了的获取股票名称方法，优化了缓存机制
    
    修复问题:
    1. 改进缓存检查逻辑
    2. 更好的错误处理
    3. 确保返回的名称有效
    
    参数:
        symbol (str): 股票代码，如"000001.SZ"
        
    返回:
        str: 股票名称
    """
    try:
        # 如果已经缓存，直接返回
        if hasattr(self, '_stock_names_cache') and symbol in self._stock_names_cache:
            timestamp, name = self._stock_names_cache[symbol]
            # 使用标准的缓存过期检查
            if datetime.now().timestamp() - timestamp < 86400:  # 24小时有效期
                return name
            
        # 参数验证
        if not isinstance(symbol, str) or len(symbol) < 6:
            return symbol
            
        # 获取股票代码部分
        stock_code = symbol.split('.')[0] if '.' in symbol else symbol[:6]
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 注意：这里我们假设继续调用akshare或原始实现
                # 在实际应用中，应该保留原始的API调用代码
                import akshare as ak
                stock_info = ak.stock_individual_info_em(symbol=stock_code)
                
                if stock_info is not None and not stock_info.empty and '名称' in stock_info.columns:
                    name = stock_info.iloc[0]['名称']
                    # 确保缓存属性存在
                    if not hasattr(self, '_stock_names_cache'):
                        self._stock_names_cache = {}
                    # 更新缓存
                    self._stock_names_cache[symbol] = (datetime.now().timestamp(), name)
                    return name
                    
                break
            except Exception as e:
                logger.warning(f"获取股票名称失败 (尝试 {retry_count+1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    import time
                    time.sleep(1)  # 暂停1秒再重试
                
        # 如果无法获取名称，返回原始代码
        return symbol
                
    except Exception as e:
        logger.error(f"获取股票{symbol}名称时发生错误：{str(e)}")
        return symbol  # 出错时返回原始代码

def fixed_get_kpl_concept(self, trade_date: str = '', use_cache: bool = True, cache_expire_seconds: int = 3600*24) -> pd.DataFrame:
    """
    增强版获取开盘啦概念题材列表，包括缓存支持和更好的错误处理
    
    Args:
        trade_date: 交易日期（YYYYMMDD格式）
        use_cache: 是否使用缓存
        cache_expire_seconds: 缓存过期时间（秒）
        
    Returns:
        DataFrame: 包含概念题材列表数据
    """
    # 参数验证
    if trade_date and not re.match(r'^\d{8}$', trade_date):
        self.logger.warning(f"交易日期格式不正确: {trade_date}，应为YYYYMMDD格式")
        return pd.DataFrame()
    
    # 缓存键生成
    cache_key = f"kpl_concept_{trade_date}" if trade_date else "kpl_concept_latest"
    
    # 检查缓存
    if use_cache and cache_key in self.memory_cache:
        cache_data, cache_time = self.memory_cache[cache_key]
        if (time.time() - cache_time) < cache_expire_seconds:
            self.logger.debug(f"使用缓存数据: {cache_key}")
            return cache_data.copy()
    
    # 失败重试逻辑
    retry_intervals = [0.5, 1.0, 2.0]
    last_exception = None
    
    for retry_idx, retry_interval in enumerate(retry_intervals):
        try:
            # 调用原始方法
            df = self.get_kpl_concept(trade_date=trade_date)
            
            # 验证数据
            if df is None or df.empty:
                if retry_idx < len(retry_intervals) - 1:
                    self.logger.warning(f"获取开盘啦概念题材列表返回空数据，尝试重试 ({retry_idx+1}/{len(retry_intervals)})")
                    time.sleep(retry_interval)
                    continue
                self.logger.warning(f"获取开盘啦概念题材列表返回空数据")
                return pd.DataFrame()
            
            # 数据清洗和标准化
            if not all(col in df.columns for col in ['ts_code', 'name', 'in_date']):
                self.logger.warning(f"获取开盘啦概念题材列表数据缺少必要列")
                return df
            
            # 添加数据获取时间戳
            df['data_timestamp'] = pd.Timestamp.now()
            
            # 缓存有效数据
            if use_cache:
                self.memory_cache[cache_key] = (df.copy(), time.time())
                self.logger.debug(f"缓存数据: {cache_key}")
            
            return df
            
        except Exception as e:
            last_exception = e
            if retry_idx < len(retry_intervals) - 1:
                self.logger.warning(f"获取开盘啦概念题材列表失败，尝试重试 ({retry_idx+1}/{len(retry_intervals)}): {str(e)}")
                time.sleep(retry_interval)
            else:
                self.logger.error(f"获取开盘啦概念题材列表失败，已尝试 {len(retry_intervals)} 次: {str(e)}")
    
    # 所有重试都失败
    if last_exception:
        self.logger.error(f"获取开盘啦概念题材列表失败: {str(last_exception)}")
    
    return pd.DataFrame()

def fixed_get_kpl_concept_cons(self, ts_code: str = '', trade_date: str = '', con_code: str = '', use_cache: bool = True, cache_expire_seconds: int = 3600*24) -> pd.DataFrame:
    """
    增强版获取开盘啦概念题材成分股，包括缓存支持和更好的错误处理
    
    Args:
        ts_code: 题材代码（xxxxxx.KP格式）
        trade_date: 交易日期（YYYYMMDD格式）
        con_code: 成分代码（xxxxxx.SH格式）
        use_cache: 是否使用缓存
        cache_expire_seconds: 缓存过期时间（秒）
        
    Returns:
        DataFrame: 包含概念题材成分股数据
    """
    # 参数验证
    if ts_code and not re.match(r'^\d{6}\.[A-Z]{2}$', ts_code):
        self.logger.warning(f"题材代码格式不正确: {ts_code}，应为xxxxxx.KP格式")
        return pd.DataFrame()
        
    if trade_date and not re.match(r'^\d{8}$', trade_date):
        self.logger.warning(f"交易日期格式不正确: {trade_date}，应为YYYYMMDD格式")
        return pd.DataFrame()
        
    if con_code and not re.match(r'^\d{6}\.[A-Z]{2}$', con_code):
        self.logger.warning(f"成分代码格式不正确: {con_code}，应为xxxxxx.SH格式")
        return pd.DataFrame()
    
    # 缓存键生成
    cache_parts = []
    if ts_code:
        cache_parts.append(f"ts_{ts_code}")
    if trade_date:
        cache_parts.append(f"date_{trade_date}")
    if con_code:
        cache_parts.append(f"con_{con_code}")
    
    cache_key = f"kpl_concept_cons_{'_'.join(cache_parts)}" if cache_parts else "kpl_concept_cons_all"
    
    # 检查缓存
    if use_cache and cache_key in self.memory_cache:
        cache_data, cache_time = self.memory_cache[cache_key]
        if (time.time() - cache_time) < cache_expire_seconds:
            self.logger.debug(f"使用缓存数据: {cache_key}")
            return cache_data.copy()
    
    # 失败重试逻辑
    retry_intervals = [0.5, 1.0, 2.0]
    last_exception = None
    
    for retry_idx, retry_interval in enumerate(retry_intervals):
        try:
            # 调用原始方法
            df = self.get_kpl_concept_cons(ts_code=ts_code, trade_date=trade_date, con_code=con_code)
            
            # 验证数据
            if df is None or df.empty:
                if retry_idx < len(retry_intervals) - 1:
                    self.logger.warning(f"获取开盘啦概念题材成分股返回空数据，尝试重试 ({retry_idx+1}/{len(retry_intervals)})")
                    time.sleep(retry_interval)
                    continue
                self.logger.warning(f"获取开盘啦概念题材成分股返回空数据")
                return pd.DataFrame()
            
            # 数据清洗和标准化
            required_columns = ['ts_code', 'con_code', 'con_name', 'in_date']
            if not all(col in df.columns for col in required_columns):
                self.logger.warning(f"获取开盘啦概念题材成分股数据缺少必要列")
                return df
            
            # 添加数据获取时间戳
            df['data_timestamp'] = pd.Timestamp.now()
            
            # 缓存有效数据
            if use_cache:
                self.memory_cache[cache_key] = (df.copy(), time.time())
                self.logger.debug(f"缓存数据: {cache_key}")
            
            return df
            
        except Exception as e:
            last_exception = e
            if retry_idx < len(retry_intervals) - 1:
                self.logger.warning(f"获取开盘啦概念题材成分股失败，尝试重试 ({retry_idx+1}/{len(retry_intervals)}): {str(e)}")
                time.sleep(retry_interval)
            else:
                self.logger.error(f"获取开盘啦概念题材成分股失败，已尝试 {len(retry_intervals)} 次: {str(e)}")
    
    # 所有重试都失败
    if last_exception:
        self.logger.error(f"获取开盘啦概念题材成分股失败: {str(last_exception)}")
    
    return pd.DataFrame()

def fixed_get_kpl_list(self, ts_code: str = '', trade_date: str = '', tag: str = '', start_date: str = '', end_date: str = '', use_cache: bool = True, cache_expire_seconds: int = 3600*24) -> pd.DataFrame:
    """
    增强版获取开盘啦榜单数据，包括缓存支持和更好的错误处理
    
    Args:
        ts_code: 股票代码（xxxxxx.SH/SZ格式）
        trade_date: 交易日期（YYYYMMDD格式）
        tag: 板单类型（涨停/炸板/跌停/自然涨停/竞价)
        start_date: 开始日期（YYYYMMDD格式）
        end_date: 结束日期（YYYYMMDD格式）
        use_cache: 是否使用缓存
        cache_expire_seconds: 缓存过期时间（秒）
        
    Returns:
        DataFrame: 包含榜单数据
    """
    # 参数验证
    if ts_code and not re.match(r'^\d{6}\.[A-Z]{2}$', ts_code):
        self.logger.warning(f"股票代码格式不正确: {ts_code}，应为xxxxxx.SH/SZ格式")
        return pd.DataFrame()
        
    for date_param, date_name in [(trade_date, "交易日期"), (start_date, "开始日期"), (end_date, "结束日期")]:
        if date_param and not re.match(r'^\d{8}$', date_param):
            self.logger.warning(f"{date_name}格式不正确: {date_param}，应为YYYYMMDD格式")
            return pd.DataFrame()
    
    # 缓存键生成
    cache_parts = []
    if ts_code:
        cache_parts.append(f"ts_{ts_code}")
    if trade_date:
        cache_parts.append(f"date_{trade_date}")
    if tag:
        cache_parts.append(f"tag_{tag}")
    if start_date:
        cache_parts.append(f"start_{start_date}")
    if end_date:
        cache_parts.append(f"end_{end_date}")
    
    cache_key = f"kpl_list_{'_'.join(cache_parts)}" if cache_parts else "kpl_list_all"
    
    # 检查缓存
    if use_cache and cache_key in self.memory_cache:
        cache_data, cache_time = self.memory_cache[cache_key]
        if (time.time() - cache_time) < cache_expire_seconds:
            self.logger.debug(f"使用缓存数据: {cache_key}")
            return cache_data.copy()
    
    # 失败重试逻辑
    retry_intervals = [0.5, 1.0, 2.0]
    last_exception = None
    
    for retry_idx, retry_interval in enumerate(retry_intervals):
        try:
            # 调用原始方法
            df = self.get_kpl_list(ts_code=ts_code, trade_date=trade_date, tag=tag, 
                                   start_date=start_date, end_date=end_date)
            
            # 验证数据
            if df is None or df.empty:
                if retry_idx < len(retry_intervals) - 1:
                    self.logger.warning(f"获取开盘啦榜单数据返回空数据，尝试重试 ({retry_idx+1}/{len(retry_intervals)})")
                    time.sleep(retry_interval)
                    continue
                self.logger.warning(f"获取开盘啦榜单数据返回空数据")
                return pd.DataFrame()
            
            # 数据清洗和标准化
            required_columns = ['ts_code', 'trade_date', 'name']
            if not all(col in df.columns for col in required_columns):
                self.logger.warning(f"获取开盘啦榜单数据缺少必要列")
                return df
            
            # 添加数据获取时间戳
            df['data_timestamp'] = pd.Timestamp.now()
            
            # 缓存有效数据
            if use_cache:
                self.memory_cache[cache_key] = (df.copy(), time.time())
                self.logger.debug(f"缓存数据: {cache_key}")
            
            return df
            
        except Exception as e:
            last_exception = e
            if retry_idx < len(retry_intervals) - 1:
                self.logger.warning(f"获取开盘啦榜单数据失败，尝试重试 ({retry_idx+1}/{len(retry_intervals)}): {str(e)}")
                time.sleep(retry_interval)
            else:
                self.logger.error(f"获取开盘啦榜单数据失败，已尝试 {len(retry_intervals)} 次: {str(e)}")
    
    # 所有重试都失败
    if last_exception:
        self.logger.error(f"获取开盘啦榜单数据失败: {str(last_exception)}")
    
    return pd.DataFrame()

def apply_fixes(vss):
    """
    将所有的修复应用到VisualStockSystem实例
    
    Args:
        vss: VisualStockSystem实例
    """
    # 现有的修复...
    vss.analyze_momentum = types.MethodType(fixed_analyze_momentum, vss)
    vss.get_stock_data = types.MethodType(fixed_get_stock_data, vss)
    vss.get_stock_name = types.MethodType(fixed_get_stock_name, vss)
    
    # 新增的修复
    vss.get_kpl_concept = types.MethodType(fixed_get_kpl_concept, vss)
    vss.get_kpl_concept_cons = types.MethodType(fixed_get_kpl_concept_cons, vss)
    vss.get_kpl_list = types.MethodType(fixed_get_kpl_list, vss)
    
    return vss