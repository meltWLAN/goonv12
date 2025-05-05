import pandas as pd
import numpy as np
import talib as ta
import time
from typing import Dict
from minimal_visual_stock_system import VisualStockSystem
from jf_trading_system import JFTradingSystem
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import threading

class SingleStockAnalyzer:
    def __init__(self, token=None):
        # 导入必要的模块
        import os
        import time
        import logging
        
        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('SingleStockAnalyzer')
        
        # 初始化可视化系统
        self.visual_system = VisualStockSystem(token, headless=True)
        self.token = token
        
        self.jf_system = JFTradingSystem()
        import akshare as ak
        self.ak = ak
        self._last_api_call = 0
        self._min_api_interval = 0.12  # 进一步降低API调用间隔到120ms以提高性能
        
        # 优化缓存系统
        self._cache = {}
        self._cache_expiry = 7200  # 缓存过期时间2小时
        self._cache_lock = threading.Lock()
        
        # 增加线程池大小以提高并行处理能力
        cpu_count = os.cpu_count() or 4
        self._thread_pool = ThreadPoolExecutor(max_workers=cpu_count * 2)
        
        # 分析结果缓存
        self._analysis_cache = {}
        self._analysis_cache_expiry = 3600  # 分析结果缓存1小时
        
        # 添加性能监控
        self._performance_metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'analysis_time': []
        }
        
        self.logger.info("SingleStockAnalyzer初始化完成，线程池大小: %d", cpu_count * 2)
        
    def _wait_for_api_limit(self):
        """等待API访问间隔，使用自适应延迟"""
        current_time = time.time()
        elapsed = current_time - self._last_api_call
        
        # 自适应延迟：根据API调用频率动态调整等待时间
        if self._performance_metrics['api_calls'] > 100:
            # 如果API调用次数较多，适当增加间隔以避免被限流
            wait_time = max(self._min_api_interval, self._min_api_interval * 1.2)
        else:
            wait_time = self._min_api_interval
            
        if elapsed < wait_time:
            time.sleep(wait_time - elapsed)
            
        self._last_api_call = time.time()
        self._performance_metrics['api_calls'] += 1
        
    @lru_cache(maxsize=128)
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称，优先使用缓存"""
        try:
            # 使用visual_system的批量获取方法
            result = self.visual_system.get_stock_names_batch([stock_code])
            return result.get(stock_code, stock_code)
        except Exception as e:
            self.logger.warning(f'批量获取股票名称失败: {str(e)}')
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stock_info = self.ak.stock_individual_info_em(symbol=stock_code)
                if not stock_info.empty:
                    name = stock_info.iloc[0]['名称']
                    # 更新缓存
                    with self._cache_lock:
                        self._cache[stock_code] = (time.time(), name)
                    return name
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
        return stock_code
            
    def analyze_financial_metrics(self, stock_code: str) -> dict:
        """分析财务指标（扣非净利润增长率、市值）
        
        Args:
            stock_code: 股票代码（支持带交易所后缀格式）
        """
        cache_key = f'financial_{stock_code}'
        
        # 检查缓存有效性
        with self._cache_lock:
            if cache_key in self._cache and time.time() - self._cache[cache_key]['timestamp'] < self._cache_expiry:
                return self._cache[cache_key]['data']

        try:
            # 获取最新财务数据
            fin_data = self.ak.stock_financial_analysis_indicator(symbol=stock_code)
            market_data = self.ak.stock_individual_info_em(symbol=stock_code)
            
            # 计算扣非净利润同比增长（使用最近两个报告期数据）
            net_profit = fin_data['扣除非经常性损益后的净利润'].iloc[-2:]
            if len(net_profit) >= 2 and net_profit.iloc[-2] != 0:
                growth_rate = (net_profit.iloc[-1] - net_profit.iloc[-2]) / abs(net_profit.iloc[-2]) * 100
            else:
                growth_rate = 0.0
            
            # 获取总市值（单位：亿元）
            market_cap = market_data['总市值'].iloc[-1] if not market_data.empty else 0.0
            
            result = {
                'net_profit_growth': round(growth_rate, 2),
                'market_cap': round(market_cap / 1e8, 2)  # 转换为亿元单位
            }
            
            # 更新缓存
            with self._cache_lock:
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
            return result
            
        except Exception as e:
            self.logger.error(f"财务分析失败[{stock_code}]: {str(e)}", exc_info=True)
            return {'net_profit_growth': 0.0, 'market_cap': 0.0}
    
    def _update_stock_name(self, analysis_result: Dict, symbol: str) -> Dict:
        """更新分析结果中的股票名称
        使用akshare获取股票中文名称并更新到分析结果中
        """
        try:
            if analysis_result['status'] != 'success':
                return analysis_result
                
            # 从股票代码中提取纯数字部分
            stock_code = symbol.split('.')[0] if '.' in symbol else symbol
            
            # 尝试获取股票名称
            max_retries = 3
            retry_count = 0
            stock_name = symbol
            
            while retry_count < max_retries:
                try:
                    # 使用缓存的方法获取股票名称
                    stock_name = self._get_stock_name(stock_code)
                    if stock_name != stock_code:
                        break
                        
                    # 如果缓存方法失败，尝试直接获取
                    stock_info = self.ak.stock_individual_info_em(symbol=stock_code)
                    if not stock_info.empty and '名称' in stock_info.columns:
                        stock_name = stock_info.iloc[0]['名称']
                        break
                except Exception as e:
                    self.logger.warning(f"获取股票{symbol}名称失败: {str(e)}")
                    
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(0.5)  # 失败后等待0.5秒再重试
            
            # 更新分析结果中的股票名称
            if 'data' in analysis_result and stock_name != symbol:
                analysis_result['data']['name'] = stock_name
                
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"更新股票{symbol}名称时发生错误: {str(e)}")
            return analysis_result
    
    def _parallel_technical_analysis(self, df: pd.DataFrame) -> tuple:
        """并行执行技术分析，提高处理速度"""
        start_time = time.time()
        
        # 使用缓存键避免重复计算
        cache_key = hash(tuple(df['Close'].tail(50).values.tolist()) + 
                         tuple(df['Volume'].tail(50).values.tolist()))
        
        with self._cache_lock:
            if cache_key in self._cache and time.time() - self._cache[cache_key]['timestamp'] < self._cache_expiry:
                self._performance_metrics['cache_hits'] += 1
                return self._cache[cache_key]['result']
            self._performance_metrics['cache_misses'] += 1
        
        futures = []
        try:
            with self._thread_pool as executor:
                futures.append(executor.submit(self._analyze_trend, df))
                futures.append(executor.submit(self._analyze_volume_price, df))
                futures.append(executor.submit(self.jf_system.analyze_volatility_expansion, df))
                futures.append(executor.submit(self.jf_system.check_multi_cycle_resonance, df))
            
            # 收集结果并处理可能的异常
            results = []
            for future in futures:
                try:
                    results.append(future.result())
                except Exception as e:
                    self.logger.error(f"并行分析任务失败: {str(e)}")
                    # 提供默认值以确保程序继续运行
                    if len(results) == 0:
                        results.append({'trend': '震荡整理', 'strength': 50.0, 'rsi_value': 50.0})
                    elif len(results) == 1:
                        results.append({'volume_trend': '平稳', 'volume_ratio': 1.0, 'volume_price_correlation': 0.0})
                    elif len(results) == 2:
                        results.append(1.0)  # 默认波动率
                    elif len(results) == 3:
                        results.append(0.0)  # 默认周期共振
            
            # 确保结果完整
            while len(results) < 4:
                if len(results) == 0:
                    results.append({'trend': '震荡整理', 'strength': 50.0, 'rsi_value': 50.0})
                elif len(results) == 1:
                    results.append({'volume_trend': '平稳', 'volume_ratio': 1.0, 'volume_price_correlation': 0.0})
                elif len(results) == 2:
                    results.append(1.0)  # 默认波动率
                elif len(results) == 3:
                    results.append(0.0)  # 默认周期共振
            
            result_tuple = tuple(results)
            
            # 缓存结果
            with self._cache_lock:
                self._cache[cache_key] = {
                    'result': result_tuple,
                    'timestamp': time.time()
                }
            
            # 记录性能指标
            analysis_time = time.time() - start_time
            self._performance_metrics['analysis_time'].append(analysis_time)
            if len(self._performance_metrics['analysis_time']) > 100:
                self._performance_metrics['analysis_time'] = self._performance_metrics['analysis_time'][-100:]
            
            return result_tuple
            
        except Exception as e:
            self.logger.error(f"并行技术分析失败: {str(e)}")
            # 返回默认值以确保程序不会崩溃
            return (
                {'trend': '震荡整理', 'strength': 50.0, 'rsi_value': 50.0},
                {'volume_trend': '平稳', 'volume_ratio': 1.0, 'volume_price_correlation': 0.0},
                1.0,  # 默认波动率
                0.0   # 默认周期共振
            )
    
    def get_detailed_analysis(self, symbol: str) -> Dict:
        """获取单只股票的详细分析结果
        使用多级缓存和错误恢复机制提高性能和稳定性
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key = f"analysis_{symbol}"
        with self._cache_lock:
            if cache_key in self._analysis_cache and time.time() - self._analysis_cache[cache_key]['timestamp'] < self._analysis_cache_expiry:
                self._performance_metrics['cache_hits'] += 1
                self.logger.info(f"从缓存获取{symbol}分析结果")
                return self._analysis_cache[cache_key]['result']
        try:
            # 验证股票代码格式
            if not symbol:
                return {
                    'status': 'error',
                    'message': '股票代码不能为空'
                }
            
            # 标准化股票代码格式
            if '.' not in symbol:
                # 根据股票代码首字符判断市场
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                elif symbol.startswith(('0', '3')):
                    symbol = f"{symbol}.SZ"
                else:
                    return {
                        'status': 'error',
                        'message': f'无效的股票代码格式：{symbol}，请使用正确的股票代码（如：000001.SZ或600001.SH）'
                    }
            
            # 获取股票数据
            self._wait_for_api_limit()  # 确保API调用间隔
            # 获取股票数据（新增重试机制和超时控制）
            max_retries = 3
            retry_delay = 1
            for attempt in range(max_retries):
                try:
                    self._wait_for_api_limit()
                    df = self.visual_system.get_stock_data(symbol)
                    if df is not None and not df.empty:
                        break
                except (TimeoutError, ConnectionError) as e:
                    if attempt == max_retries - 1:
                        self.logger.error(f"获取{symbol}数据失败: {str(e)}")
                        return {'status':'error','message':'数据获取失败，请检查网络连接'}
                    time.sleep(retry_delay * (attempt + 1))
            
            # 增强数据验证
            required_columns = ['Open','High','Low','Close','Volume']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"{symbol}数据缺失必要列: {required_columns}")
                return {'status':'error','message':'数据格式不完整'}
            
            # 新增数据质量检查
            data_quality = df[required_columns].isnull().mean().max()
            if data_quality > 0.1:
                self.logger.warning(f"{symbol}数据存在{data_quality:.1%}空值")
                df = df.ffill().bfill()
            
            if df is None or df.empty:
                return {
                    'status': 'error',
                    'message': f'获取股票{symbol}数据失败，请检查股票代码是否正确或网络连接是否正常。如果网络正常，请确认该股票是否处于正常交易状态。'
                }
                
            # 技术指标分析
            df = self._calculate_technical_indicators(df)
            if df is None:
                return {
                    'status': 'error',
                    'message': f'计算{symbol}技术指标失败，可能是数据量不足'
                }
            
            # 趋势分析
            trend_analysis = self._analyze_trend(df)
            
            # 量价分析
            volume_analysis = self._analyze_volume_price(df)
            
            # 波动率分析
            try:
                volatility = float(self.jf_system.analyze_volatility_expansion(df))
            except (TypeError, ValueError):
                volatility = 1.0
            
            # 多周期共振
            try:
                cycle_resonance = float(self.jf_system.check_multi_cycle_resonance(df))
            except (TypeError, ValueError):
                cycle_resonance = 0.0
            
            # 生成交易建议
            trading_advice = self._generate_trading_advice(df, trend_analysis, volume_analysis, volatility, cycle_resonance)
            
            # 获取最新价格
            try:
                last_price = float(df['Close'].iloc[-1])
            except (IndexError, KeyError, ValueError, AttributeError) as e:
                last_price = 0.0
                
            # 暂时使用股票代码作为名称，稍后会更新
            stock_name = symbol
            
            # 构建完整的分析结果
            analysis_result = {
                'status': 'success',
                'data': {
                    'name': stock_name,
                    'symbol': symbol,
                    'last_price': last_price,
                    'price_explanation': '当前价格处于正常交易区间',
                    'trend_analysis': {
                        'trend': trend_analysis['trend'],
                        'strength': trend_analysis['strength'],
                        'strength_explanation': f"趋势强度为{trend_analysis['strength']:.2f}%，{'趋势可信度高' if trend_analysis['strength'] > 70 else '趋势可信度中等' if trend_analysis['strength'] > 40 else '趋势可信度低'}，{trend_analysis['trend']}形态明显" if trend_analysis['strength'] > 40 else f"趋势强度为{trend_analysis['strength']:.2f}%，趋势不明显，建议观望",
                        'rsi_value': trend_analysis['rsi_value'],
                        'rsi_explanation': f"RSI当前为{trend_analysis['rsi_value']:.2f}，{'处于超买区间，建议逢高减仓' if trend_analysis['rsi_value'] > 70 else '处于超卖区间，可以考虑买入' if trend_analysis['rsi_value'] < 30 else '处于中性区间'}"
                    },
                    'volume_analysis': {
                        'status': volume_analysis['volume_trend'],
                        'ratio': volume_analysis['volume_ratio'],
                        'volume_explanation': f"当前成交量是20日均量的{volume_analysis['volume_ratio']:.2f}倍，{'成交量显著放大，交投活跃' if volume_analysis['volume_ratio'] > 2 else '成交量温和放大' if volume_analysis['volume_ratio'] > 1.2 else '成交量低于均量水平，交投较为清淡'}"
                    },
                    'technical_indicators': {
                        'macd': df['MACD'].iloc[-1],
                        'macd_signal': df['MACD_Signal'].iloc[-1],
                        'macd_hist': df['MACD_Hist'].iloc[-1],
                        'macd_explanation': f"MACD指标：{'金叉形成，上涨动能增强' if df['MACD_Hist'].iloc[-1] > 0 and df['MACD_Hist'].iloc[-2] <= 0 else '死叉形成，下跌动能增强' if df['MACD_Hist'].iloc[-1] < 0 and df['MACD_Hist'].iloc[-2] >= 0 else 'MACD柱状持续为正，上涨趋势延续' if df['MACD_Hist'].iloc[-1] > 0 else 'MACD柱状持续为负，下跌趋势延续'}",
                        'k': df['K'].iloc[-1],
                        'd': df['D'].iloc[-1],
                        'j': df['J'].iloc[-1],
                        'kdj_explanation': f"KDJ指标：K值{df['K'].iloc[-1]:.2f}，{'已进入超买区间，注意回调风险' if df['K'].iloc[-1] > 80 else '已进入超卖区间，关注反弹机会' if df['K'].iloc[-1] < 20 else '处于中性区间'}"
                    },
                    'market_analysis': {
                        'volatility': volatility,
                        'volatility_explanation': f'波动率{volatility:.2f}，{"表示市场波动剧烈，建议谨慎操作" if volatility > 1.5 else "表示市场波动温和，可以考虑布局" if volatility < 0.8 else "表示市场波动处于中等水平，注意控制风险"}',
                        'cycle_resonance': cycle_resonance,
                        'resonance_explanation': f'周期共振{cycle_resonance:.2f}，{"表示多个周期趋势一致，信号较强" if cycle_resonance > 0.5 else "表示各周期趋势分散，建议观望"}'
                    },
                    'trading_advice': trading_advice['action'],
                    'trading_ranges': trading_advice['trading_ranges']
                }
            }
            
            # 分析结果生成后，再次尝试获取股票名称
            analysis_result = self._update_stock_name(analysis_result, symbol)
            
            # 缓存分析结果
            cache_key = f"analysis_{symbol}"
            with self._cache_lock:
                self._analysis_cache[cache_key] = {
                    'result': analysis_result,
                    'timestamp': time.time()
                }
                
            # 记录分析完成时间
            analysis_time = time.time() - start_time
            self.logger.info(f"分析股票{symbol}完成，耗时{analysis_time:.3f}秒")
            
            return analysis_result
            
        except Exception as e:
            print(f"分析股票{symbol}时发生错误：{str(e)}")
            return {
                'status': 'error',
                'message': f'分析股票{symbol}时发生错误：{str(e)}'
            }
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        try:
            if df is None or df.empty:
                raise ValueError("输入数据为空")

            required_columns = ['Close', 'High', 'Low', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必要的数据列：{', '.join(missing_columns)}")

            # 确保数据类型正确
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 检查是否有足够的数据点
            if len(df) < 30:  # 至少需要30个数据点才能计算指标
                raise ValueError(f"数据点数量不足：当前{len(df)}个，至少需要30个")

            # MACD计算
            try:
                macd, signal, hist = ta.MACD(
                    df['Close'].values,
                    fastperiod=12,
                    slowperiod=26,
                    signalperiod=9
                )
                df['MACD'] = pd.Series(macd, index=df.index)
                df['MACD_Signal'] = pd.Series(signal, index=df.index)
                df['MACD_Hist'] = pd.Series(hist, index=df.index)
                df[['MACD', 'MACD_Signal', 'MACD_Hist']] = df[['MACD', 'MACD_Signal', 'MACD_Hist']].fillna(0.0)
            except Exception as e:
                print(f"计算MACD时发生错误：{str(e)}")
                df['MACD'] = df['MACD_Signal'] = df['MACD_Hist'] = 0.0

            # RSI计算
            try:
                rsi = ta.RSI(df['Close'].values, timeperiod=14)
                df['RSI'] = pd.Series(rsi, index=df.index)
                df['RSI'] = df['RSI'].fillna(50.0)
                df['RSI'] = df['RSI'].clip(0, 100)  # 确保RSI值在0-100之间
            except Exception as e:
                print(f"计算RSI时发生错误：{str(e)}")
                df['RSI'] = 50.0

            # 布林带计算
            try:
                upper, middle, lower = ta.BBANDS(
                    df['Close'].values,
                    timeperiod=20,
                    nbdevup=2,
                    nbdevdn=2
                )
                df['BB_Upper'] = pd.Series(upper, index=df.index)
                df['BB_Middle'] = pd.Series(middle, index=df.index)
                df['BB_Lower'] = pd.Series(lower, index=df.index)
                # 使用前向填充和后向填充处理空值
                df[['BB_Upper', 'BB_Middle', 'BB_Lower']] = df[['BB_Upper', 'BB_Middle', 'BB_Lower']].ffill().bfill()
                
                # ATR计算
                try:
                    atr = ta.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
                    df['ATR'] = pd.Series(atr, index=df.index)
                    df['ATR'] = df['ATR'].ffill().bfill()
                except Exception as e:
                    print(f"计算ATR时发生错误：{str(e)}")
                    df['ATR'] = df['Close'].rolling(window=14).std().fillna(method='ffill').fillna(method='bfill')
            except Exception as e:
                print(f"计算布林带时发生错误：{str(e)}")
                df['BB_Upper'] = df['BB_Middle'] = df['BB_Lower'] = df['Close']

            # KDJ计算
            try:
                k, d = ta.STOCH(
                    df['High'].values,
                    df['Low'].values,
                    df['Close'].values,
                    fastk_period=9,
                    slowk_period=3,
                    slowk_matype=0,
                    slowd_period=3,
                    slowd_matype=0
                )
                df['K'] = pd.Series(k, index=df.index)
                df['D'] = pd.Series(d, index=df.index)
                df['J'] = 3 * df['K'] - 2 * df['D']
                # 填充空值并限制范围
                df[['K', 'D', 'J']] = df[['K', 'D', 'J']].fillna(50.0)
                df[['K', 'D', 'J']] = df[['K', 'D', 'J']].clip(0, 100)
            except Exception as e:
                print(f"计算KDJ时发生错误：{str(e)}")
                df['K'] = df['D'] = df['J'] = 50.0

            # 最终验证
            all_indicators = ['MACD', 'MACD_Signal', 'MACD_Hist', 'RSI', 
                            'BB_Upper', 'BB_Middle', 'BB_Lower', 'K', 'D', 'J']
            for col in all_indicators:
                if col not in df.columns:
                    df[col] = 50.0 if col in ['RSI', 'K', 'D', 'J'] else 0.0
                elif df[col].isnull().any():
                    print(f"警告：{col}列存在空值，已填充")
                    df[col] = df[col].fillna(50.0 if col in ['RSI', 'K', 'D', 'J'] else 0.0)

            return df
            
        except Exception as e:
            print(f"计算技术指标时发生错误：{str(e)}")
            # 确保返回的DataFrame包含所有必要的列
            required_columns = ['MACD', 'MACD_Signal', 'MACD_Hist', 'RSI', 
                              'BB_Upper', 'BB_Middle', 'BB_Lower', 'K', 'D', 'J']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 50.0 if col in ['RSI', 'K', 'D', 'J'] else 0.0
            return df
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析趋势状态
        使用多重技术指标综合判断趋势，提高趋势判断的准确性
        """
        try:
            if df is None or df.empty:
                raise ValueError("输入数据为空")

            required_columns = ['Close', 'MACD_Hist', 'RSI', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必要的数据列：{', '.join(missing_columns)}")

            # 获取最新技术指标值
            try:
                last_close = float(df['Close'].iloc[-1])
                last_macd_hist = float(df['MACD_Hist'].iloc[-1])
                rsi = float(df['RSI'].iloc[-1])
                volume = float(df['Volume'].iloc[-1])
                volume_ma = df['Volume'].rolling(window=20).mean().iloc[-1]
                price_ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
                price_ma60 = df['Close'].rolling(window=60).mean().iloc[-1]

                # 数据验证和处理
                if pd.isna(last_close) or last_close <= 0:
                    raise ValueError("无效的收盘价")
                last_macd_hist = 0.0 if pd.isna(last_macd_hist) else last_macd_hist
                rsi = 50.0 if pd.isna(rsi) or not (0 <= rsi <= 100) else rsi
                volume_ratio = 1.0 if pd.isna(volume_ma) or volume_ma == 0 else volume / volume_ma

            except (IndexError, KeyError, ValueError, TypeError) as e:
                print(f"获取技术指标数据时发生错误：{str(e)}")
                return {'trend': '数据异常', 'strength': 0.0, 'rsi_value': 50.0}

            # 趋势综合评分系统
            trend_score = 0.0  # 使用浮点数以提高精度
            
            # MACD趋势判断（权重：35%）
            trend_score += 35.0 if last_macd_hist > 0.001 else -35.0 if last_macd_hist < -0.001 else 0.0
            
            # RSI趋势判断（权重：25%）
            trend_score += 25.0 if rsi > 55 else -25.0 if rsi < 45 else 0.0
            
            # 均线趋势判断（权重：25%）
            if not pd.isna(price_ma20) and not pd.isna(price_ma60) and price_ma60 > 0:
                if price_ma20 > price_ma60:
                    trend_score += min(25.0 * (price_ma20 / price_ma60 - 1), 25.0)
                else:
                    trend_score -= min(25.0 * (price_ma60 / price_ma20 - 1), 25.0)
            
            # 成交量趋势判断（权重：15%）
            trend_score += 15.0 if volume_ratio > 1.2 else -15.0 if volume_ratio < 0.8 else 0.0
            
            # 根据综合评分判断趋势
            if trend_score > 35.0:  # 提高趋势判断阈值
                trend = '上升趋势'
                strength = min(abs(trend_score), 100.0)
            elif trend_score < -35.0:
                trend = '下降趋势'
                strength = min(abs(trend_score), 100.0)
            else:
                trend = '震荡整理'
                strength = 50.0
            
            return {
                'trend': trend,
                'strength': strength,
                'rsi_value': rsi
            }
            
        except Exception as e:
            print(f"分析趋势时发生错误：{str(e)}")
            return {
                'trend': '震荡整理',
                'strength': 50.0,
                'rsi_value': 50.0
            }
    
    def _analyze_volume_price(self, df: pd.DataFrame) -> Dict:
        """分析量价关系
        包含量能结构、主力资金流向、量价背离等多维度分析
        """
        try:
            if df is None or df.empty:
                raise ValueError("输入数据为空")

            required_columns = ['Volume', 'Close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必要的数据列：{', '.join(missing_columns)}")

            # 确保数据类型正确
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 基础量能指标计算
            try:
                df['Volume_MA5'] = df['Volume'].rolling(window=5, min_periods=1).mean()
                df['Volume_MA10'] = df['Volume'].rolling(window=10, min_periods=1).mean()
                df['Volume_MA20'] = df['Volume'].rolling(window=20, min_periods=1).mean()
                
                # 计算量能结构，避免除以零
                df['Volume_Ratio_5'] = df['Volume'] / df['Volume_MA5'].replace(0, np.nan).fillna(df['Volume'])
                df['Volume_Ratio_10'] = df['Volume'] / df['Volume_MA10'].replace(0, np.nan).fillna(df['Volume'])
                df['Volume_Ratio_20'] = df['Volume'] / df['Volume_MA20'].replace(0, np.nan).fillna(df['Volume'])
                
                # 填充可能的空值
                volume_cols = ['Volume_MA5', 'Volume_MA10', 'Volume_MA20', 
                              'Volume_Ratio_5', 'Volume_Ratio_10', 'Volume_Ratio_20']
                df[volume_cols] = df[volume_cols].ffill().fillna(1.0)
            except Exception as e:
                print(f"计算量能指标时发生错误：{str(e)}")
                df['Volume_MA5'] = df['Volume_MA10'] = df['Volume_MA20'] = df['Volume']
                df['Volume_Ratio_5'] = df['Volume_Ratio_10'] = df['Volume_Ratio_20'] = 1.0
            
            # 计算价格变化和均线
            try:
                df['Price_Change'] = df['Close'].pct_change().fillna(0)
                df['Price_MA5'] = df['Close'].rolling(window=5, min_periods=1).mean()
                df['Price_MA10'] = df['Close'].rolling(window=10, min_periods=1).mean()
                df['Price_MA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
                df['Price_MA60'] = df['Close'].rolling(window=60, min_periods=1).mean()
                
                # 填充可能的空值
                price_cols = ['Price_MA5', 'Price_MA10', 'Price_MA20', 'Price_MA60']
                df[price_cols] = df[price_cols].ffill().fillna(df['Close'])
            except Exception as e:
                print(f"计算价格均线时发生错误：{str(e)}")
                df['Price_Change'] = 0.0
                df['Price_MA5'] = df['Price_MA10'] = df['Price_MA20'] = df['Price_MA60'] = df['Close']
            
            # 计算量价配合度
            try:
                # 使用更短的时间窗口计算相关性，避免长期趋势的影响
                volume_price_corr = df['Volume'].tail(20).corr(df['Close'].tail(20))
                if pd.isna(volume_price_corr):
                    volume_price_corr = 0.0
            except Exception as e:
                print(f"计算量价相关性时发生错误：{str(e)}")
                volume_price_corr = 0.0
            
            # 判断量价趋势
            try:
                last_volume = float(df['Volume'].iloc[-1])
                last_volume_ma20 = float(df['Volume_MA20'].iloc[-1])
                
                # 确保分母不为零
                if last_volume_ma20 > 0:
                    volume_ratio = last_volume / last_volume_ma20
                else:
                    volume_ratio = 1.0
                
                # 限制量比范围，避免极端值
                volume_ratio = min(max(volume_ratio, 0.1), 10.0)
                
                if volume_ratio > 1.2:
                    volume_trend = '放量'
                elif volume_ratio < 0.8:
                    volume_trend = '缩量'
                else:
                    volume_trend = '平稳'
            except Exception as e:
                print(f"判断量价趋势时发生错误：{str(e)}")
                volume_trend = '平稳'
                volume_ratio = 1.0
            
            return {
                'volume_trend': volume_trend,
                'volume_ratio': volume_ratio,
                'volume_price_correlation': volume_price_corr
            }
        except Exception as e:
            print(f"分析量价关系时发生错误：{str(e)}")
            return {
                'volume_trend': '平稳',
                'volume_ratio': 1.0,
                'volume_price_correlation': 0.0
            }
            
    def _generate_trading_advice(self, df: pd.DataFrame, trend_analysis: Dict, volume_analysis: Dict, volatility: float, cycle_resonance: float) -> Dict:
        """生成交易建议
        根据趋势分析、量价分析、波动率和周期共振等指标生成综合交易建议
        """
        try:
            # 数据验证
            if df is None or df.empty:
                raise ValueError("输入数据无效")
                
            # 获取最新的技术指标值并进行数据验证
            try:
                last_close = float(df['Close'].iloc[-1])
                if pd.isna(last_close) or last_close <= 0:
                    raise ValueError("无效的收盘价")
                    
                last_macd_hist = float(df['MACD_Hist'].iloc[-1])
                if pd.isna(last_macd_hist):
                    last_macd_hist = 0.0
                    
                last_rsi = float(df['RSI'].iloc[-1])
                if pd.isna(last_rsi) or last_rsi < 0 or last_rsi > 100:
                    last_rsi = 50.0
                    
                last_k = float(df['K'].iloc[-1])
                if pd.isna(last_k) or last_k < 0 or last_k > 100:
                    last_k = 50.0

                # 计算支撑位和阻力位
                support_level = min(df['Low'].tail(20).min(), last_close * 0.95)
                resistance_level = max(df['High'].tail(20).max(), last_close * 1.05)

                # 计算信号得分
                signal_score = 0.0
                signal_score += 1.0 if trend_analysis['trend'] == '上升趋势' else -1.0 if trend_analysis['trend'] == '下降趋势' else 0.0
                signal_score += 0.5 if volume_analysis['volume_trend'] == '放量' else -0.5 if volume_analysis['volume_trend'] == '缩量' else 0.0
                signal_score += 0.5 if last_rsi > 50 else -0.5 if last_rsi < 50 else 0.0
                signal_score += 0.5 if last_macd_hist > 0 else -0.5 if last_macd_hist < 0 else 0.0
                signal_score += 0.5 if cycle_resonance > 0.5 else -0.5 if cycle_resonance < 0.3 else 0.0

            except (IndexError, KeyError, ValueError, TypeError) as e:
                print(f"获取技术指标值时发生错误：{str(e)}")
                raise ValueError("无法获取有效的技术指标数据")
            
            # 初始化建议结果
            # 安全地获取ATR值，如果不存在则使用价格的一定比例作为替代
            atr_value = df['ATR'].iloc[-1] if 'ATR' in df.columns else (last_close * 0.02)
            buy_range_low = support_level + atr_value * 0.5
            buy_range_high = support_level + atr_value * 1.5
            sell_range_low = resistance_level - atr_value * 0.5
            sell_range_high = resistance_level - atr_value * 1.5
            advice = {
                'action': '建议观望',
                'confidence': 0.65,
                'risk_level': '中',
                'stop_loss': support_level,
                'take_profit': resistance_level,
                'trading_ranges': {
                    'buy_range': {'low': buy_range_low, 'high': buy_range_high},
                    'sell_range': {'low': sell_range_low, 'high': sell_range_high},
                    'support': support_level,
                    'resistance': resistance_level,
                }
            }
            if signal_score >= 0.8:
                advice['action'] = '建议买入'
                advice['confidence'] = 0.7
                advice['explanation'] = '上涨趋势明显，建议适量建仓'
                advice['risk_level'] = '低'
                advice['stop_loss'] = support_level
                advice['take_profit'] = resistance_level
                advice['trading_ranges'] = {
                    'buy_range': {'low': buy_range_low, 'high': buy_range_high},
                    'sell_range': {'low': sell_range_low, 'high': sell_range_high},
                    'support': support_level,
                    'resistance': resistance_level,
                    'explanation': f'建议在{buy_range_low:.2f}-{buy_range_high:.2f}区间买入，在{sell_range_low:.2f}-{sell_range_high:.2f}区间卖出，止损位{support_level:.2f}'
                }
            elif signal_score >= 1:
                advice['action'] = '强烈建议买入'
                advice['confidence'] = 0.9
                advice['explanation'] = '多重技术指标共振，强势上涨信号明确'
                advice['risk_level'] = '低'
                advice['stop_loss'] = support_level
                advice['take_profit'] = resistance_level
                advice['trading_ranges'] = {
                    'buy_range': {'low': buy_range_low, 'high': buy_range_high},
                    'sell_range': {'low': sell_range_low, 'high': sell_range_high},
                    'support': support_level,
                    'resistance': resistance_level,
                    'explanation': f'建议在{buy_range_low:.2f}-{buy_range_high:.2f}区间买入，在{sell_range_low:.2f}-{sell_range_high:.2f}区间卖出，止损位{support_level:.2f}'
                }
            elif signal_score >= 0.5:
                advice['action'] = '建议买入'
                advice['confidence'] = 0.7
                advice['explanation'] = '上涨趋势形成，建议分批建仓'
                advice['risk_level'] = '中低'
                advice['stop_loss'] = last_close * 0.93
                advice['take_profit'] = last_close * 1.1
                advice['trading_ranges'] = {
                    'buy_range': {'low': last_close * 0.97, 'high': last_close * 1.03},
                    'sell_range': {'low': last_close * 1.08, 'high': last_close * 1.1},
                    'support': last_close * 0.93,
                    'resistance': last_close * 1.1,
                    'explanation': '建议在支撑位附近分批买入，在阻力位附近分批卖出'
                }
            elif signal_score <= -3:
                advice['action'] = '强烈建议卖出'
                advice['confidence'] = 0.9
                advice['explanation'] = '多重技术指标共振，下跌信号明确'
                advice['risk_level'] = '高'
                advice['stop_loss'] = last_close * 1.05
                advice['take_profit'] = last_close * 0.85
                advice['trading_ranges'] = {
                    'buy_range': {'low': last_close * 0.85, 'high': last_close * 0.88},
                    'sell_range': {'low': last_close * 0.98, 'high': last_close * 1.02},
                    'support': last_close * 0.85,
                    'resistance': last_close * 1.05,
                    'explanation': '建议在当前价格附近分批卖出，等待企稳后再考虑买入'
                }
            elif signal_score <= -1:
                advice['action'] = '建议卖出'
                advice['confidence'] = 0.7
                advice['explanation'] = '下跌趋势形成，建议分批减仓'
                advice['risk_level'] = '中高'
                advice['stop_loss'] = last_close * 1.07
                advice['take_profit'] = last_close * 0.9
                advice['trading_ranges'] = {
                    'buy_range': {'low': last_close * 0.88, 'high': last_close * 0.92},
                    'sell_range': {'low': last_close * 0.97, 'high': last_close * 1.03},
                    'support': last_close * 0.9,
                    'resistance': last_close * 1.07,
                    'explanation': '建议在当前价格附近分批卖出，等待企稳后再考虑买入'
                }
            else:
                advice['action'] = '观望'
                advice['confidence'] = 0.5
                advice['explanation'] = '市场信号不明确，建议观望'
                advice['risk_level'] = '中等'
                advice['stop_loss'] = last_close * 0.95
                advice['take_profit'] = last_close * 1.05
                advice['trading_ranges'] = {
                    'buy_range': {'low': last_close * 0.95, 'high': last_close * 0.98},
                    'sell_range': {'low': last_close * 1.02, 'high': last_close * 1.05},
                    'support': last_close * 0.95,
                    'resistance': last_close * 1.05,
                    'explanation': '市场震荡，建议等待明确信号'
                }
            
            return advice
            
        except Exception as e:
            print(f"生成交易建议时发生错误：{str(e)}")
            return {
                'action': '数据异常',
                'confidence': 0,
                'explanation': f'分析过程中出现错误：{str(e)}',
                'risk_level': '未知',
                'stop_loss': None,
                'take_profit': None,
                'trading_ranges': {
                    'buy_range': {'low': None, 'high': None},
                    'sell_range': {'low': None, 'high': None},
                    'support': None,
                    'resistance': None,
                    'explanation': '由于数据异常，无法提供准确的交易区间建议'
                }
            }