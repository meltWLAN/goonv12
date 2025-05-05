import pandas as pd
import numpy as np
import talib as ta
import akshare as ak
import pytz
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from tqdm import tqdm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jf_trading_system import JFTradingSystem, MarketSignal
import time
import os
import logging
import tushare as ts
from china_stock_provider import ChinaStockProvider
import re
import traceback


# Fix Chinese font display
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTextEdit

class VisualStockSystem(QMainWindow):
    def __init__(self, token=None, headless=False, cache_dir: str = './data_cache', log_level: str = 'INFO', data_source: str = 'tushare'):
        self.token = token  # 正确保存传入的token参数
        self.headless = headless  # 无头模式标志
        
        # 只有在非无头模式下才初始化GUI
        if not headless:
            super().__init__()
            self.initUI()
        else:
            self._init_non_gui()

        # 设置日志
        self.logger = logging.getLogger('VisualStockSystem')
        self.logger.setLevel(getattr(logging, log_level))
        
        # 缓存设置
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
        self.cache = {}
        self.cache_timeout = 3600  # 缓存过期时间(秒)
        
        # API设置
        self.api_cooldown = 0.5  # API调用间隔(秒)
        self.last_api_call = 0  # 上次API调用时间
        
        # 东方财富API (默认)
        self.stock_api = None
        
        # Tushare API设置
        self.tushare_token = token or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.tushare_pro = None
        
        # 初始化数据提供者
        self.data_provider = ChinaStockProvider(api_token=self.tushare_token)
        
        # 设置数据源
        self.set_data_source(data_source)
        
        # 线程相关初始化
        import threading
        self._cache_lock = threading.Lock()
        self.threading = threading
        from concurrent.futures import ThreadPoolExecutor
        import os
        self._thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count() * 2 or 8)
        
        self.logger.info(f"VisualStockSystem初始化完成，数据源: {data_source}")

    def _init_non_gui(self):
        """初始化非GUI模式的必要组件"""
        # 初始化无头模式下需要的组件
        self.china_tz = pytz.timezone('Asia/Shanghai')
        self.jf_system = JFTradingSystem()
        self._stock_names_cache = {}
        self._stock_data_cache = {}
        self._market_data_cache = {}
        self._last_api_call = 0
        self._min_api_interval = 0.15
        self._cache_expiry = 7200
        import threading
        self._cache_lock = threading.Lock()
        self.threading = threading
        from concurrent.futures import ThreadPoolExecutor
        import os
        self._thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count() * 2 or 8)

    def initUI(self):
        """初始化用户界面组件"""
        # 创建中央部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.setWindowTitle('可视化股票分析系统')
        self.setGeometry(100, 100, 1200, 800)
        
        # 添加日志输出区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

    def get_stock_data(self, symbol, start_date=None, end_date=None, limit=None):
        """获取股票历史数据
        使用统一数据提供者获取A股历史数据
        """
        try:
            # 兼容 limit 参数但不实际使用，避免因多余参数报错
            _ = limit
            
            # 设置日期范围
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
                
            # 格式化日期
            try:
                try:
                    start_dt = datetime.strptime(start_date, '%Y%m%d')
                except ValueError:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        start_date = start_dt.strftime('%Y%m%d')
                    except ValueError as e:
                        raise ValueError(f"起始日期格式错误：{str(e)}，支持的格式：YYYYMMDD或YYYY-MM-DD")
                try:
                    end_dt = datetime.strptime(end_date, '%Y%m%d')
                except ValueError:
                    try:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        end_date = end_dt.strftime('%Y%m%d')
                    except ValueError as e:
                        raise ValueError(f"结束日期格式错误：{str(e)}，支持的格式：YYYYMMDD或YYYY-MM-DD")
                if start_dt > end_dt:
                    raise ValueError("起始日期不能晚于结束日期")
                if end_dt > datetime.now():
                    end_date = datetime.now().strftime('%Y%m%d')
            except ValueError as e:
                raise ValueError(str(e))
                
            # 使用统一数据提供者获取数据
            df = self.data_provider.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            # 如果数据为空，抛出异常
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                raise ValueError(f"未能获取到{symbol}的交易数据")
                
            # 重命名列以兼容现有代码
            rename_map = {
                'date': 'trade_date'
            }
            df = df.rename(columns=rename_map)
            
            # 确保返回的类型与原函数一致
            if 'trade_date' in df.columns and 'date' not in df.columns:
                try:
                    df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
                except:
                    # 已经是标准格式，忽略错误
                    pass
                
            # 类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
                    if df[col].isnull().any():
                        if col == 'volume':
                            # 使用明确的布尔操作，避免DataFrame真值歧义
                            vol_mean = df[col].mean()
                            df.loc[df[col].isnull(), col] = vol_mean
                        else:
                            # 正确使用前向和后向填充替代旧方法
                            df[col] = df[col].ffill().bfill()
                    df[col] = df[col].astype('float64')
                    
            # 验证必须列是否存在
            required_columns = ['trade_date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.warning(f"数据缺少关键列: {missing_columns}，尝试补全")
                for col in missing_columns:
                    if col == 'trade_date':
                        # 如果缺少交易日期列，使用索引创建
                        df['trade_date'] = pd.date_range(start=start_dt, periods=len(df)).strftime('%Y%m%d')
                    else:
                        # 对于价格数据，如果缺少则使用已有列估算
                        if col == 'close' and 'open' in df.columns:
                            df[col] = df['open']
                        elif col in ['open', 'high', 'low'] and 'close' in df.columns:
                            df[col] = df['close']
                        elif col == 'volume':
                            df['volume'] = 0  # 如果没有成交量，则设为0
                
            # 验证数据点数量是否足够
            if len(df) < 20:
                self.logger.warning(f"{symbol}数据点不足(仅{len(df)}条)，技术分析可能不准确")
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票数据失败: {str(e)}")
            # 创建一个空的DataFrame并添加必要的列
            empty_df = pd.DataFrame(columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
            # 添加一些基本数据，避免后续分析出错
            today = datetime.now().strftime('%Y%m%d')
            empty_df.loc[0] = [today, 0.0, 0.0, 0.0, 0.0, 0]
            return empty_df
            
    def get_stock_name(self, symbol):
        """获取股票中文名称"""
        try:
            # 尝试使用数据提供者获取股票信息
            stock_info = self.data_provider.get_stock_info(symbol=symbol)
            
            if stock_info is not None and not stock_info.empty:
                # 根据数据源不同，处理返回结果
                if 'name' in stock_info.columns:
                    return stock_info.iloc[0]['name']
                elif '名称' in stock_info.columns:
                    return stock_info.iloc[0]['名称']
                else:
                    # 尝试获取任何可能的名称列
                    for col in stock_info.columns:
                        if any(name_key in col.lower() for name_key in ['name', '名称', '股票名称']):
                            return stock_info.iloc[0][col]
            
            # 如果上面的方法都失败，尝试旧方法
            return self._legacy_get_stock_name(symbol)
            
        except Exception as e:
            self.logger.warning(f"获取股票{symbol}名称时发生错误：{str(e)}")
            return symbol
            
    def _legacy_get_stock_name(self, symbol):
        """旧版获取股票名称方法(备用)"""
        try:
            # 如果已经缓存，直接返回
            # 带时间戳的缓存检查
            if hasattr(self, '_stock_names_cache') and symbol in self._stock_names_cache:
                timestamp, name = self._stock_names_cache[symbol]
                if time.time() - timestamp < 86400:  # 24小时有效期
                    return name
                del self._stock_names_cache[symbol]
            
            # 添加请求间隔控制
            time.sleep(0.3)  # 300ms间隔
            
            # 从akshare获取股票基本信息
            stock_code = symbol[:6]  # 直接取前6位数字作为股票代码
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    stock_info = ak.stock_individual_info_em(symbol=stock_code)
                    if not stock_info.empty:
                        name = stock_info.iloc[0]['名称']
                        if not hasattr(self, '_stock_names_cache'):
                            self._stock_names_cache = {}
                        self._stock_names_cache[symbol] = (time.time(), name)
                        return name
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(1)  # 失败后等待1秒再重试
                    else:
                        self.logger.warning(f"从akshare获取股票{symbol}信息失败：{str(e)}")
            return symbol
            
        except Exception as e:
            self.logger.warning(f"获取股票{symbol}名称时发生错误：{str(e)}")
            return symbol

    def analyze_momentum(self, df):
        """动量分析
        计算EMA21、MACD等动量指标
        
        参数:
            df (pd.DataFrame): 包含股票数据的DataFrame
        
        返回:
            pd.DataFrame: 添加了动量指标的DataFrame
        """
        if df is None:
            return None
            
        # 确定收盘价所在列
        close_column = None
        potential_columns = ['close', 'Close', 'close_price', 'CLOSE']
        
        for col in potential_columns:
            if col in df.columns:
                close_column = col
                break
                
        if close_column is None:
            try:
                if len(df.columns) > 0:
                    if 'close' in df.columns[3].lower():
                        close_column = df.columns[3]
                    else:
                        return None
                else:
                    print("数据中没有列")
                    return None
            except Exception as e:
                print(f"查找收盘价列时出错: {str(e)}")
                if len(df.columns) >= 4:
                    close_column = df.columns[3]  # 假设第4列是收盘价
                else:
                    return None
            
        try:
            # 创建数据副本避免修改原始数据
            df = df.copy()
            
            # 确保没有缺失值会影响技术指标计算
            if df[close_column].isnull().any():
                df[close_column] = df[close_column].fillna(method='ffill').fillna(method='bfill')
                
            # 根据数据点数量使用不同的计算方法
            data_length = len(df)
            
            # 当数据量充足时使用talib计算准确指标
            if data_length >= 30:
                try:
                    # 预分配空列，避免NaN值警告
                    df['EMA21'] = np.zeros(len(df))
                    df['MACD'] = np.zeros(len(df))
                    df['MACD_Signal'] = np.zeros(len(df))
                    df['MACD_Hist'] = np.zeros(len(df))
                    
                    # 使用有效的数据点计算
                    valid_values = df[close_column].values
                    
                    # 标准计算方法
                    ema21 = ta.EMA(valid_values, timeperiod=21)
                    macd, signal, hist = ta.MACD(valid_values)
                    
                    # 仅在计算完成后一次性赋值，避免多次生成NaN警告
                    if ema21 is not None:
                        # 填充NaN，消除警告信息
                        ema21 = np.nan_to_num(ema21, nan=0.0)
                        df['EMA21'] = ema21
                    
                    if macd is not None and signal is not None and hist is not None:
                        # 填充NaN，消除警告信息
                        macd = np.nan_to_num(macd, nan=0.0)
                        signal = np.nan_to_num(signal, nan=0.0)
                        hist = np.nan_to_num(hist, nan=0.0)
                        
                        # 赋值指标
                        df['MACD'] = macd
                        df['MACD_Signal'] = signal
                        df['MACD_Hist'] = hist
                
                except Exception as e:
                    print(f"使用talib计算指标失败: {str(e)}，使用替代方法")
                    self._calculate_simplified_indicators(df, close_column)
            else:
                # 数据量不足，使用简化的计算方法
                self._calculate_simplified_indicators(df, close_column)
            
            # 最终数据有效性检查 - 不输出警告，而是静默修复
            for indicator in ['EMA21', 'MACD', 'MACD_Signal', 'MACD_Hist']:
                if indicator not in df.columns:
                    self._create_fallback_indicator(df, indicator, close_column)
                elif df[indicator].isnull().any():
                    # 静默填充，不打印警告
                    df[indicator] = df[indicator].ffill().bfill().fillna(0.0)
        
        except Exception as e:
            print(f"计算动量指标时出错: {str(e)}")
            # 如果出错，创建所有需要的指标列
            self._create_all_fallback_indicators(df, close_column)
        
        return df
        
    def _calculate_simplified_indicators(self, df, close_column):
        """使用简化方法计算技术指标"""
        try:
            # 简化的EMA计算 - 使用较小的窗口和最小周期
            window_size = min(21, len(df) - 1)
            min_periods = max(1, min(window_size // 2, len(df) - 1))
            
            # 预分配，避免生成警告
            df['EMA21'] = np.zeros(len(df))
            df['MACD'] = np.zeros(len(df))
            df['MACD_Signal'] = np.zeros(len(df))
            df['MACD_Hist'] = np.zeros(len(df))
            
            # 先计算，再一次性赋值
            ema_values = df[close_column].ewm(span=window_size, min_periods=min_periods).mean().values
            df['EMA21'] = np.nan_to_num(ema_values, nan=0.0)
            
            # 简化的MACD计算
            if len(df) >= 9:
                # 尽可能使用标准参数但降低最小周期要求
                fast_window = min(12, len(df) - 1)
                slow_window = min(26, len(df) - 1)
                signal_window = min(9, len(df) - 1)
                
                # 临时计算，不保存中间结果
                macd_fast = df[close_column].ewm(span=fast_window, min_periods=min_periods).mean()
                macd_slow = df[close_column].ewm(span=slow_window, min_periods=min_periods).mean()
                macd_values = macd_fast - macd_slow
                signal_values = macd_values.ewm(span=signal_window, min_periods=min_periods).mean()
                hist_values = macd_values - signal_values
                
                # 一次性赋值，避免多次警告
                df['MACD'] = np.nan_to_num(macd_values.values, nan=0.0)
                df['MACD_Signal'] = np.nan_to_num(signal_values.values, nan=0.0)
                df['MACD_Hist'] = np.nan_to_num(hist_values.values, nan=0.0)
            else:
                # 数据极少，使用最简单的计算
                diff_values = df[close_column].diff(1).values
                df['MACD'] = np.nan_to_num(diff_values, nan=0.0)
                
                signal_values = pd.Series(diff_values).rolling(window=2, min_periods=1).mean().values
                df['MACD_Signal'] = np.nan_to_num(signal_values, nan=0.0)
                
                hist_values = diff_values - signal_values
                df['MACD_Hist'] = np.nan_to_num(hist_values, nan=0.0)
                
        except Exception as e:
            print(f"计算简化指标失败: {str(e)}")
            self._create_all_fallback_indicators(df, close_column)

    def _create_fallback_indicator(self, df, indicator, close_column):
        """为缺失的指标创建替代列"""
        if indicator == 'EMA21':
            df['EMA21'] = df[close_column]
        elif indicator == 'MACD':
            df['MACD'] = 0.0
        elif indicator == 'MACD_Signal':
            df['MACD_Signal'] = 0.0
        elif indicator == 'MACD_Hist':
            df['MACD_Hist'] = 0.0
    def _create_all_fallback_indicators(self, df, close_column):
        """创建所有必要的替代指标"""
        df['EMA21'] = df[close_column]
        df['MACD'] = 0.0
        df['MACD_Signal'] = 0.0
        df['MACD_Hist'] = 0.0
    def analyze_volume_price(self, df):
        """量价分析
        分析成交量与价格的关系，并整合3L理论
        增加更多技术指标和市场分析维度
        """
        if df is None or len(df) < 20:
            return None

        # 创建数据副本避免修改原始数据
        df = df.copy()
            
        # 确保列名标准化（支持大小写）
        column_mapping = {
            'volume': 'Volume', 'close': 'Close', 'open': 'Open', 
            'high': 'High', 'low': 'Low', 'trade_date': 'Date',
            'vol': 'Volume'  # 添加'vol'到'Volume'的映射
        }
        
        # 将小写列名转换为大写列名
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]
                
        # 检查所需的关键列是否存在
        required_columns = ['Volume', 'Close', 'High', 'Low']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"量价分析数据缺少必要列: {missing_columns}")
            return None

        # 检查Volume列是否有有效值
        if 'Volume' in df.columns and (df['Volume'] == 0).all():
            # 如果Volume列全为0，但有vol列，则使用vol列
            if 'vol' in df.columns and (df['vol'] != 0).any():
                df['Volume'] = df['vol']
            else:
                # 创建虚拟成交量数据进行分析
                self.logger.warning("成交量数据无效，使用模拟数据进行分析")
                mean_price = df['Close'].mean()
                df['Volume'] = np.random.normal(1000000, 200000, len(df)) * (df['Close'] / mean_price)

                try:
            # 确保日期索引
        if 'Date' in df.columns:
            df.set_index('Date', inplace=True)
        df.index = pd.to_datetime(df.index)

            # 初始化指标数据，防止NaN警告
            indicator_columns = [
                'Volume_MA20', 'Volume_MA5', 'Volume_Ratio', 'Price_Change', 'Volume_Change',
                'ATR', 'Volatility', 'PEV', 'PEV_MA20', 'BB_Middle', 'BB_Upper', 'BB_Lower',
                'CCI', 'DI_Plus', 'DI_Minus', 'ADX', 'MFI', 'Trend_Strength',
                'Future_High', 'Future_Low', 'Trend_Confidence', 'Liquidity_Score', 
                'Liquidity_MA10', 'Price_MA20', 'Price_MA60', 'Level_Position',
                'Upper_Line', 'Lower_Line', 'Channel_Width', 'Volume_Price_Score'
            ]
            
            for col in indicator_columns:
                df[col] = np.zeros(len(df))
    
            # 计算均量指标 - 处理NaN
            df['Volume_MA20'] = df['Volume'].rolling(window=20, min_periods=1).mean().fillna(df['Volume'])
            df['Volume_MA5'] = df['Volume'].rolling(window=5, min_periods=1).mean().fillna(df['Volume'])
            df['Volume_Ratio'] = (df['Volume'] / df['Volume_MA20']).fillna(1.0)
        
        # 计算价格和成交量变化
            df['Price_Change'] = df['Close'].pct_change().fillna(0)
            df['Volume_Change'] = df['Volume'].pct_change().fillna(0)
        
        # 计算ATR和波动率
            atr_values = ta.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
            df['ATR'] = np.nan_to_num(atr_values, nan=df['Close'].std() * 0.1)
            
            # 确保ATR不为零，因为它将用作分母
            df.loc[df['ATR'] == 0, 'ATR'] = df['Close'] * 0.02
            
            # 安全计算波动率 - 使用向量化操作
            df['Volatility'] = (df['ATR'] / df['Close'] * 100).fillna(5.0)  # 默认5%波动率

        # 计算政策量能指标
        df['PEV'] = df['Volume'] * df['Price_Change'].abs()
            df['PEV_MA20'] = df['PEV'].rolling(window=20, min_periods=1).mean().fillna(df['PEV'])
        
        # 计算布林带
            sma_values = ta.SMA(df['Close'].values, timeperiod=20)
            df['BB_Middle'] = np.nan_to_num(sma_values, nan=df['Close'])
            std_20 = df['Close'].rolling(window=20, min_periods=1).std().fillna(df['Close'] * 0.02)
            df['BB_Upper'] = df['BB_Middle'] + 2 * std_20
            df['BB_Lower'] = df['BB_Middle'] - 2 * std_20
        
        # 计算CCI指标
            cci_values = ta.CCI(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
            df['CCI'] = np.nan_to_num(cci_values, nan=0.0)
        
        # 计算DMI指标
            di_plus = ta.PLUS_DI(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
            di_minus = ta.MINUS_DI(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
            adx = ta.ADX(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
            
            df['DI_Plus'] = np.nan_to_num(di_plus, nan=20.0)
            df['DI_Minus'] = np.nan_to_num(di_minus, nan=20.0)
            df['ADX'] = np.nan_to_num(adx, nan=15.0)
        
        # 计算资金流向指标
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
            mfi_values = ta.MFI(df['High'].values, df['Low'].values, df['Close'].values, df['Volume'].values, timeperiod=14)
            df['MFI'] = np.nan_to_num(mfi_values, nan=50.0)
        
        # 计算趋势强度
            trend_values = ta.LINEARREG_SLOPE(df['Close'].values, timeperiod=14)
            df['Trend_Strength'] = np.nan_to_num(trend_values, nan=0.0)
        
        # 计算未来价格区间
        df['Future_High'] = df['Close'] + df['ATR'] * 2
        df['Future_Low'] = df['Close'] - df['ATR'] * 2
        
            # 安全计算趋势可信度，避免NaN
            vol_adjusted = df['Volatility'].clip(upper=100)  # 限制最大波动率为100%
        df['Trend_Confidence'] = (df['Volume_Ratio'] * (1 + abs(df['Price_Change'])) * 
                                    (1 - vol_adjusted/100)).clip(0, 1)
        
        # 3L理论分析
        # 1. Liquidity（流动性）
        df['Liquidity_Score'] = df['Volume_Ratio'] * (1 + abs(df['Price_Change']))
            df['Liquidity_MA10'] = df['Liquidity_Score'].rolling(window=20, min_periods=1).mean().fillna(df['Liquidity_Score'])
        
        # 2. Level（价格水平）
            df['Price_MA20'] = df['Close'].rolling(window=20, min_periods=1).mean().fillna(df['Close'])
            df['Price_MA60'] = df['Close'].rolling(window=60, min_periods=1).mean().fillna(df['Close'])
            
            # 安全计算价格水平位置
        df['Level_Position'] = (df['Close'] - df['Price_MA60']) / (df['ATR'] * 2)
        
            # 3. Line（趋势线）- 再次计算趋势强度，确保有值
            trend_values = ta.LINEARREG_SLOPE(df['Close'].values, timeperiod=20)
            df['Trend_Strength'] = np.nan_to_num(trend_values, nan=0.0)
            
            # 计算支撑位和阻力位
            upper_line = df['High'].rolling(window=20, min_periods=1).max().fillna(df['High'])
            lower_line = df['Low'].rolling(window=20, min_periods=1).min().fillna(df['Low'])
            
            # 赋值并确保无NaN
            df['Upper_Line'] = upper_line
            df['Lower_Line'] = lower_line
            
            # 确保支撑位小于阻力位 - 使用元素级别的比较和赋值
            df_max = df[['Upper_Line', 'Lower_Line']].max(axis=1)
            df_min = df[['Upper_Line', 'Lower_Line']].min(axis=1)
            df['Upper_Line'] = df_max
            df['Lower_Line'] = df_min
            
            # 安全计算通道宽度 - 避免除以零
            # 创建一个安全的除数，确保不为零
            close_for_division = df['Close'].copy()
            close_for_division.loc[close_for_division == 0] = 1.0  # 替换零值
            df['Channel_Width'] = (df['Upper_Line'] - df['Lower_Line']) / close_for_division * 100
            
            # 计算综合得分 - 安全处理可能的无穷大值
            df['Volume_Price_Score'] = (
                df['Liquidity_Score'] * 
                (1 + df['Level_Position'].abs().clip(0, 10)) * 
                (1 + df['Trend_Strength'].abs().clip(0, 2))
            ).clip(0, 100)  # 限制最大值
            
            # 预测未来趋势 - 使用向量化操作而不是条件逻辑
            if len(df) > 0:
                # 获取最新值，避免使用索引[-1]可能引起歧义
                last_idx = len(df) - 1
                last_close = df['Close'].iloc[last_idx]
                last_atr = df['ATR'].iloc[last_idx]
                last_trend_strength = df['Trend_Strength'].iloc[last_idx]
                last_volume_ratio = df['Volume_Ratio'].iloc[last_idx]
                
                # 安全计算趋势因子，避免负数和无穷大
                safe_volume_ratio = max(0.1, last_volume_ratio)  # 避免log(0)或log(负数)
                trend_factor = last_trend_strength * (1 + np.log(safe_volume_ratio))
                
                # 更新最新记录的未来价格区间
                future_high = last_close + (last_atr * 2 * abs(trend_factor))
                future_low = last_close - (last_atr * abs(trend_factor))
                df.loc[df.index[last_idx], 'Future_High'] = future_high
                df.loc[df.index[last_idx], 'Future_Low'] = future_low
        
        # 计算趋势可信度
                liquidity_ma5 = df['Liquidity_Score'].rolling(window=5, min_periods=1).mean().fillna(df['Liquidity_Score'])
                channel_width_safe = df['Channel_Width'].clip(0, 200)  # 限制最大通道宽度
                
                trend_confidence = (
                    liquidity_ma5 *
                    (1 + abs(df['Trend_Strength']).clip(0, 2)) *
                    (1 - channel_width_safe / 200)  # 通道越窄，可信度越高
        ).clip(0, 1)
                df['Trend_Confidence'] = trend_confidence
            
            # 最终检查和清理 - 处理任何剩余的NaN值
            for col in df.columns:
                if df[col].isnull().any():
                    df[col] = df[col].ffill().bfill().fillna(0)
        
        return df
            
        except Exception as e:
            print(f"量价分析计算出错: {str(e)}")
            return None

    def check_trend(self, df):
        """趋势判断
        基于EMA21和MACD判断趋势
        """
        if df is None or len(df) < 21:
            return 'unknown'
            
        # 确保关键列存在
        if 'close' in df.columns:
            close_column = 'close'
        elif 'Close' in df.columns:
            close_column = 'Close'
        else:
            print("趋势判断缺少收盘价列")
            return 'unknown'
            
        # 检查是否缺少技术指标列，并尝试计算
        if 'EMA21' not in df.columns or 'MACD_Hist' not in df.columns:
            print("趋势判断缺少技术指标列")
            try:
                # 尝试计算缺少的指标
                if 'EMA21' not in df.columns:
                    df['EMA21'] = ta.EMA(df[close_column].values, timeperiod=21)
                
                if 'MACD_Hist' not in df.columns:
                    macd, signal, hist = ta.MACD(df[close_column].values)
                    df['MACD'] = macd
                    df['MACD_Signal'] = signal
                    df['MACD_Hist'] = hist
            except Exception as e:
                print(f"计算缺少的技术指标时出错: {str(e)}")
                # 如果无法计算指标，则使用简单的价格变化趋势判断
                if len(df) >= 5:
                    price_change = df[close_column].pct_change(5).iloc[-1]
                    if price_change > 0.03:  # 5日涨幅超过3%
                        return 'uptrend'
                    elif price_change < -0.03:  # 5日跌幅超过3%
                        return 'downtrend'
                    else:
                        return 'sideways'
                return 'unknown'

        # 继续执行原有的趋势判断逻辑
        last_close = df[close_column].iloc[-1]
        last_ema21 = df['EMA21'].iloc[-1]
        last_macd = df['MACD_Hist'].iloc[-1]

        if last_close > last_ema21 and last_macd > 0:
            return 'uptrend'
        elif last_close < last_ema21 and last_macd < 0:
            return 'downtrend'
        else:
            return 'sideways'

    def analyze_stock(self, symbol):
        """分析单只股票的技术指标和趋势
        
        Args:
            symbol: 股票代码
            
        Returns:
            (分析结果字典, 处理后的数据DataFrame)
        """
        try:
            # 获取股票数据
            df = self.get_stock_data(symbol)
            
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                return None, None
    
            # 先进行动量分析，计算EMA21和MACD等必要指标
            df = self.analyze_momentum(df)
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                return None, None
    
            # 量价分析
            df = self.analyze_volume_price(df)
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                return None, None
    
            # 趋势判断 (现在放在指标计算后)
            trend = self.check_trend(df)
    
            # 计算最新的技术指标 - 避免使用[-1]索引
            if len(df) > 0:
                latest_idx = len(df) - 1
                latest = df.iloc[latest_idx]
                prev_idx = latest_idx - 1 if latest_idx > 0 else latest_idx
                prev = df.iloc[prev_idx]
            else:
                # 创建空的Series以避免错误
                latest = pd.Series()
                prev = pd.Series()
    
            # 获取简放交易系统的分析结果
            try:
                # 检查jf_system是否存在，若不存在则跳过相关功能
                jf_signal = None
                jf_market_structure = None
                if hasattr(self, 'jf_system'):
                    jf_signal = self.jf_system.generate_trading_signal(df, symbol)
                    jf_market_structure = self.jf_system.analyze_market_structure(df)
            except Exception as e:
                print(f"获取简放交易系统分析结果出错: {str(e)}")
                jf_signal = None
                jf_market_structure = None
    
            # 计算KDJ指标
            try:
                # 确保必要的列存在
                high_col = 'High' if 'High' in df.columns else 'high'
                low_col = 'Low' if 'Low' in df.columns else 'low'
                close_col = 'Close' if 'Close' in df.columns else 'close'
                
                k, d = ta.STOCH(df[high_col].values, df[low_col].values, df[close_col].values,
                              fastk_period=9, slowk_period=3, slowk_matype=0,
                              slowd_period=3, slowd_matype=0)
                k_series = pd.Series(k, index=df.index)
                d_series = pd.Series(d, index=df.index)
                df['K'] = k_series
                df['D'] = d_series
                df['J'] = 3 * df['K'] - 2 * df['D']
                j = df['J']
    
                # 计算RSI
                rsi = ta.RSI(df[close_col].values, timeperiod=14)
                rsi_series = pd.Series(rsi, index=df.index)
                df['RSI'] = rsi_series
                
                # 添加Cycle_Resonance指标计算
                try:
                    # 这里添加周期共振指标的实际计算逻辑
                    # 以下为简单示例，实际计算可能更复杂
                    # 例如使用傅立叶变换或小波分析来检测多个周期的同步性
                    
                    # 简单示例：计算短周期和长周期均线的同步性
                    ma5 = df[close_col].rolling(window=5).mean()
                    ma10 = df[close_col].rolling(window=10).mean()
                    ma20 = df[close_col].rolling(window=20).mean()
                    
                    # 计算方向一致性，使用显式的比较操作
                    ma5_diff = ma5.diff()
                    ma10_diff = ma10.diff()
                    ma20_diff = ma20.diff()
                    
                    ma5_direction = ma5_diff.apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
                    ma10_direction = ma10_diff.apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
                    ma20_direction = ma20_diff.apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
                    
                    # 计算方向一致性比例 - 使用逐元素的布尔运算
                    direction_match = ((ma5_direction == ma10_direction) & 
                                      (ma10_direction == ma20_direction))
                    
                    # 使用滚动窗口计算一致性
                    resonance = direction_match.rolling(window=10).mean()
                    df['Cycle_Resonance'] = resonance
                except Exception as e:
                    # 如果计算失败，设置默认值
                    df['Cycle_Resonance'] = 0.0
                    # print(f"计算Cycle_Resonance指标时出错: {str(e)}")
            except Exception as e:
                print(f"计算KDJ/RSI指标时出错: {str(e)}")
                # 设置默认值
                df['K'] = df['D'] = df['J'] = df['RSI'] = 50.0
                df['Cycle_Resonance'] = 0.0
    
            analysis = {
                'symbol': symbol,
                'name': self.get_stock_name(symbol),
                'trend': trend,
                'close': self.safe_get_value(df, 'Close'),
                'volume': self.safe_get_value(df, 'Volume'),
                'volume_ma20': self.safe_get_value(df, 'Volume_MA20'),
                'macd_hist': self.safe_get_value(df, 'MACD_Hist'),
                'atr': self.safe_get_value(df, 'ATR'),
                'trend_analysis': {
                    'trend': trend,
                    'strength': round(self.safe_get_value(df, 'Trend_Strength') * 100, 2),
                    'rsi_value': round(self.safe_get_value(df, 'RSI'), 2),
                    'explanation': f"趋势强度为{round(self.safe_get_value(df, 'Trend_Strength') * 100, 2)}%，{'趋势较强' if abs(self.safe_get_value(df, 'Trend_Strength')) > 0.1 else '趋势一般'}，{'建议顺势操作' if abs(self.safe_get_value(df, 'Trend_Strength')) > 0.1 else '建议谨慎操作'}"
                },
                'price_info': {
                    'current': round(self.safe_get_value(df, 'Close'), 2),
                    'change': round(self.safe_get_value(df, 'Price_Change') * 100, 2),
                    'explanation': f"最新价格{round(self.safe_get_value(df, 'Close'), 2)}元，相比昨日{'上涨' if self.safe_get_value(df, 'Price_Change') > 0 else '下跌'}{abs(round(self.safe_get_value(df, 'Price_Change') * 100, 2))}%（{'利好' if self.safe_get_value(df, 'Price_Change') > 0 else '利空'}）"
                },
                'volume_analysis': {
                    'status': '活跃' if self.safe_get_value(df, 'Volume') > self.safe_get_value(df, 'Volume_MA20') * 1.5 else '正常' if self.safe_get_value(df, 'Volume') > self.safe_get_value(df, 'Volume_MA20') * 0.5 else '清淡',
                    'ratio': round(self.safe_get_value(df, 'Volume') / max(0.0001, self.safe_get_value(df, 'Volume_MA20')), 2),
                    'explanation': self._get_volume_explanation(df)
                },
                'technical_indicators': {
                    'macd': {
                        'macd': round(self.safe_get_value(df, 'MACD'), 3),
                        'signal': round(self.safe_get_value(df, 'MACD_Signal'), 3),
                        'hist': round(self.safe_get_value(df, 'MACD_Hist'), 3),
                        'explanation': self._get_macd_explanation(df)
                    },
                    'kdj': {
                        'k': round(self.safe_get_value(df, 'K'), 2),
                        'd': round(self.safe_get_value(df, 'D'), 2),
                        'j': round(self.safe_get_value(df, 'J'), 2),
                        'explanation': self._get_kdj_explanation(df)
                    },
                    'rsi': {
                        'value': round(self.safe_get_value(df, 'RSI'), 2),
                        'explanation': self._get_rsi_explanation(df)
                    }
                },
                'market_analysis': {
                    'volatility': round(self.safe_get_value(df, 'Volatility'), 2),
                    'cycle_resonance': round(self.safe_get_value(df, 'Cycle_Resonance'), 3),
                    'explanation': self._get_market_explanation(df)
                },
                'support_resistance': {
                    'support': round(self.safe_get_value(df, 'Lower_Line'), 2) if 'Lower_Line' in df.columns else None,
                    'resistance': round(self.safe_get_value(df, 'Upper_Line'), 2) if 'Upper_Line' in df.columns else None,
                    'explanation': self._get_support_resistance_explanation(df)
                },
                'trading_ranges': {
                    'buy_range': {
                        'low': round(self.safe_get_value(df, 'Close') * 0.95, 2),
                        'high': round(self.safe_get_value(df, 'Close') * 0.98, 2)
                    },
                    'sell_range': {
                        'low': round(self.safe_get_value(df, 'Close') * 1.02, 2),
                        'high': round(self.safe_get_value(df, 'Close') * 1.05, 2)
                    }
                }
            }

            # 生成交易建议
            if jf_signal and hasattr(self, 'jf_system'):
                recommendation = self.jf_system.get_trading_signal(jf_signal)
            else:
                recommendation = self.generate_recommendation(analysis)

            # 添加交易建议的详细解释
            analysis['trading_advice'] = self._get_trading_advice(df, trend)
            
            return analysis, df
            
        except Exception as e:
            print(f"分析股票{symbol}时出错: {str(e)}")
            traceback.print_exc()  # 打印完整的错误追踪
            return None, None
            
    def _get_volume_explanation(self, df):
        """生成成交量分析解释，避免在字符串格式化中嵌入条件逻辑"""
        volume = self.safe_get_value(df, 'Volume')
        volume_ma20 = self.safe_get_value(df, 'Volume_MA20')
        volume_ma20_safe = max(0.0001, volume_ma20)  # 避免除以零
        
        ratio = round(volume / volume_ma20_safe, 2)
        
        if volume > volume_ma20 * 1.5:
            status = "活跃"
            detail = "表明市场交投热络"
        elif volume > volume_ma20 * 0.5:
            status = "正常"
            detail = "表明市场交投正常"
        else:
            status = "清淡"
            detail = "表明市场较为清淡"
            
        return f"成交量{status}，为20日均量的{ratio}倍，{detail}"
        
    def _get_macd_explanation(self, df):
        """生成MACD分析解释"""
        macd_hist = self.safe_get_value(df, 'MACD_Hist')
        
        if macd_hist > 0.1:
            return "MACD信号：金叉形成，上涨趋势确立"
        elif macd_hist < -0.1:
            return "MACD信号：死叉形成，下跌趋势确立"
        else:
            return "MACD信号：趋势模糊，建议观望"
            
    def _get_kdj_explanation(self, df):
        """生成KDJ分析解释"""
        k_value = self.safe_get_value(df, 'K')
        
        if k_value > 80:
            return "KDJ状态：超买，股价可能即将回调"
        elif k_value < 20:
            return "KDJ状态：超卖，股价可能即将反弹"
        else:
            return "KDJ状态：位于中性区域"
            
    def _get_rsi_explanation(self, df):
        """生成RSI分析解释"""
        rsi_value = self.safe_get_value(df, 'RSI')
        
        if rsi_value > 70:
            return "RSI状态：超买，股价可能即将回调"
        elif rsi_value < 30:
            return "RSI状态：超卖，股价可能即将反弹"
        else:
            return "RSI状态：位于中性区域"
            
    def _get_market_explanation(self, df):
        """生成市场分析解释"""
        volatility = self.safe_get_value(df, 'Volatility')
        cycle_resonance = self.safe_get_value(df, 'Cycle_Resonance')
        
        vol_text = "波动剧烈，风险较高" if volatility > 1.5 else "波动正常，风险适中"
        cycle_text = "周期共振，趋势持续较强" if cycle_resonance > 0.7 else "周期发散，趋势可能转折"
        
        return f"市场状态：{vol_text}，{cycle_text}"
        
    def _get_support_resistance_explanation(self, df):
        """生成支撑阻力位分析解释"""
        has_support = 'Lower_Line' in df.columns
        has_resistance = 'Upper_Line' in df.columns
        
        support = round(self.safe_get_value(df, 'Lower_Line'), 2) if has_support else '未知'
        resistance = round(self.safe_get_value(df, 'Upper_Line'), 2) if has_resistance else '未知'
        
        if has_support and has_resistance:
            advice = "建议在支撑位附近买入，阻力位附近卖出"
        else:
            advice = "暂无明确支撑阻力位"
            
        return f"支撑位{support}元，阻力位{resistance}元，{advice}"
        
    def _get_trading_advice(self, df, trend):
        """生成交易建议"""
        volume = self.safe_get_value(df, 'Volume')
        volume_ma20 = self.safe_get_value(df, 'Volume_MA20')
        macd_hist = self.safe_get_value(df, 'MACD_Hist')
        
            if trend == 'uptrend':
            if volume > volume_ma20 * 1.5 and macd_hist > 0:
                return {
                        'action': '建议买入',
                        'explanation': '上升趋势明显，成交量放大，MACD金叉，多重指标共振看多'
                    }
                else:
                return {
                        'action': '谨慎买入',
                        'explanation': '上升趋势形成，但需要观察量能配合，建议分批建仓'
                    }
            elif trend == 'downtrend':
            if volume > volume_ma20 * 1.5 and macd_hist < 0:
                return {
                        'action': '建议卖出',
                        'explanation': '下跌趋势明显，成交量放大，MACD死叉，注意及时止损'
                    }
                else:
                return {
                        'action': '谨慎卖出',
                        'explanation': '下跌趋势形成，但可能存在超跌反弹，建议分批减仓'
                    }
            else:
            return {
                'action': '建议观望',
                'explanation': '横盘整理，等待明确信号出现再行动，可少量高抛低吸'
            }

    def generate_recommendation(self, analysis):
        """生成交易建议"""
        if analysis['trend'] == 'uptrend':
            if analysis['volume_analysis']['ratio'] > 1.5:
                if analysis['technical_indicators']['macd']['hist'] > 0:
                    return '强烈推荐买入'
                else:
                    return '建议买入'
            else:
                return '观望'
        elif analysis['trend'] == 'downtrend':
            return '建议卖出'
        else:
            return '观望'

    def plot_stock_analysis(self, symbol):
        """绘制股票分析图表"""
        try:
            # 获取并验证数据
            analysis, df = self.analyze_stock(symbol)
            if analysis is None or df is None:
                print(f"无法获取股票 {symbol} 的数据或分析结果")
                return None
                
            # 验证数据完整性
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'EMA21', 
                              'MACD', 'MACD_Signal', 'MACD_Hist', 'PEV', 'PEV_MA20']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"数据缺失以下必要列：{', '.join(missing_columns)}")
                return None
                
            # 验证数据类型
            for col in required_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    print(f"列 {col} 的数据类型不正确，应为数值类型")
                    return None
                    
            # 验证数据长度
            if len(df) < 20:
                print(f"数据量不足，至少需要20个交易日的数据")
                return None

            # 创建子图
            fig = make_subplots(rows=6, cols=1,
                               shared_xaxes=True,
                               vertical_spacing=0.02,
                               subplot_titles=(
                                   '<b>价格趋势</b>',
                                   '<b>KDJ指标</b>',
                                   '<b>RSI指标</b>',
                                   '<b>MACD</b>',
                                   '<b>成交量</b>',
                                   '<b>资金流向</b>'
                               ),
                               row_heights=[0.4, 0.15, 0.15, 0.15, 0.15, 0.15])

            # 添加K线图
            fig.add_trace(go.Candlestick(x=df.index,
                                        open=df['Open'],
                                        high=df['High'],
                                        low=df['Low'],
                                        close=df['Close'],
                                        name='K线',
                                        increasing_line_color='#ff4444',
                                        decreasing_line_color='#44ff44'),
                         row=1, col=1)

            # 添加布林带
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['BB_Upper'],
                                    name='布林上轨',
                                    line=dict(color='rgba(173,216,230,0.8)', width=1)),
                         row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['BB_Middle'],
                                    name='布林中轨',
                                    line=dict(color='rgba(173,216,230,0.5)', width=1)),
                         row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['BB_Lower'],
                                    name='布林下轨',
                                    line=dict(color='rgba(173,216,230,0.8)', width=1),
                                    fill='tonexty',
                                    fillcolor='rgba(173,216,230,0.1)'),
                         row=1, col=1)

            # 添加KDJ指标
            k_series = pd.Series(df['K'], index=df.index)
            d_series = pd.Series(df['D'], index=df.index)
            j_series = pd.Series(df['J'], index=df.index)
            
            fig.add_trace(go.Scatter(x=df.index,
                                    y=k_series,
                                    name='K值',
                                    line=dict(color='#ffd700', width=1.5)),
                         row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=d_series,
                                    name='D值',
                                    line=dict(color='#ff69b4', width=1.5)),
                         row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=j_series,
                                    name='J值',
                                    line=dict(color='#00ffff', width=1.5)),
                         row=2, col=1)

            # 添加RSI指标
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['RSI'],
                                    name='RSI',
                                    line=dict(color='#ff4500', width=1.5)),
                         row=3, col=1)

            # 添加MACD
            fig.add_trace(go.Bar(x=df.index,
                                y=df['MACD_Hist'],
                                name='MACD柱状',
                                marker_color='rgba(128,128,128,0.5)',
                                opacity=0.8),
                         row=4, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['MACD'],
                                    name='MACD',
                                    line=dict(color='#4169e1', width=1.5)),
                         row=4, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['MACD_Signal'],
                                    name='Signal',
                                    line=dict(color='#ff6b6b', width=1.5)),
                         row=4, col=1)

            # 添加成交量柱状图
            colors = ['#ff4444' if x >= 0 else '#44ff44' for x in df['Price_Change']]
            fig.add_trace(go.Bar(x=df.index,
                                y=df['Volume'],
                                name='成交量',
                                marker_color=colors,
                                opacity=0.8),
                         row=5, col=1)

            # 添加成交量均线
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['Volume_MA5'],
                                    name='成交量5日均线',
                                    line=dict(color='#ffd700', width=1)),
                         row=5, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['Volume_MA20'],
                                    name='成交量20日均线',
                                    line=dict(color='#ff69b4', width=1)),
                         row=5, col=1)

            # 添加政策量能指标
            fig.add_trace(go.Bar(x=df.index,
                                y=df['PEV'],
                                name='政策量能',
                                marker_color='rgba(55, 128, 191, 0.7)'),
                         row=6, col=1)
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['PEV_MA20'],
                                    name='20日均量能',
                                    line=dict(color='#ffa500', width=1.5)),
                         row=6, col=1)

            # 添加北向资金影响
            flow_impacts = df['Close'].pct_change() * df['Volume'] / df['Volume_MA20']
            fig.add_trace(go.Scatter(
                x=df.index,
                y=flow_impacts,
                name='北向资金影响',
                line=dict(color='rgba(147,112,219,0.8)', width=1.5),
                fill='tozeroy',
                fillcolor='rgba(147,112,219,0.1)'
            ), row=5, col=1)
            
            # 添加EMA21
            fig.add_trace(go.Scatter(x=df.index,
                                    y=df['EMA21'],
                                    name='EMA21',
                                    line=dict(color='#ffa500', width=1.5)),
                         row=1, col=1)

            return fig

        except Exception as e:
            print(f"绘制股票分析图表时发生错误：{str(e)}")
            return None

    def scan_stocks(self, stock_list=None, industry=None):
        """扫描股票列表或指定行业的股票，使用多线程并行处理和缓存机制提高性能"""
        try:
            if industry:
                stock_list = self.get_industry_stocks(industry)

            if not stock_list:
                return []

            def analyze_stock_with_cache(symbol):
                try:
                    # 检查缓存
                    with self._cache_lock:
                        cache_key = f"scan_{symbol}"
                        if cache_key in self.cache:
                            return self.cache[cache_key]

                    # 分析股票
                    analysis, _ = self.analyze_stock(symbol)
                    if analysis:
                        # 更新缓存
                        with self._cache_lock:
                            self.cache[cache_key] = analysis
                        return analysis
                    return None
                except Exception as e:
                    self.logger.error(f"分析股票 {symbol} 时出错：{str(e)}")
                    return None

            # 使用线程池并行处理
            recommendations = []
            futures = [self._thread_pool.submit(analyze_stock_with_cache, symbol) for symbol in stock_list]
            for future in futures:
                result = future.result()
                if result:
                    recommendations.append(result)

            return recommendations
        except Exception as e:
            self.logger.error(f"扫描股票时发生错误：{str(e)}")
            return []
            
    def print_recommendations(self, recommendations):
        """打印股票推荐结果"""
        if not recommendations:
            print("没有符合条件的推荐股票")
            return
            
        print(f"\n找到 {len(recommendations)} 只推荐股票:")
        print("-" * 50)
        
        for idx, stock in enumerate(recommendations, 1):
            name = stock.get('name', '未知')
            symbol = stock.get('symbol', '')
            price = stock.get('price', 0)
            trend = stock.get('trend', '未知')
            score = stock.get('total_score', 0)
            
            # 提取推荐理由
            reason = []
            if stock.get('trend') == 'uptrend':
                reason.append("上升趋势")
            if stock.get('volume_ratio', 0) > 1.2:
                reason.append("成交量放大")
            if stock.get('macd_hist', 0) > 0:
                reason.append("MACD金叉")
            if stock.get('ma5', 0) > stock.get('ma10', 0):
                reason.append("均线多头排列")
                
            if not reason:
                reason.append("综合技术指标较好")
            
            # 格式化打印
            print(f"{idx}. {name}({symbol}) - {price:.2f}元")
            print(f"   趋势: {trend}, 评分: {score:.2f}")
            print(f"   推荐理由: {', '.join(reason)}")
            print("-" * 50)

    def set_data_source(self, source_name: str) -> bool:
        """设置数据源
        
        Args:
            source_name: 数据源名称 ('akshare' 或 'tushare')
            
        Returns:
            是否设置成功
        """
        # 使用数据提供者设置数据源
        if self.data_provider.set_data_source(source_name):
            self.logger.info(f"已切换数据源为: {source_name}")
            return True
        return False
        
    def ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            self.logger.info(f"创建缓存目录: {self.cache_dir}")

    def get_realtime_data(self, ts_code: str) -> Dict:
        """获取股票实时行情数据
        
        Args:
            ts_code: 股票代码，如'000001.SZ'或'600000.SH'
            
        Returns:
            包含实时行情数据的字典
        """
        try:
            # 标准化股票代码格式
            if '.' not in ts_code and len(ts_code) == 6:
                if ts_code.startswith(('600', '601', '603', '605', '688')):
                    ts_code = f"{ts_code}.SH"
                elif ts_code.startswith(('000', '001', '002', '003', '300', '301')):
                    ts_code = f"{ts_code}.SZ"
                elif ts_code.startswith(('4', '8')):
                    ts_code = f"{ts_code}.BJ"
            
            self.logger.info(f"获取股票{ts_code}实时行情")
            
            # 1. 获取实时日K线数据
            df_daily = self.data_provider.get_realtime_daily(ts_code=ts_code)
            
            # 2. 获取实时分钟K线数据 (最近30分钟)
            df_min = self.data_provider.get_realtime_minute(ts_code=ts_code, freq='1MIN')
            if not df_min.empty:
                df_min = df_min.head(30)  # 只取最近30分钟数据
            
            # 3. 获取实时成交明细
            df_tick = self.data_provider.get_tick_data(ts_code=ts_code)
            if not df_tick.empty:
                df_tick = df_tick.head(50)  # 只取最近50笔成交
            
            # 4. 获取实时行情快照(盘口)
            df_quote = self.data_provider.get_realtime_quotes(ts_code=ts_code)
            
            # 5. 获取股票名称
            stock_name = self.get_stock_name(ts_code)
            
            # 构建结果字典
            result = {
                'ts_code': ts_code,
                'name': stock_name,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'daily_data': df_daily.to_dict('records')[0] if not df_daily.empty else {},
                'minute_data': df_min.to_dict('records') if not df_min.empty else [],
                'tick_data': df_tick.to_dict('records') if not df_tick.empty else [],
                'quote_data': df_quote.to_dict('records')[0] if not df_quote.empty else {}
            }
            
            # 计算一些附加指标
            if not df_min.empty and len(df_min) > 5:
                # 计算最近5分钟涨跌
                latest_price = df_min.iloc[0]['close'] if 'close' in df_min.columns else None
                five_min_ago = df_min.iloc[4]['close'] if len(df_min) > 4 and 'close' in df_min.columns else None
                
                if latest_price is not None and five_min_ago is not None:
                    result['price_change_5min'] = round((latest_price - five_min_ago) / five_min_ago * 100, 2)
                    
                # 计算分钟波动率
                if 'high' in df_min.columns and 'low' in df_min.columns:
                    highs = df_min['high'].values
                    lows = df_min['low'].values
                    if len(highs) > 0 and len(lows) > 0:
                        minute_ranges = [(high - low) / low * 100 for high, low in zip(highs, lows)]
                        result['volatility_minute'] = round(sum(minute_ranges) / len(minute_ranges), 2)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取实时行情数据出错: {str(e)}")
            return {'error': str(e), 'ts_code': ts_code}
    
    def get_market_realtime_snapshot(self, market: str = None) -> Dict:
        """获取市场实时快照
        
        Args:
            market: 市场类型，SH-上海，SZ-深圳，BJ-北京，None-全部
            
        Returns:
            市场实时概览数据
        """
        try:
            # 根据市场类型构建代码模式
            if market == 'SH':
                code_pattern = '6*.SH'
            elif market == 'SZ':
                code_pattern = '0*.SZ,3*.SZ'
            elif market == 'BJ':
                code_pattern = '8*.BJ,4*.BJ'
            else:
                code_pattern = '6*.SH,0*.SZ,3*.SZ,8*.BJ,4*.BJ'
                
            self.logger.info(f"获取市场实时概览: {market if market else '全市场'}")
            
            # 获取实时行情数据
            df = self.data_provider.get_realtime_daily(ts_code=code_pattern)
            
            if df.empty:
                return {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'market': market if market else '全市场',
                    'error': '未获取到行情数据'
                }
                
            # 计算市场统计指标
            total_stocks = len(df)
            up_stocks = len(df[df['close'] > df['pre_close']])
            down_stocks = len(df[df['close'] < df['pre_close']])
            flat_stocks = total_stocks - up_stocks - down_stocks
            
            # 计算涨跌幅分布
            df['change_pct'] = (df['close'] - df['pre_close']) / df['pre_close'] * 100
            
            limit_up_stocks = len(df[df['change_pct'] >= 9.5])
            limit_down_stocks = len(df[df['change_pct'] <= -9.5])
            
            # 涨跌幅分布统计
            pct_dist = {
                'limit_up': limit_up_stocks,
                'above_5pct': len(df[(df['change_pct'] >= 5) & (df['change_pct'] < 9.5)]),
                'between_0_5pct': len(df[(df['change_pct'] > 0) & (df['change_pct'] < 5)]),
                'flat': flat_stocks,
                'between_0_5pct_down': len(df[(df['change_pct'] < 0) & (df['change_pct'] > -5)]),
                'below_5pct': len(df[(df['change_pct'] <= -5) & (df['change_pct'] > -9.5)]),
                'limit_down': limit_down_stocks
            }
            
            # 计算成交额
            total_amount = df['amount'].sum() if 'amount' in df.columns else 0
            
            # 获取涨幅前10和跌幅前10
            top_up = df.sort_values('change_pct', ascending=False).head(10)
            top_down = df.sort_values('change_pct', ascending=True).head(10)
            
            # 构建结果
            result = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'market': market if market else '全市场',
                'total_stocks': total_stocks,
                'up_stocks': up_stocks,
                'down_stocks': down_stocks,
                'flat_stocks': flat_stocks,
                'up_down_ratio': round(up_stocks / down_stocks, 2) if down_stocks > 0 else float('inf'),
                'advance_decline_ratio': round(up_stocks / total_stocks * 100, 2) if total_stocks > 0 else 0,
                'pct_distribution': pct_dist,
                'total_amount': total_amount,
                'average_amount': round(total_amount / total_stocks, 2) if total_stocks > 0 else 0,
                'top_up': top_up[['ts_code', 'name', 'close', 'change_pct']].to_dict('records') if not top_up.empty else [],
                'top_down': top_down[['ts_code', 'name', 'close', 'change_pct']].to_dict('records') if not top_down.empty else []
            }
            
            # 计算市场情绪指数 (0-100)
            # 计算方法：涨跌股比例 * 40% + 涨跌幅分布 * 40% + 成交额变化 * 20%
            sentiment = (up_stocks / total_stocks * 100) * 0.4 if total_stocks > 0 else 50
            limit_impact = ((limit_up_stocks - limit_down_stocks) / total_stocks * 100) * 0.4 if total_stocks > 0 else 0
            
            result['market_sentiment'] = round(min(max(sentiment + limit_impact + 50, 0), 100), 1)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取市场实时概览出错: {str(e)}")
            return {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'market': market if market else '全市场',
                'error': str(e)
            }
            
    def get_industry_list(self):
        """获取行业列表"""
        try:
            # 使用akshare获取行业分类数据
            industry_df = ak.stock_board_industry_name_em()
            return industry_df['板块名称'].tolist()
        except Exception as e:
            print(f"获取行业列表时发生错误：{str(e)}")
            return []
            
    def get_industry_stocks(self, industry_name):
        """获取指定行业的股票列表"""
        try:
            # 使用akshare获取行业成分股
            stocks_df = ak.stock_board_industry_cons_em(symbol=industry_name)
            return stocks_df['代码'].tolist()
        except Exception as e:
            print(f"获取行业股票列表时发生错误：{str(e)}")
            return []

    # ========== 研究数据API方法 ==========
    
    def get_research_data(self, data_type: str, ts_code: str = '', **kwargs) -> pd.DataFrame:
        """获取研究数据
        
        Args:
            data_type: 数据类型
                'earnings_forecast' - 盈利预测数据
                'chip_distribution' - 筹码分布数据
                'chip_performance' - 筹码胜率数据
                'technical_factors' - 技术面因子
                'auction_data' - 集合竞价数据
                'nine_turn' - 神奇九转指标
                'institutional_research' - 机构调研
                'broker_recommendations' - 券商推荐
                'hk_holdings' - 沪深港股通持股
                'ccass_holdings' - 中央结算系统持股
                'market_concepts' - 市场概念题材
            ts_code: 股票代码
            **kwargs: 其他参数，如日期等
                
        Returns:
            DataFrame 包含相应研究数据
        """
        try:
            if not self.data_provider:
                self.logger.error("数据提供者未初始化")
                return pd.DataFrame()
            
            self.logger.info(f"获取研究数据: 类型={data_type}, 股票={ts_code}")
            
            # 根据数据类型调用相应方法
            if data_type == 'earnings_forecast':
                return self.data_provider.get_earnings_forecast(ts_code=ts_code, **kwargs)
            
            elif data_type == 'chip_distribution':
                return self.data_provider.get_chip_distribution(ts_code=ts_code, **kwargs)
            
            elif data_type == 'chip_performance':
                return self.data_provider.get_chip_performance(ts_code=ts_code, **kwargs)
            
            elif data_type == 'technical_factors':
                return self.data_provider.get_technical_factors(ts_code=ts_code, **kwargs)
            
            elif data_type == 'auction_data':
                return self.data_provider.get_auction_data(ts_code=ts_code, **kwargs)
            
            elif data_type == 'nine_turn':
                return self.data_provider.get_nine_turn_indicator(ts_code=ts_code, **kwargs)
            
            elif data_type == 'institutional_research':
                return self.data_provider.get_institutional_research(ts_code=ts_code, **kwargs)
            
            elif data_type == 'broker_recommendations':
                month = kwargs.get('month', datetime.now().strftime('%Y%m'))
                return self.data_provider.get_broker_recommendations(month=month)
            
            elif data_type == 'hk_holdings':
                return self.data_provider.get_hk_holdings(ts_code=ts_code, **kwargs)
            
            elif data_type == 'ccass_holdings':
                return self.data_provider.get_ccass_holdings(ts_code=ts_code, **kwargs)
            
            elif data_type == 'market_concepts':
                return self.data_provider.get_market_concepts(**kwargs)
            
            else:
                self.logger.error(f"不支持的数据类型: {data_type}")
                return pd.DataFrame()
        
        except Exception as e:
            self.logger.error(f"获取研究数据失败[{data_type}]: {str(e)}")
            return pd.DataFrame()
    
    def analyze_earnings_estimates(self, ts_code: str, latest_n: int = 5) -> Dict:
        """分析最新的盈利预测数据
        
        Args:
            ts_code: 股票代码
            latest_n: 获取最近n条预测记录
            
        Returns:
            分析结果字典
        """
        try:
            self.logger.info(f"分析盈利预测数据: {ts_code}")
            
            # 获取最近一个月的预测数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.get_research_data('earnings_forecast', ts_code=ts_code, 
                                        start_date=start_date, end_date=end_date)
            
            if df.empty:
                self.logger.warning(f"未找到盈利预测数据: {ts_code}")
                return {'success': False, 'message': '未找到近期盈利预测数据'}
            
            # 按报告日期排序
            df = df.sort_values('report_date', ascending=False)
            
            # 取最新的n条记录
            recent_forecasts = df.head(latest_n)
            
            # 处理可能的NaN值
            recent_forecasts = recent_forecasts.fillna({
                'eps': 0, 'pe': 0, 'op_rt': 0, 'np': 0
            })
            
            # 计算平均预测值
            avg_eps = recent_forecasts['eps'].mean()
            avg_pe = recent_forecasts['pe'].mean()
            
            # 获取当前股价
            stock_data = self.get_stock_data(ts_code)
            current_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0
            
            # 计算隐含价值
            implied_value = avg_eps * avg_pe if avg_eps and avg_pe else 0
            
            # 计算安全边际
            margin_of_safety = (implied_value - current_price) / current_price * 100 if current_price else 0
            
            # 预测机构分析
            orgs = recent_forecasts['org_name'].unique()
            
            # 整理评级信息
            ratings = recent_forecasts['rating'].value_counts().to_dict()
            
            result = {
                'success': True,
                'ts_code': ts_code,
                'name': recent_forecasts['name'].iloc[0] if 'name' in recent_forecasts.columns else '',
                'forecast_count': len(recent_forecasts),
                'org_count': len(orgs),
                'orgs': orgs.tolist(),
                'avg_eps': avg_eps,
                'avg_pe': avg_pe,
                'current_price': current_price,
                'implied_value': implied_value,
                'margin_of_safety': margin_of_safety,
                'ratings': ratings,
                'forecasts': recent_forecasts[['report_date', 'org_name', 'eps', 'pe', 'rating']].to_dict('records')
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析盈利预测数据失败[{ts_code}]: {str(e)}")
            return {'success': False, 'message': f'分析失败: {str(e)}'}
    
    def analyze_chip_distribution(self, ts_code: str) -> Dict:
        """分析筹码分布数据
        
        Args:
            ts_code: 股票代码
            
        Returns:
            分析结果字典
        """
        try:
            self.logger.info(f"分析筹码分布数据: {ts_code}")
            
            # 获取筹码分布数据
            trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')  # 默认昨天
            
            chip_data = self.get_research_data('chip_distribution', ts_code=ts_code, trade_date=trade_date)
            if chip_data.empty:
                # 尝试前一天
                trade_date = (datetime.now() - timedelta(days=2)).strftime('%Y%m%d')
                chip_data = self.get_research_data('chip_distribution', ts_code=ts_code, trade_date=trade_date)
            
            # 获取筹码胜率数据
            perf_data = self.get_research_data('chip_performance', ts_code=ts_code, trade_date=trade_date)
            
            if chip_data.empty or perf_data.empty:
                self.logger.warning(f"未找到筹码分布数据: {ts_code}")
                return {'success': False, 'message': '未找到筹码分布数据'}
            
            # 获取当前股价
            stock_data = self.get_stock_data(ts_code)
            current_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0
            
            # 计算套牢比例 (计算价格高于当前价格的筹码占比总和)
            trapped_ratio = chip_data[chip_data['price'] > current_price]['percent'].sum()
            profitable_ratio = chip_data[chip_data['price'] <= current_price]['percent'].sum()
            
            # 获取最新的筹码胜率情况
            latest_perf = perf_data.iloc[0]
            
            # 计算当前价格在成本分布中的位置
            price_position = 0
            if current_price >= latest_perf['cost_95pct']:
                price_position = 95
            elif current_price >= latest_perf['cost_85pct']:
                price_position = 85 + (current_price - latest_perf['cost_85pct']) / (latest_perf['cost_95pct'] - latest_perf['cost_85pct']) * 10
            elif current_price >= latest_perf['cost_50pct']:
                price_position = 50 + (current_price - latest_perf['cost_50pct']) / (latest_perf['cost_85pct'] - latest_perf['cost_50pct']) * 35
            elif current_price >= latest_perf['cost_15pct']:
                price_position = 15 + (current_price - latest_perf['cost_15pct']) / (latest_perf['cost_50pct'] - latest_perf['cost_15pct']) * 35
            elif current_price >= latest_perf['cost_5pct']:
                price_position = 5 + (current_price - latest_perf['cost_5pct']) / (latest_perf['cost_15pct'] - latest_perf['cost_5pct']) * 10
            else:
                price_position = 5 * current_price / latest_perf['cost_5pct']
            
            # 分析结果
            result = {
                'success': True,
                'ts_code': ts_code,
                'trade_date': trade_date,
                'current_price': current_price,
                'winner_rate': latest_perf['winner_rate'],
                'trapped_ratio': trapped_ratio,
                'profitable_ratio': profitable_ratio,
                'price_position': price_position,
                'weight_avg': latest_perf['weight_avg'],
                'cost_5pct': latest_perf['cost_5pct'],
                'cost_15pct': latest_perf['cost_15pct'],
                'cost_50pct': latest_perf['cost_50pct'],
                'cost_85pct': latest_perf['cost_85pct'],
                'cost_95pct': latest_perf['cost_95pct'],
                'distribution': chip_data[['price', 'percent']].to_dict('records')
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析筹码分布数据失败[{ts_code}]: {str(e)}")
            return {'success': False, 'message': f'分析失败: {str(e)}'}
    
    def get_broker_monthly_picks(self, month: str = '') -> Dict:
        """获取券商月度金股推荐
        
        Args:
            month: 月度，格式为'YYYYMM'，如'202206'，默认当月
            
        Returns:
            券商金股推荐分析结果
        """
        try:
            if not month:
                month = datetime.now().strftime('%Y%m')
            
            self.logger.info(f"获取券商月度金股推荐: {month}")
            
            # 获取券商金股推荐数据
            df = self.get_research_data('broker_recommendations', month=month)
            
            if df.empty:
                self.logger.warning(f"未找到券商月度金股推荐: {month}")
                return {'success': False, 'message': '未找到券商月度金股推荐数据'}
            
            # 统计推荐次数
            stock_counts = df['ts_code'].value_counts().reset_index()
            stock_counts.columns = ['ts_code', 'recommend_count']
            
            # 获取股票名称
            stocks_with_name = df[['ts_code', 'name']].drop_duplicates().reset_index(drop=True)
            
            # 合并推荐次数和股票名称
            result_df = pd.merge(stock_counts, stocks_with_name, on='ts_code')
            
            # 排序
            result_df = result_df.sort_values('recommend_count', ascending=False).reset_index(drop=True)
            
            # 统计券商数量
            broker_count = df['broker'].nunique()
            
            # 统计TOP推荐券商
            broker_counts = df['broker'].value_counts().reset_index()
            broker_counts.columns = ['broker', 'recommend_count']
            top_brokers = broker_counts.head(5).to_dict('records')
            
            # 组装返回结果
            result = {
                'success': True,
                'month': month,
                'total_stocks': len(result_df),
                'total_brokers': broker_count,
                'top_recommended': result_df.head(20).to_dict('records'),
                'top_brokers': top_brokers,
                'all_recommendations': df.to_dict('records')
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取券商月度金股推荐失败[{month}]: {str(e)}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}

    def get_kpl_concept(self, trade_date: str = '') -> pd.DataFrame:
        """
        获取开盘啦概念题材列表
        
        Args:
            trade_date: 交易日期（YYYYMMDD格式）
            
        Returns:
            DataFrame: 包含概念题材列表数据
        """
        try:
            if not self.tushare_token:
                self.logger.error("Tushare token未设置，无法获取开盘啦概念题材列表")
                return pd.DataFrame()
                
            self.logger.info(f"获取开盘啦概念题材列表，日期: {trade_date}")
            
            # 确保tushare pro api已初始化
            if self.data_provider and hasattr(self.data_provider, 'tushare_pro') and self.data_provider.tushare_pro:
                pro = self.data_provider.tushare_pro
            else:
                import tushare as ts
                ts.set_token(self.tushare_token)
                pro = ts.pro_api()
            
            # 构建API参数
            params = {}
            if trade_date:
                params['trade_date'] = trade_date
                    
            # 调用API
            df = pro.kpl_concept(**params)
            
            if df.empty:
                self.logger.warning(f"未找到开盘啦概念题材列表数据")
                return df
                
            return df
                
        except Exception as e:
            self.logger.error(f"获取开盘啦概念题材列表失败: {str(e)}")
            return pd.DataFrame()

    def get_kpl_concept_cons(self, ts_code: str = '', trade_date: str = '', con_code: str = '') -> pd.DataFrame:
        """
        获取开盘啦概念题材的成分股
        
        Args:
            ts_code: 题材代码（xxxxxx.KP格式）
            trade_date: 交易日期（YYYYMMDD格式）
            con_code: 成分代码（xxxxxx.SH格式）
            
        Returns:
            DataFrame: 包含概念题材成分股数据
        """
        try:
            if not self.tushare_token:
                self.logger.error("Tushare token未设置，无法获取开盘啦概念题材成分股")
                return pd.DataFrame()
                
            self.logger.info(f"获取开盘啦概念题材成分股，题材代码: {ts_code}, 日期: {trade_date}")
            
            # 确保tushare pro api已初始化
            if self.data_provider and hasattr(self.data_provider, 'tushare_pro') and self.data_provider.tushare_pro:
                pro = self.data_provider.tushare_pro
            else:
                import tushare as ts
                ts.set_token(self.tushare_token)
                pro = ts.pro_api()
            
            # 构建API参数
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if con_code:
                params['con_code'] = con_code
                    
            # 调用API
            df = pro.kpl_concept_cons(**params)
            
            if df.empty:
                self.logger.warning(f"未找到开盘啦概念题材成分股数据")
                return df
                
            return df
                
        except Exception as e:
            self.logger.error(f"获取开盘啦概念题材成分股失败: {str(e)}")
            return pd.DataFrame()

    def get_kpl_list(self, ts_code: str = '', trade_date: str = '', tag: str = '', start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """
        获取开盘啦榜单数据，包括涨停、跌停、炸板等
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期（YYYYMMDD格式）
            tag: 板单类型（涨停/炸板/跌停/自然涨停/竞价)
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            
        Returns:
            DataFrame: 包含榜单数据
        """
        try:
            if not self.tushare_token:
                self.logger.error("Tushare token未设置，无法获取开盘啦榜单数据")
                return pd.DataFrame()
                
            self.logger.info(f"获取开盘啦榜单数据，日期: {trade_date}, 标签: {tag}")
            
            # 确保tushare pro api已初始化
            if self.data_provider and hasattr(self.data_provider, 'tushare_pro') and self.data_provider.tushare_pro:
                pro = self.data_provider.tushare_pro
            else:
                import tushare as ts
                ts.set_token(self.tushare_token)
                pro = ts.pro_api()
            
            # 构建API参数
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if tag:
                params['tag'] = tag
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                    
            # 调用API
            df = pro.kpl_list(**params)
            
            if df.empty:
                self.logger.warning(f"未找到开盘啦榜单数据")
                return df
                
            return df
                
        except Exception as e:
            self.logger.error(f"获取开盘啦榜单数据失败: {str(e)}")
            return pd.DataFrame()

    def safe_get_value(self, dataframe, column_name, default_value=0.0):
        """安全获取DataFrame中的值，处理列不存在的情况
        
        Args:
            dataframe: 数据表
            column_name: 列名
            default_value: 默认值
            
        Returns:
            列的值或默认值
        """
        # 对某些特定列使用静默处理
        silence_warnings = ['Cycle_Resonance']
        
        # 尝试不同的列名变体
        variants = [column_name, column_name.lower(), column_name.upper()]
        for variant in variants:
            if variant in dataframe.columns:
                value = dataframe[variant].iloc[-1]
                return float(value) if pd.notna(value) else default_value
                
        # 只有在不是静默列的情况下才打印警告
        if column_name not in silence_warnings:
            print(f"警告：找不到列 {column_name}，使用默认值 {default_value}")
        return default_value

def main():
    # Tushare token
    token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    
    # 命令行参数解析
    import argparse
    parser = argparse.ArgumentParser(description='可视化股票系统')
    parser.add_argument('--mode', type=str, default='interactive',
                        choices=['interactive', 'realtime', 'market'],
                        help='运行模式: interactive-交互分析, realtime-实时行情, market-市场概览')
    parser.add_argument('--code', type=str, default='000001.SZ',
                        help='股票代码，用于realtime模式')
    parser.add_argument('--market', type=str, default=None, 
                        choices=[None, 'SH', 'SZ', 'BJ'],
                        help='市场类型，用于market模式')
    args = parser.parse_args()
    
    # 创建可视化股票系统实例
    system = VisualStockSystem(token)
    
    # 根据运行模式执行相应功能
    if args.mode == 'realtime':
        # 实时行情模式
        import json
        result = system.get_realtime_data(args.code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.mode == 'market':
        # 市场概览模式
        import json
        result = system.get_market_realtime_snapshot(args.market)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 默认交互式分析模式
        system.analyze_input_stock()

if __name__ == '__main__':
    main()