#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import talib as ta
from typing import Dict, List, Any, Union, Optional, Set
import time
import logging
from datetime import datetime

class LazyStockAnalyzer:
    """
    LazyStockAnalyzer类 - 一个高效的股票分析器
    只计算请求的技术指标，避免冗余计算
    """
    
    def __init__(self, required_indicators=None):
        """初始化分析器
        
        Args:
            required_indicators: 需要计算的指标列表，可以是'all'或特定指标列表
        """
        self.supported_indicators = {
            'ma', 'ema', 'macd', 'rsi', 'boll', 'kdj', 'atr', 
            'adx', 'obv', 'trend_direction', 'volume_ratio'
        }
        
        if required_indicators == 'all' or required_indicators == ['all']:
            self.required_indicators = self.supported_indicators
        elif required_indicators is None:
            self.required_indicators = set()
        else:
            self.required_indicators = set(required_indicators).intersection(self.supported_indicators)
            
        self.logger = logging.getLogger(__name__)
            
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析股票数据
        
        Args:
            df: 股票数据DataFrame，至少应包含open, high, low, close, volume列
            
        Returns:
            包含所需技术指标的字典
        """
        try:
            start_time = time.time()
            
            # 确保DataFrame有数据
            if df is None or len(df) < 20:
                self.logger.warning(f"数据不足({len(df) if df is not None else 0}条)，技术分析可能不准确")
            
            # 标准化列名
            data = df.copy()
            
            # 尝试不同的列名映射
            ohlcv_mapping = self._get_column_mapping(data)
            
            # 重命名列
            renamed_columns = {}
            for std_name, possible_names in ohlcv_mapping.items():
                for col_name in possible_names:
                    if col_name in data.columns:
                        renamed_columns[col_name] = std_name
                        break
            
            if renamed_columns:
                data = data.rename(columns=renamed_columns)
            
            # 确保基本OHLCV列存在
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            
            if missing_cols:
                self.logger.warning(f"缺少必要的列: {missing_cols}")
                # 尝试用最接近的列填充
                for col in missing_cols:
                    if col == 'open' and 'close' in data.columns:
                        data['open'] = data['close']
                    elif col == 'high' and 'close' in data.columns:
                        data['high'] = data['close']
                    elif col == 'low' and 'close' in data.columns:
                        data['low'] = data['close']
                    elif col == 'volume':
                        data['volume'] = 0
            
            # 初始化结果字典
            result = {}
            
            # 添加基本信息
            if len(data) > 0:
                last_row = data.iloc[-1]
                result.update({
                    'date': data.index[-1] if hasattr(data.index[-1], 'strftime') else str(data.index[-1]),
                    'open': float(last_row.get('open', 0)),
                    'high': float(last_row.get('high', 0)),
                    'low': float(last_row.get('low', 0)),
                    'close': float(last_row.get('close', 0)),
                    'volume': float(last_row.get('volume', 0))
                })
            
            # 只计算需要的指标
            if self.required_indicators:
                if 'ma' in self.required_indicators:
                    self._calculate_ma(data, result)
                
                if 'ema' in self.required_indicators:
                    self._calculate_ema(data, result)
                
                if 'macd' in self.required_indicators:
                    self._calculate_macd(data, result)
                
                if 'rsi' in self.required_indicators:
                    self._calculate_rsi(data, result)
                
                if 'boll' in self.required_indicators:
                    self._calculate_boll(data, result)
                
                if 'kdj' in self.required_indicators:
                    self._calculate_kdj(data, result)
                
                if 'atr' in self.required_indicators:
                    self._calculate_atr(data, result)
                
                if 'volume_ratio' in self.required_indicators:
                    self._calculate_volume_ratio(data, result)
                
                if 'trend_direction' in self.required_indicators:
                    self._calculate_trend_direction(data, result)
                
                if 'adx' in self.required_indicators:
                    self._calculate_adx(data, result)
                
                if 'obv' in self.required_indicators:
                    self._calculate_obv(data, result)
            
            # 记录分析耗时
            end_time = time.time()
            result['analysis_time'] = round(end_time - start_time, 3)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析股票数据时出错: {str(e)}")
            # 返回默认结果
            return {
                'error': str(e),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'close': 0,
                'volume': 0
            }
    
    def _get_column_mapping(self, df):
        """获取列名映射"""
        return {
            'open': ['Open', 'open', 'OPEN', 'O', 'o', '开盘价', '开盘'],
            'high': ['High', 'high', 'HIGH', 'H', 'h', '最高价', '最高'],
            'low': ['Low', 'low', 'LOW', 'L', 'l', '最低价', '最低'],
            'close': ['Close', 'close', 'CLOSE', 'C', 'c', '收盘价', '收盘', 'Adj Close', 'adj_close'],
            'volume': ['Volume', 'volume', 'VOLUME', 'V', 'v', '成交量', '成交额']
        }
    
    def _calculate_ma(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算移动平均线"""
        try:
            # 检查是否有足够的数据
            if len(data) < 60:
                self.logger.warning(f"数据不足({len(data)}条)，MA计算可能不准确")
            
            # 计算各周期MA
            for period in [5, 10, 20, 30, 60]:
                if len(data) >= period:
                    ma = data['close'].rolling(window=period).mean()
                    if not ma.empty and not ma.isna().all():
                        result[f'ma{period}'] = float(ma.iloc[-1])
                    else:
                        result[f'ma{period}'] = float(data['close'].mean())
                else:
                    result[f'ma{period}'] = float(data['close'].mean())
        except Exception as e:
            self.logger.error(f"计算MA出错: {str(e)}")
    
    def _calculate_ema(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算指数移动平均线"""
        try:
            # 检查是否有足够的数据
            if len(data) < 60:
                self.logger.warning(f"数据不足({len(data)}条)，EMA计算可能不准确")
            
            # 计算各周期EMA
            for period in [5, 10, 21, 34, 55]:
                try:
                    ema = ta.EMA(data['close'].values, timeperiod=period)
                    if ema is not None and len(ema) > 0 and not np.isnan(ema[-1]):
                        result[f'ema{period}'] = float(ema[-1])
                    else:
                        self.logger.warning(f"EMA{period}全为NaN，尝试替代方法")
                        # 使用简单移动平均作为替代
                        result[f'ema{period}'] = float(data['close'].rolling(window=period).mean().iloc[-1])
                except Exception:
                    self.logger.warning(f"计算EMA{period}失败，使用简单移动平均替代")
                    result[f'ema{period}'] = float(data['close'].rolling(window=period).mean().iloc[-1])
        except Exception as e:
            self.logger.error(f"计算EMA出错: {str(e)}")
    
    def _calculate_macd(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算MACD指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 40:
                self.logger.warning(f"数据不足({len(data)}条)，MACD计算可能不准确")
            
            # 计算MACD
            try:
                macd, signal, hist = ta.MACD(
                    data['close'].values,
                    fastperiod=12,
                    slowperiod=26,
                    signalperiod=9
                )
                
                if macd is not None and len(macd) > 0 and not np.isnan(macd[-1]):
                    result['macd'] = float(macd[-1])
                    result['macd_signal'] = float(signal[-1])
                    result['macd_hist'] = float(hist[-1])
                else:
                    self.logger.warning("MACD全为NaN，尝试替代方法")
                    # 简单替代
                    ema12 = data['close'].ewm(span=12, adjust=False).mean()
                    ema26 = data['close'].ewm(span=26, adjust=False).mean()
                    macd_line = ema12 - ema26
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    macd_hist = macd_line - signal_line
                    
                    result['macd'] = float(macd_line.iloc[-1])
                    result['macd_signal'] = float(signal_line.iloc[-1])
                    result['macd_hist'] = float(macd_hist.iloc[-1])
            except Exception:
                self.logger.warning("MACD计算出错，使用替代方法")
                # 简单替代
                ema12 = data['close'].ewm(span=12, adjust=False).mean()
                ema26 = data['close'].ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_hist = macd_line - signal_line
                
                result['macd'] = float(macd_line.iloc[-1])
                result['macd_signal'] = float(signal_line.iloc[-1])
                result['macd_hist'] = float(macd_hist.iloc[-1])
        except Exception as e:
            self.logger.error(f"计算MACD出错: {str(e)}")
            result['macd'] = 0
            result['macd_signal'] = 0
            result['macd_hist'] = 0
    
    def _calculate_rsi(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算RSI指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 30:
                self.logger.warning(f"数据不足({len(data)}条)，RSI计算可能不准确")
            
            # 计算RSI
            for period in [6, 14, 24]:
                try:
                    rsi = ta.RSI(data['close'].values, timeperiod=period)
                    if rsi is not None and len(rsi) > 0 and not np.isnan(rsi[-1]):
                        result[f'rsi{period}'] = float(rsi[-1])
                    else:
                        # 使用pandas实现作为备选
                        delta = data['close'].diff()
                        gain = delta.where(delta > 0, 0)
                        loss = -delta.where(delta < 0, 0)
                        avg_gain = gain.rolling(window=period).mean()
                        avg_loss = loss.rolling(window=period).mean()
                        rs = avg_gain / avg_loss
                        rsi_pandas = 100 - (100 / (1 + rs))
                        result[f'rsi{period}'] = float(rsi_pandas.iloc[-1])
                except Exception:
                    # 使用pandas实现作为备选
                    delta = data['close'].diff()
                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)
                    avg_gain = gain.rolling(window=period).mean()
                    avg_loss = loss.rolling(window=period).mean()
                    rs = avg_gain / avg_loss
                    rsi_pandas = 100 - (100 / (1 + rs))
                    result[f'rsi{period}'] = float(rsi_pandas.iloc[-1])
            
            # 设置标准RSI (14天)
            result['rsi'] = result['rsi14']
        except Exception as e:
            self.logger.error(f"计算RSI出错: {str(e)}")
            result['rsi'] = 50  # 中性值
    
    def _calculate_boll(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算布林带"""
        try:
            # 检查是否有足够的数据
            if len(data) < 25:
                self.logger.warning(f"数据不足({len(data)}条)，布林带计算可能不准确")
            
            # 计算布林带 (20,2)
            ma20 = data['close'].rolling(window=20).mean()
            std20 = data['close'].rolling(window=20).std()
            
            result['boll_upper'] = float(ma20.iloc[-1] + 2 * std20.iloc[-1])
            result['boll_middle'] = float(ma20.iloc[-1])
            result['boll_lower'] = float(ma20.iloc[-1] - 2 * std20.iloc[-1])
            
            # 当前价格在布林带的位置 (0-1)
            last_close = data['close'].iloc[-1]
            band_width = result['boll_upper'] - result['boll_lower']
            if band_width > 0:
                result['boll_position'] = float((last_close - result['boll_lower']) / band_width)
            else:
                result['boll_position'] = 0.5
            
            # 布林带宽度百分比
            result['boll_width'] = float(band_width / result['boll_middle'] * 100)
        except Exception as e:
            self.logger.error(f"计算布林带出错: {str(e)}")
    
    def _calculate_kdj(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算KDJ指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 20:
                self.logger.warning(f"数据不足({len(data)}条)，KDJ计算可能不准确")
            
            # 计算KDJ 9,3,3
            low_min = data['low'].rolling(window=9).min()
            high_max = data['high'].rolling(window=9).max()
            
            rsv = (data['close'] - low_min) / (high_max - low_min) * 100
            k = rsv.ewm(alpha=1/3, adjust=False).mean()
            d = k.ewm(alpha=1/3, adjust=False).mean()
            j = 3 * k - 2 * d
            
            result['k'] = float(k.iloc[-1])
            result['d'] = float(d.iloc[-1])
            result['j'] = float(j.iloc[-1])
        except Exception as e:
            self.logger.error(f"计算KDJ出错: {str(e)}")
            # 设置为中性值
            result['k'] = 50
            result['d'] = 50
            result['j'] = 50
    
    def _calculate_atr(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算ATR指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 20:
                self.logger.warning(f"数据不足({len(data)}条)，ATR计算可能不准确")
            
            # 计算ATR 14
            tr1 = abs(data['high'] - data['low'])
            tr2 = abs(data['high'] - data['close'].shift(1))
            tr3 = abs(data['low'] - data['close'].shift(1))
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            atr = tr.rolling(window=14).mean()
            
            result['atr'] = float(atr.iloc[-1])
            
            # ATR百分比
            last_close = data['close'].iloc[-1]
            if last_close > 0:
                result['atr_percent'] = float(result['atr'] / last_close * 100)
            else:
                result['atr_percent'] = 0
        except Exception as e:
            self.logger.error(f"计算ATR出错: {str(e)}")
    
    def _calculate_volume_ratio(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算成交量相关指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 20:
                self.logger.warning(f"数据不足({len(data)}条)，成交量比率计算可能不准确")
            
            # 计算成交量均线
            vol_ma5 = data['volume'].rolling(window=5).mean()
            vol_ma10 = data['volume'].rolling(window=10).mean()
            vol_ma20 = data['volume'].rolling(window=20).mean()
            
            result['volume_ma5'] = float(vol_ma5.iloc[-1])
            result['volume_ma10'] = float(vol_ma10.iloc[-1])
            result['volume_ma20'] = float(vol_ma20.iloc[-1])
            
            # 计算成交量比率
            last_volume = data['volume'].iloc[-1]
            result['volume_ratio'] = float(last_volume / vol_ma20.iloc[-1]) if vol_ma20.iloc[-1] > 0 else 1.0
            
            # 计算相对成交量变化
            if len(data) > 1:
                prev_volume = data['volume'].iloc[-2]
                if prev_volume > 0:
                    result['volume_change'] = float((last_volume - prev_volume) / prev_volume * 100)
                else:
                    result['volume_change'] = 0
            else:
                result['volume_change'] = 0
        except Exception as e:
            self.logger.error(f"计算成交量比率出错: {str(e)}")
            result['volume_ratio'] = 1.0
    
    def _calculate_trend_direction(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算趋势方向"""
        try:
            # 检查是否有足够的数据
            if len(data) < 30:
                self.logger.warning(f"数据不足({len(data)}条)，趋势方向计算可能不准确")
            
            # 基于EMA和价格关系的趋势判断
            ema_short = data['close'].ewm(span=12, adjust=False).mean()
            ema_long = data['close'].ewm(span=26, adjust=False).mean()
            
            # 短期趋势：价格相对于短期均线
            price_vs_short = data['close'].iloc[-1] > ema_short.iloc[-1]
            
            # 中期趋势：短期均线相对于长期均线
            short_vs_long = ema_short.iloc[-1] > ema_long.iloc[-1]
            
            # 计算短期动量
            momentum_period = min(10, len(data)-1)
            momentum = (data['close'].iloc[-1] / data['close'].iloc[-momentum_period-1] - 1) * 100
            
            # 综合趋势得分 (-1 到 1)
            trend_score = 0
            
            if price_vs_short:
                trend_score += 0.3
            else:
                trend_score -= 0.3
                
            if short_vs_long:
                trend_score += 0.3
            else:
                trend_score -= 0.3
                
            if momentum > 5:
                trend_score += 0.4
            elif momentum > 0:
                trend_score += 0.2
            elif momentum < -5:
                trend_score -= 0.4
            elif momentum < 0:
                trend_score -= 0.2
                
            # 限制在-1到1的范围内
            trend_score = max(-1, min(1, trend_score))
            
            result['trend_direction'] = float(trend_score)
            result['momentum'] = float(momentum)
        except Exception as e:
            self.logger.error(f"计算趋势方向出错: {str(e)}")
            result['trend_direction'] = 0
    
    def _calculate_adx(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算ADX指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 30:
                self.logger.warning(f"数据不足({len(data)}条)，ADX计算可能不准确")
            
            # 计算DMI指标
            high = data['high']
            low = data['low']
            close = data['close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            atr = tr.rolling(window=14).mean()
            
            # Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            
            # Positive DM
            pos_dm = up_move.copy()
            pos_dm[pos_dm < 0] = 0
            pos_dm[(up_move < down_move) | (up_move <= 0)] = 0
            
            # Negative DM
            neg_dm = down_move.copy()
            neg_dm[neg_dm < 0] = 0
            neg_dm[(down_move < up_move) | (down_move <= 0)] = 0
            
            # Smooth DI
            pos_di = 100 * (pos_dm.rolling(window=14).mean() / atr)
            neg_di = 100 * (neg_dm.rolling(window=14).mean() / atr)
            
            # ADX
            dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
            adx = dx.rolling(window=14).mean()
            
            result['adx'] = float(adx.iloc[-1])
            result['pos_di'] = float(pos_di.iloc[-1])
            result['neg_di'] = float(neg_di.iloc[-1])
        except Exception as e:
            self.logger.error(f"计算ADX出错: {str(e)}")
            result['adx'] = 25  # 中性值
    
    def _calculate_obv(self, data: pd.DataFrame, result: Dict[str, Any]) -> None:
        """计算OBV指标"""
        try:
            # 检查是否有足够的数据
            if len(data) < 20:
                self.logger.warning(f"数据不足({len(data)}条)，OBV计算可能不准确")
            
            # 计算OBV
            obv = (data['close'] - data['close'].shift(1)).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)) * data['volume']
            obv = obv.cumsum()
            
            result['obv'] = float(obv.iloc[-1])
            
            # OBV均线
            obv_ma10 = obv.rolling(window=10).mean()
            result['obv_ma10'] = float(obv_ma10.iloc[-1])
            
            # OBV相对强度
            if not np.isnan(obv_ma10.iloc[-1]) and obv_ma10.iloc[-1] != 0:
                result['obv_ratio'] = float(obv.iloc[-1] / obv_ma10.iloc[-1])
            else:
                result['obv_ratio'] = 1.0
        except Exception as e:
            self.logger.error(f"计算OBV出错: {str(e)}")


# 测试函数
def test_lazy_analyzer():
    """测试LazyStockAnalyzer功能"""
    import time
    
    # 创建样本数据
    dates = pd.date_range(start='2022-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, size=100)
    }, index=dates)
    
    # 使用所有指标
    print("测试计算所有指标...")
    start_time = time.time()
    analyzer_all = LazyStockAnalyzer(required_indicators='all')
    result_all = analyzer_all.analyze(data)
    all_time = time.time() - start_time
    
    # 使用部分指标
    print("测试只计算部分指标...")
    start_time = time.time()
    analyzer_partial = LazyStockAnalyzer(required_indicators=['ma', 'rsi'])
    result_partial = analyzer_partial.analyze(data)
    partial_time = time.time() - start_time
    
    # 输出结果
    print(f"\n计算所有指标耗时: {all_time:.4f}秒，结果包含 {len(result_all)} 个指标")
    print(f"计算部分指标耗时: {partial_time:.4f}秒，结果包含 {len(result_partial)} 个指标")
    print(f"性能提升: {all_time/partial_time:.2f}倍")
    
    print("\n部分计算结果示例:")
    for key in ['close', 'volume', 'ma5', 'rsi', 'macd', 'trend_direction']:
        all_value = result_all.get(key, 'N/A')
        partial_value = result_partial.get(key, 'N/A')
        print(f"{key}: 全量计算={all_value}, 部分计算={partial_value}")
    
    return True


if __name__ == "__main__":
    test_lazy_analyzer() 