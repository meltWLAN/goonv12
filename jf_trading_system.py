import pandas as pd
import numpy as np
import talib as ta
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum

class TrendType(Enum):
    STRONG_UP = "强势上涨"
    WEAK_UP = "弱势上涨"
    SIDEWAYS = "盘整"
    WEAK_DOWN = "弱势下跌"
    STRONG_DOWN = "强势下跌"

class MarketEnvironment(Enum):
    BULL = "牛市"
    BEAR = "熊市"
    RANGE = "震荡市"

@dataclass
class MarketSignal:
    """市场信号数据结构"""
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    volatility: float
    trend_strength: float
    cycle_resonance: float
    risk_level: float
    market_env: MarketEnvironment
    trend_type: TrendType
    psychological_score: float  # 心理状态评分
    signal_quality: float  # 信号质量分数

class JFTradingSystem:
    def __init__(self):
        self.signals: List[MarketSignal] = []
        self.historical_signals = pd.DataFrame(columns=['timestamp','symbol','price','volume','volatility','signal_quality'])
        self.risk_threshold = 0.25  # 降低风险阈值，提高安全性
        self.min_profit_ratio = 3.5  # 提高最小盈亏比要求
        self.max_position_per_stock = 0.15  # 降低单股最大仓位
        self.max_drawdown_threshold = 0.08  # 收紧最大回撤阈值
        self.consecutive_loss_limit = 2  # 降低连续亏损限制
        self.psychological_threshold = 0.75  # 提高心理状态要求
        self.signal_quality_threshold = 0.8  # 信号质量阈值
        self.min_liquidity_score = 1.2  # 最小流动性评分
        self.trend_confirmation_period = 3  # 趋势确认周期
        self.volume_price_correlation_threshold = 0.7  # 量价相关性阈值
        
    def analyze_volatility_expansion(self, df: pd.DataFrame) -> float:
        """分析波动率扩张
        使用ATR指标衡量波动率变化，优化计算性能和稳定性
        """
        try:
            # 使用缓存避免重复计算
            cache_key = hash(tuple(df['Close'].tail(30).values.tolist()) if 'Close' in df.columns and len(df) >= 30 else 0)
            if hasattr(self, '_volatility_cache') and cache_key in self._volatility_cache:
                return self._volatility_cache[cache_key]
                
            # 确保输入数据不为空
            if df.empty or len(df) < 20:
                return 1.0
            
            # 确保必要的列存在且不含空值
            required_columns = ['High', 'Low', 'Close']
            if not all(col in df.columns for col in required_columns):
                return 1.0
            
            # 创建数据副本以避免修改原始数据
            df_copy = df[required_columns].copy()
            
            # 验证输入数据并填充空值
            has_nulls = df_copy.isnull().any().any()
            if has_nulls:
                # 使用更高效的填充方法
                df_copy = df_copy.ffill().bfill()
            
            # 计算ATR并转换为Series
            try:
                atr = pd.Series(ta.ATR(df_copy['High'].values, df_copy['Low'].values, df_copy['Close'].values, timeperiod=14))
                if atr.isnull().all() or len(atr) == 0:
                    if not hasattr(self, '_volatility_cache'):
                        self._volatility_cache = {}
                    self._volatility_cache[cache_key] = 1.0
                    return 1.0
            except Exception as e:
                if not hasattr(self, '_volatility_cache'):
                    self._volatility_cache = {}
                self._volatility_cache[cache_key] = 1.0
                return 1.0
                
            # 使用前向填充处理空值，然后使用后向填充确保首部的空值也被处理
            atr = atr.ffill().bfill()
            
            # 验证填充后的数据
            if atr.isnull().any():
                if not hasattr(self, '_volatility_cache'):
                    self._volatility_cache = {}
                self._volatility_cache[cache_key] = 1.0
                return 1.0
                
            # 计算移动平均，使用min_periods=1允许在数据不足时仍能计算
            atr_ma = atr.rolling(window=20, min_periods=1).mean()
            
            # 计算波动率扩张程度
            current_atr = atr.iloc[-1]
            avg_atr = atr_ma.iloc[-1]
            
            if pd.isna(current_atr) or pd.isna(avg_atr) or avg_atr <= 0:
                if not hasattr(self, '_volatility_cache'):
                    self._volatility_cache = {}
                self._volatility_cache[cache_key] = 1.0
                return 1.0
                
            expansion_ratio = current_atr / avg_atr
            
            # 限制扩张比率的范围，避免极端值
            result = min(max(expansion_ratio, 0.5), 3.0)
            
            # 缓存结果
            if not hasattr(self, '_volatility_cache'):
                self._volatility_cache = {}
            self._volatility_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            # 出现异常时返回默认值并记录错误
            import logging
            logging.getLogger('JFTradingSystem').error(f"计算波动率扩张时发生错误: {str(e)}")
            return 1.0

    def check_multi_cycle_resonance(self, df: pd.DataFrame) -> float:
        """增强版多周期共振检测算法
        新增MACD趋势验证和布林带宽度分析
        """
        try:
            # 使用缓存避免重复计算
            cache_key = hash(tuple(df['Close'].tail(60).values.tolist()) if 'Close' in df.columns and len(df) >= 60 else 0)
            if hasattr(self, '_resonance_cache') and cache_key in self._resonance_cache:
                return self._resonance_cache[cache_key]

            # 数据验证
            if df is None or df.empty or len(df) < 60 or 'Close' not in df.columns:
                return 0.0

            # 计算多周期EMA（新增5日、30日、60日周期）
            close_values = df['Close'].ffill().bfill().values
            periods = [5, 10, 21, 30, 55, 60]
            ema_values = {
                f'ema_{p}': ta.EMA(close_values, timeperiod=p)
                for p in periods
            }

            # 趋势排列验证（要求至少3个周期形成趋势）
            trend_counts = 0
            for i in range(2, len(periods)):
                if (df['Close'].iloc[-1] > ema_values[f'ema_{periods[i-2]}'][-1] 
                    and ema_values[f'ema_{periods[i-2]}'][-1] > ema_values[f'ema_{periods[i-1]}'][-1] 
                    and ema_values[f'ema_{periods[i-1]}'][-1] > ema_values[f'ema_{periods[i]}'][-1]):
                    trend_counts += 1
                elif (df['Close'].iloc[-1] < ema_values[f'ema_{periods[i-2]}'][-1] 
                      and ema_values[f'ema_{periods[i-2]}'][-1] < ema_values[f'ema_{periods[i-1]}'][-1] 
                      and ema_values[f'ema_{periods[i-1]}'][-1] < ema_values[f'ema_{periods[i]}'][-1]):
                    trend_counts += 1

            # MACD趋势验证
            macd, macd_signal, _ = ta.MACD(close_values)
            macd_trend = macd[-1] > macd_signal[-1] if len(macd) > 0 else False

            # 布林带宽度分析
            upper, middle, lower = ta.BBANDS(close_values)
            bb_width = (upper[-1] - lower[-1]) / middle[-1] if middle[-1] != 0 else 0

            # 综合趋势强度计算（加入波动率因子）
            trend_strength = (sum(
                (ema_values[f'ema_{p}'][-1] - ema_values[f'ema_{p*2}'][-1]) / ema_values[f'ema_{p*2}'][-1]
                for p in [5, 10, 21] if p*2 in periods
            ) / 3) * (1 + bb_width)

            # 共振条件：至少3个周期趋势一致且MACD验证通过
            result = trend_strength if trend_counts >=3 and macd_trend else 0.0
            
            # 更新缓存
            if not hasattr(self, '_resonance_cache'):
                self._resonance_cache = {}
            self._resonance_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            import logging
            logging.getLogger('JFTradingSystem').error(f"计算多周期共振时发生错误: {str(e)}")
            return 0.0
    
    def calculate_kelly_position(self, win_rate: float, profit_ratio: float) -> float:
        """使用凯利公式计算仓位
        win_rate: 胜率
        profit_ratio: 盈亏比
        """
        q = 1 - win_rate
        f = (win_rate * profit_ratio - q) / profit_ratio
        
        # 考虑风险阈值限制
        return min(max(f, 0), self.risk_threshold)
    
    def analyze_policy_impact(self, df: pd.DataFrame, policy_heat: float = 1.0) -> Dict:
        """分析政策影响
        policy_heat: 政策热度系数，默认为1.0（无影响）
        """
        # 计算政策量能指标(PEV)
        df['PEV'] = df['Volume'] * policy_heat
        df['PEV_MA20'] = df['PEV'].rolling(window=20).mean()
        
        # 计算PEV分位数
        pev_percentile = (df['PEV'].iloc[-1] - df['PEV'].min()) / (df['PEV'].max() - df['PEV'].min()) * 100
        
        # 判断是否突破90分位
        pev_breakthrough = pev_percentile > 90
        
        return {
            'pev_value': df['PEV'].iloc[-1],
            'pev_percentile': pev_percentile,
            'pev_breakthrough': pev_breakthrough
        }
    
    def analyze_northbound_flow(self, df: pd.DataFrame, north_flow: float = 0) -> Dict:
        """分析北向资金流向
        north_flow: 北向资金净流入金额（亿元）
        """
        # 计算北向资金影响系数
        flow_impact = 1 + (north_flow / 100) if abs(north_flow) <= 100 else 2 if north_flow > 0 else 0.5
        
        # 检查流动性风险（使用数值类型：2=高风险，1=中等风险，0=低风险）
        liquidity_risk = 2 if north_flow < -80 else 1 if north_flow < -40 else 0
        
        return {
            'flow_impact': flow_impact,
            'liquidity_risk': liquidity_risk
        }

    def analyze_market_structure(self, df: pd.DataFrame, policy_heat: float = 1.0, north_flow: float = 0) -> Dict:
        """分析市场结构
        整合波动率扩张、多周期共振分析、政策影响和北向资金分析
        增加市场情绪和资金流向分析
        """
        # 基础市场结构分析
        try:
            volatility = float(self.analyze_volatility_expansion(df))
            resonance = float(self.check_multi_cycle_resonance(df))
        except (TypeError, ValueError) as e:
            print(f"计算基础市场指标时发生错误：{str(e)}")
            volatility = 1.0
            resonance = 0.0
        
        # 获取3L理论指标并进行数据验证
        try:
            liquidity_score = float(df['Liquidity_Score'].iloc[-1]) if 'Liquidity_Score' in df.columns else 1.0
            level_position = float(df['Level_Position'].iloc[-1]) if 'Level_Position' in df.columns else 0.0
            trend_strength = float(df['Trend_Strength'].iloc[-1]) if 'Trend_Strength' in df.columns else 0.0
            channel_width = float(df['Channel_Width'].iloc[-1]) if 'Channel_Width' in df.columns else 10.0
            
            # 数据合理性验证
            liquidity_score = max(0.1, min(liquidity_score, 5.0))
            level_position = max(-2.0, min(level_position, 2.0))
            trend_strength = max(-1.0, min(trend_strength, 1.0))
            channel_width = max(1.0, min(channel_width, 50.0))
        except Exception as e:
            print(f"处理3L理论指标时发生错误：{str(e)}")
            liquidity_score = 1.0
            level_position = 0.0
            trend_strength = 0.0
            channel_width = 10.0
        
        # 政策影响分析
        try:
            policy_analysis = self.analyze_policy_impact(df, policy_heat)
        except Exception as e:
            print(f"分析政策影响时发生错误：{str(e)}")
            policy_analysis = {'pev_breakthrough': False}
        
        # 北向资金分析
        try:
            flow_analysis = self.analyze_northbound_flow(df, north_flow)
        except Exception as e:
            print(f"分析北向资金时发生错误：{str(e)}")
            flow_analysis = {'flow_impact': 1.0, 'liquidity_risk': 0}
        
        # 市场情绪分析
        try:
            rsi = float(ta.RSI(df['Close'].values, timeperiod=14)[-1])
            k, d = ta.STOCH(df['High'].values, df['Low'].values, df['Close'].values,
                            fastk_period=9, slowk_period=3, slowk_matype=0,
                            slowd_period=3, slowd_matype=0)
            sentiment_score = (50 - abs(rsi - 50)) / 50  # RSI越接近50，市场情绪越稳定
            
            # 数据验证
            if pd.isna(rsi) or not (0 <= rsi <= 100):
                rsi = 50.0
                sentiment_score = 0.5
        except Exception as e:
            print(f"计算市场情绪指标时发生错误：{str(e)}")
            rsi = 50.0
            sentiment_score = 0.5
        
        # 计算资金流向强度
        volume_ma = df['Volume'].rolling(window=20).mean()
        price_change = df['Close'].pct_change()
        money_flow = (price_change * df['Volume'] / volume_ma).mean()
        
        # 计算综合胜率（考虑更多因素）
        base_win_rate = 0.19 if volatility > 1.5 and resonance > 0.02 else 0.5
        liquidity_bonus = 0.1 if liquidity_score > 1.5 else 0
        level_bonus = 0.1 if abs(level_position) < 1.0 else 0
        trend_bonus = 0.1 if trend_strength > 0.01 else 0
        sentiment_bonus = 0.1 if sentiment_score > 0.7 else 0
        flow_bonus = 0.1 if money_flow > 0 and flow_analysis['flow_impact'] > 1.2 else 0
        
        win_rate = min(max(
            base_win_rate + liquidity_bonus + level_bonus + trend_bonus + sentiment_bonus + flow_bonus,
            0.1
        ), 0.9)
        
        # 计算建议仓位（考虑通道宽度）
        position = self.calculate_kelly_position(win_rate, self.min_profit_ratio)
        position *= (1.0 / (1.0 + channel_width/100))  # 通道越宽，仓位越小
        
        # 根据北向资金流向调整仓位
        position *= flow_analysis['flow_impact']
        
        # 计算量价关系
        volume_price_correlation = df['Volume'].corr(df['Close'])
        volume_trend = df['Volume'].pct_change().mean()
        price_trend = df['Close'].pct_change().mean()
        
        # 计算市场环境和趋势类型
        market_env = (
            MarketEnvironment.BULL if trend_strength > 0.05 and volume_price_correlation > 0.6
            else MarketEnvironment.BEAR if trend_strength < -0.05 and volume_price_correlation < -0.6
            else MarketEnvironment.RANGE
        )
        
        trend_type = (
            TrendType.STRONG_UP if trend_strength > 0.05 and volume_trend > 0
            else TrendType.WEAK_UP if trend_strength > 0.02
            else TrendType.STRONG_DOWN if trend_strength < -0.05 and volume_trend < 0
            else TrendType.WEAK_DOWN if trend_strength < -0.02
            else TrendType.SIDEWAYS
        )
        
        return {
            'volatility_expansion': volatility,
            'cycle_resonance': resonance,
            'win_rate': win_rate,
            'suggested_position': position,
            'policy_signal': policy_analysis['pev_breakthrough'],
            'north_flow_risk': flow_analysis['liquidity_risk'],
            'liquidity_score': liquidity_score,
            'level_position': level_position,
            'trend_strength': trend_strength,
            'channel_width': channel_width,
            'volume_price_correlation': volume_price_correlation,
            'volume_trend': volume_trend,
            'price_trend': price_trend,
            'market_environment': market_env,
            'trend_type': trend_type
        }
    
    def generate_trading_signal(self, df: pd.DataFrame, symbol: str) -> Optional[MarketSignal]:
        """生成交易信号
        基于市场结构分析生成交易信号，增加多重验证机制
        """
        analysis = self.analyze_market_structure(df)
        
        # 计算信号质量分数
        signal_quality = self._calculate_signal_quality(analysis)
        
        # 计算心理状态评分
        psychological_score = self._evaluate_psychological_state(df)
        
        # 多重条件验证
        conditions = [
            analysis['volatility_expansion'] > 1.5,
            analysis['cycle_resonance'] > 0.02,
            signal_quality >= self.signal_quality_threshold,
            psychological_score >= self.psychological_threshold,
            analysis['volume_price_correlation'] >= self.volume_price_correlation_threshold,
            analysis['liquidity_score'] >= self.min_liquidity_score
        ]
        
        if all(conditions):
            signal = MarketSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                price=df['Close'].iloc[-1],
                volume=df['Volume'].iloc[-1],
                volatility=analysis['volatility_expansion'],
                trend_strength=analysis['trend_strength'],
                cycle_resonance=analysis['cycle_resonance'],
                risk_level=1 - analysis['suggested_position'],
                market_env=analysis['market_environment'],
                trend_type=analysis['trend_type'],
                psychological_score=psychological_score,
                signal_quality=signal_quality
            )
            self.signals.append(signal)
            # 保存历史信号
            new_record = {
                'timestamp': signal.timestamp,
                'symbol': signal.symbol,
                'price': signal.price,
                'volume': signal.volume,
                'volatility': signal.volatility,
                'signal_quality': signal.signal_quality
            }
            self.historical_signals = pd.concat([self.historical_signals, pd.DataFrame([new_record])], ignore_index=True)
            return signal
        
        return None
        
    def _calculate_signal_quality(self, analysis: Dict) -> float:
        """计算信号质量分数
        综合考虑多个指标评估信号的可靠性
        """
        weights = {
            'trend_strength': 0.25,
            'volume_price_correlation': 0.2,
            'cycle_resonance': 0.2,
            'volatility': 0.15,
            'liquidity': 0.1,
            'policy_impact': 0.1
        }
        
        scores = {
            'trend_strength': min(abs(analysis['trend_strength']) * 10, 1.0),
            'volume_price_correlation': abs(analysis['volume_price_correlation']),
            'cycle_resonance': min(analysis['cycle_resonance'] * 5, 1.0),
            'volatility': 1.0 if 1.2 <= analysis['volatility_expansion'] <= 2.0 else 0.5,
            'liquidity': min(analysis['liquidity_score'] / self.min_liquidity_score, 1.0),
            'policy_impact': 1.0 if analysis['policy_signal'] else 0.5
        }
        
        return sum(weights[k] * scores[k] for k in weights)
    
    def _evaluate_psychological_state(self, df: pd.DataFrame) -> float:
        """评估市场心理状态
        分析市场情绪和交易行为的理性程度
        """
        # 计算价格波动的标准差
        returns = df['Close'].pct_change()
        volatility = returns.std()
        
        # 计算成交量的稳定性
        volume_stability = 1 - df['Volume'].pct_change().std()
        
        # 计算RSI指标
        rsi = ta.RSI(df['Close'].values, timeperiod=14)[-1]
        rsi_score = 1 - abs(rsi - 50) / 50
        
        # 综合评分
        stability_score = 1 - min(volatility * 10, 1.0)  # 价格稳定性得分
        volume_score = min(max(volume_stability, 0), 1)  # 成交量稳定性得分
        
        return (stability_score * 0.4 + volume_score * 0.3 + rsi_score * 0.3)
    
    def get_trading_suggestion(self, signal: MarketSignal) -> str:
        """生成交易建议，增加多维度分析和风险控制
        优化止盈止损计算和仓位管理，提高决策精度
        """
        try:
            # 使用缓存避免重复计算
            cache_key = f"{signal.symbol}_{signal.timestamp.isoformat()}"
            if hasattr(self, '_suggestion_cache') and cache_key in self._suggestion_cache:
                return self._suggestion_cache[cache_key]
                
            # 增强的风险控制 - 多重验证
            if signal.risk_level > 0.7 or signal.signal_quality < self.signal_quality_threshold:
                result = "风险过高或信号质量不足，建议观望"
                if not hasattr(self, '_suggestion_cache'):
                    self._suggestion_cache = {}
                self._suggestion_cache[cache_key] = result
                return result
            
            # 市场环境分析 - 增加更多市场环境判断
            if signal.market_env == MarketEnvironment.BEAR and signal.trend_type in [TrendType.WEAK_DOWN, TrendType.STRONG_DOWN]:
                result = "当前处于熊市下跌趋势，建议观望或谨慎持仓"
                if not hasattr(self, '_suggestion_cache'):
                    self._suggestion_cache = {}
                self._suggestion_cache[cache_key] = result
                return result
            
            # 强信号条件（增加更多验证和精细化条件）
            # 增强交易信号条件（新增流动性评分和市场情绪指标）
            liquidity_score = signal.liquidity_score if hasattr(signal, 'liquidity_score') else 1.0
            market_sentiment = signal.market_sentiment if hasattr(signal, 'market_sentiment') else 0.5
            
            strong_signal = (
            signal.trend_strength > 0.05
            and 1.2 <= signal.volatility <= 2.0
            and signal.signal_quality > 0.85
            and liquidity_score > self.min_liquidity_score
            and market_sentiment > 0.6
            )
            
            # 优化仓位计算（新增流动性因子）
            liquidity_factor = min(liquidity_score / self.min_liquidity_score, 2.0)
            position = min(
            position_size * market_factor * quality_factor * liquidity_factor,
            self.max_position_per_stock * 100
            )
            
            # 增强缓存机制（新增缓存有效性验证）
            if hasattr(self, '_suggestion_cache') and cache_key in self._suggestion_cache:
                cached_time = time.time() - self._suggestion_cache[cache_key]['timestamp']
                if cached_time < 3600:  # 1小时缓存有效期
                    return self._suggestion_cache[cache_key]['result']
            
            # 新增详细日志记录
            logging.info(f"生成交易建议 {cache_key}: 流动性评分={liquidity_score:.2f} 市场情绪={market_sentiment:.2f}")
            
            # 动态止损计算 - 使用自适应ATR倍数
            # 动态ATR倍数（波动率越大倍数越高）
            atr_multiplier = 2.0 + (signal.volatility - 1.0) * 0.5
            atr_multiplier = min(max(atr_multiplier, 1.5), 3.5)
            
            # 这里应该有更多代码...
            
        except Exception as e:
            import logging
            logging.error(f"生成交易建议时发生错误: {str(e)}")
            return "处理交易信号时发生错误，建议观望"
            
            atr = signal.volatility * signal.price * 0.01  # 估算ATR值
            base_stop_loss = signal.price - (atr_multiplier * atr)  # 基础止损位
            
            # 根据趋势强度和市场环境动态调整止损
            trend_factor = 1 + abs(signal.trend_strength)
            market_env_factor = 1.0
            if signal.market_env == MarketEnvironment.BULL:
                market_env_factor = 0.9  # 牛市中可以设置更紧的止损
            elif signal.market_env == MarketEnvironment.BEAR:
                market_env_factor = 1.2  # 熊市中需要更宽松的止损
                
            stop_loss = max(base_stop_loss * trend_factor * market_env_factor, signal.price * 0.9)  # 确保止损不超过10%
            
            # 动态计算风险收益比
            if signal.signal_quality > 0.9:
                risk_reward_ratio = 3.0  # 高质量信号使用更高的风险收益比
            elif signal.signal_quality > 0.8:
                risk_reward_ratio = 2.5
            else:
                risk_reward_ratio = 2.0  # 较低质量信号使用保守的风险收益比
                
            # 计算止盈位
            take_profit = signal.price + (signal.price - stop_loss) * risk_reward_ratio
            
            # 计算风险调整后的仓位 - 考虑更多因素
            max_risk_per_trade = 0.02  # 单次交易最大风险2%
            position_size = max_risk_per_trade / ((signal.price - stop_loss) / signal.price)
            
            # 根据市场环境和信号质量综合调整仓位
            market_factor = 1.0
            if signal.market_env == MarketEnvironment.BULL:
                market_factor = 1.2
            elif signal.market_env == MarketEnvironment.BEAR:
                market_factor = 0.7
                
            quality_factor = 0.8 + (signal.signal_quality - 0.8) * 2  # 信号质量因子，0.8-1.2范围
            
            # 生成交易建议
            if strong_signal:
                # 强信号使用更激进的仓位，但有严格限制
                position = min(position_size * market_factor * quality_factor * 1.5, self.max_position_per_stock * 100)
                result = (
                    f"强信号触发 - {signal.trend_type.value}\n"
                    f"信号质量: {signal.signal_quality:.2f}\n"
                    f"市场环境: {signal.market_env.value}\n"
                    f"建议仓位: {position:.1f}%\n"
                    f"止损价格: {stop_loss:.2f}\n"
                    f"止盈价格: {take_profit:.2f}\n"
                    f"风险提示: 建议设置移动止损，保护盈利\n"
                    f"操作建议: 分批建仓，首次建议使用{position * 0.5:.1f}%仓位，可在回调时加仓"
                )
            elif weak_signal:
                # 弱信号使用保守仓位
                position = min(position_size * market_factor * quality_factor * 0.7, self.max_position_per_stock * 50)
                result = (
                    f"弱信号触发 - {signal.trend_type.value}\n"
                    f"信号质量: {signal.signal_quality:.2f}\n"
                    f"市场环境: {signal.market_env.value}\n"
                    f"建议仓位: {position:.1f}%\n"
                    f"止损价格: {stop_loss:.2f}\n"
                    f"止盈价格: {take_profit:.2f}\n"
                    f"风险提示: 注意设置止损，控制风险\n"
                    f"操作建议: 谨慎建仓，首次建议使用{position * 0.3:.1f}%仓位，观察确认趋势后再考虑加仓"
                )
            else:
                # 无明确信号
                result = (
                    f"当前无明确信号，建议观望\n"
                    f"市场环境: {signal.market_env.value}\n"
                    f"信号质量: {signal.signal_quality:.2f}\n"
                    f"关注价格: {signal.price:.2f}\n"
                    f"支撑位: {signal.price * 0.95:.2f}\n"
                    f"阻力位: {signal.price * 1.05:.2f}\n"
                    f"操作建议: 等待更明确的市场信号出现"
                )
            
            # 缓存结果
            if not hasattr(self, '_suggestion_cache'):
                self._suggestion_cache = {}
            self._suggestion_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            import logging
            logging.getLogger('JFTradingSystem').error(f"生成交易建议时发生错误：{str(e)}")
            return "生成交易建议时发生错误，建议观望"
    
    def check_multi_cycle_resonance(self, df: pd.DataFrame) -> float:
        """增强版多周期共振检测算法
        新增MACD趋势验证和布林带宽度分析
        """
        try:
            # 使用缓存避免重复计算
            cache_key = hash(tuple(df['Close'].tail(60).values.tolist()) if 'Close' in df.columns and len(df) >= 60 else 0)
            if hasattr(self, '_resonance_cache') and cache_key in self._resonance_cache:
                return self._resonance_cache[cache_key]

            # 数据验证
            if df is None or df.empty or len(df) < 60 or 'Close' not in df.columns:
                return 0.0

            # 计算多周期EMA（新增5日、30日、60日周期）
            close_values = df['Close'].ffill().bfill().values
            periods = [5, 10, 21, 30, 55, 60]
            ema_values = {
                f'ema_{p}': ta.EMA(close_values, timeperiod=p)
                for p in periods
            }

            # 趋势排列验证（要求至少3个周期形成趋势）
            trend_counts = 0
            for i in range(2, len(periods)):
                if (df['Close'].iloc[-1] > ema_values[f'ema_{periods[i-2]}'][-1] 
                    and ema_values[f'ema_{periods[i-2]}'][-1] > ema_values[f'ema_{periods[i-1]}'][-1] 
                    and ema_values[f'ema_{periods[i-1]}'][-1] > ema_values[f'ema_{periods[i]}'][-1]):
                    trend_counts += 1
                elif (df['Close'].iloc[-1] < ema_values[f'ema_{periods[i-2]}'][-1] 
                      and ema_values[f'ema_{periods[i-2]}'][-1] < ema_values[f'ema_{periods[i-1]}'][-1] 
                      and ema_values[f'ema_{periods[i-1]}'][-1] < ema_values[f'ema_{periods[i]}'][-1]):
                    trend_counts += 1

            # MACD趋势验证
            macd, macd_signal, _ = ta.MACD(close_values)
            macd_trend = macd[-1] > macd_signal[-1] if len(macd) > 0 else False

            # 布林带宽度分析
            upper, middle, lower = ta.BBANDS(close_values)
            bb_width = (upper[-1] - lower[-1]) / middle[-1] if middle[-1] != 0 else 0

            # 综合趋势强度计算（加入波动率因子）
            trend_strength = (sum(
                (ema_values[f'ema_{p}'][-1] - ema_values[f'ema_{p*2}'][-1]) / ema_values[f'ema_{p*2}'][-1]
                for p in [5, 10, 21] if p*2 in periods
            ) / 3) * (1 + bb_width)

            # 共振条件：至少3个周期趋势一致且MACD验证通过
            result = trend_strength if trend_counts >=3 and macd_trend else 0.0
            
            # 更新缓存
            if not hasattr(self, '_resonance_cache'):
                self._resonance_cache = {}
            self._resonance_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            import logging
            logging.getLogger('JFTradingSystem').error(f"计算多周期共振时发生错误: {str(e)}")
            return 0.0
    
    def calculate_kelly_position(self, win_rate: float, profit_ratio: float) -> float:
        """使用凯利公式计算仓位
        win_rate: 胜率
        profit_ratio: 盈亏比
        """
        q = 1 - win_rate
        f = (win_rate * profit_ratio - q) / profit_ratio
        
        # 考虑风险阈值限制
        return min(max(f, 0), self.risk_threshold)
    
    def analyze_policy_impact(self, df: pd.DataFrame, policy_heat: float = 1.0) -> Dict:
        """分析政策影响
        policy_heat: 政策热度系数，默认为1.0（无影响）
        """
        # 计算政策量能指标(PEV)
        df['PEV'] = df['Volume'] * policy_heat
        df['PEV_MA20'] = df['PEV'].rolling(window=20).mean()
        
        # 计算PEV分位数
        pev_percentile = (df['PEV'].iloc[-1] - df['PEV'].min()) / (df['PEV'].max() - df['PEV'].min()) * 100
        
        # 判断是否突破90分位
        pev_breakthrough = pev_percentile > 90
        
        return {
            'pev_value': df['PEV'].iloc[-1],
            'pev_percentile': pev_percentile,
            'pev_breakthrough': pev_breakthrough
        }
    
    def analyze_northbound_flow(self, df: pd.DataFrame, north_flow: float = 0) -> Dict:
        """分析北向资金流向
        north_flow: 北向资金净流入金额（亿元）
        """
        # 计算北向资金影响系数
        flow_impact = 1 + (north_flow / 100) if abs(north_flow) <= 100 else 2 if north_flow > 0 else 0.5
        
        # 检查流动性风险（使用数值类型：2=高风险，1=中等风险，0=低风险）
        liquidity_risk = 2 if north_flow < -80 else 1 if north_flow < -40 else 0
        
        return {
            'flow_impact': flow_impact,
            'liquidity_risk': liquidity_risk
        }

    def analyze_market_structure(self, df: pd.DataFrame, policy_heat: float = 1.0, north_flow: float = 0) -> Dict:
        """分析市场结构
        整合波动率扩张、多周期共振分析、政策影响和北向资金分析
        增加市场情绪和资金流向分析
        """
        # 基础市场结构分析
        try:
            volatility = float(self.analyze_volatility_expansion(df))
            resonance = float(self.check_multi_cycle_resonance(df))
        except (TypeError, ValueError) as e:
            print(f"计算基础市场指标时发生错误：{str(e)}")
            volatility = 1.0
            resonance = 0.0
        
        # 获取3L理论指标并进行数据验证
        try:
            liquidity_score = float(df['Liquidity_Score'].iloc[-1]) if 'Liquidity_Score' in df.columns else 1.0
            level_position = float(df['Level_Position'].iloc[-1]) if 'Level_Position' in df.columns else 0.0
            trend_strength = float(df['Trend_Strength'].iloc[-1]) if 'Trend_Strength' in df.columns else 0.0
            channel_width = float(df['Channel_Width'].iloc[-1]) if 'Channel_Width' in df.columns else 10.0
            
            # 数据合理性验证
            liquidity_score = max(0.1, min(liquidity_score, 5.0))
            level_position = max(-2.0, min(level_position, 2.0))
            trend_strength = max(-1.0, min(trend_strength, 1.0))
            channel_width = max(1.0, min(channel_width, 50.0))
        except Exception as e:
            print(f"处理3L理论指标时发生错误：{str(e)}")
            liquidity_score = 1.0
            level_position = 0.0
            trend_strength = 0.0
            channel_width = 10.0
        
        # 政策影响分析
        try:
            policy_analysis = self.analyze_policy_impact(df, policy_heat)
        except Exception as e:
            print(f"分析政策影响时发生错误：{str(e)}")
            policy_analysis = {'pev_breakthrough': False}
        
        # 北向资金分析
        try:
            flow_analysis = self.analyze_northbound_flow(df, north_flow)
        except Exception as e:
            print(f"分析北向资金时发生错误：{str(e)}")
            flow_analysis = {'flow_impact': 1.0, 'liquidity_risk': 0}
        
        # 市场情绪分析
        try:
            rsi = float(ta.RSI(df['Close'].values, timeperiod=14)[-1])
            k, d = ta.STOCH(df['High'].values, df['Low'].values, df['Close'].values,
                            fastk_period=9, slowk_period=3, slowk_matype=0,
                            slowd_period=3, slowd_matype=0)
            sentiment_score = (50 - abs(rsi - 50)) / 50  # RSI越接近50，市场情绪越稳定
            
            # 数据验证
            if pd.isna(rsi) or not (0 <= rsi <= 100):
                rsi = 50.0
                sentiment_score = 0.5
        except Exception as e:
            print(f"计算市场情绪指标时发生错误：{str(e)}")
            rsi = 50.0
            sentiment_score = 0.5
        
        # 计算资金流向强度
        volume_ma = df['Volume'].rolling(window=20).mean()
        price_change = df['Close'].pct_change()
        money_flow = (price_change * df['Volume'] / volume_ma).mean()
        
        # 计算综合胜率（考虑更多因素）
        base_win_rate = 0.19 if volatility > 1.5 and resonance > 0.02 else 0.5
        liquidity_bonus = 0.1 if liquidity_score > 1.5 else 0
        level_bonus = 0.1 if abs(level_position) < 1.0 else 0
        trend_bonus = 0.1 if trend_strength > 0.01 else 0
        sentiment_bonus = 0.1 if sentiment_score > 0.7 else 0
        flow_bonus = 0.1 if money_flow > 0 and flow_analysis['flow_impact'] > 1.2 else 0
        
        win_rate = min(max(
            base_win_rate + liquidity_bonus + level_bonus + trend_bonus + sentiment_bonus + flow_bonus,
            0.1
        ), 0.9)
        
        # 计算建议仓位（考虑通道宽度）
        position = self.calculate_kelly_position(win_rate, self.min_profit_ratio)
        position *= (1.0 / (1.0 + channel_width/100))  # 通道越宽，仓位越小
        
        # 根据北向资金流向调整仓位
        position *= flow_analysis['flow_impact']
        
        # 计算量价关系
        volume_price_correlation = df['Volume'].corr(df['Close'])
        volume_trend = df['Volume'].pct_change().mean()
        price_trend = df['Close'].pct_change().mean()
        
        # 计算市场环境和趋势类型
        market_env = (
            MarketEnvironment.BULL if trend_strength > 0.05 and volume_price_correlation > 0.6
            else MarketEnvironment.BEAR if trend_strength < -0.05 and volume_price_correlation < -0.6
            else MarketEnvironment.RANGE
        )
        
        trend_type = (
            TrendType.STRONG_UP if trend_strength > 0.05 and volume_trend > 0
            else TrendType.WEAK_UP if trend_strength > 0.02
            else TrendType.STRONG_DOWN if trend_strength < -0.05 and volume_trend < 0
            else TrendType.WEAK_DOWN if trend_strength < -0.02
            else TrendType.SIDEWAYS
        )
        
        return {
            'volatility_expansion': volatility,
            'cycle_resonance': resonance,
            'win_rate': win_rate,
            'suggested_position': position,
            'policy_signal': policy_analysis['pev_breakthrough'],
            'north_flow_risk': flow_analysis['liquidity_risk'],
            'liquidity_score': liquidity_score,
            'level_position': level_position,
            'trend_strength': trend_strength,
            'channel_width': channel_width,
            'volume_price_correlation': volume_price_correlation,
            'volume_trend': volume_trend,
            'price_trend': price_trend,
            'market_environment': market_env,
            'trend_type': trend_type
        }
    
    def generate_trading_signal(self, df: pd.DataFrame, symbol: str) -> Optional[MarketSignal]:
        """生成交易信号
        基于市场结构分析生成交易信号，增加多重验证机制
        """
        analysis = self.analyze_market_structure(df)
        
        # 计算信号质量分数
        signal_quality = self._calculate_signal_quality(analysis)
        
        # 计算心理状态评分
        psychological_score = self._evaluate_psychological_state(df)
        
        # 多重条件验证
        conditions = [
            analysis['volatility_expansion'] > 1.5,
            analysis['cycle_resonance'] > 0.02,
            signal_quality >= self.signal_quality_threshold,
            psychological_score >= self.psychological_threshold,
            analysis['volume_price_correlation'] >= self.volume_price_correlation_threshold,
            analysis['liquidity_score'] >= self.min_liquidity_score
        ]
        
        if all(conditions):
            signal = MarketSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                price=df['Close'].iloc[-1],
                volume=df['Volume'].iloc[-1],
                volatility=analysis['volatility_expansion'],
                trend_strength=analysis['trend_strength'],
                cycle_resonance=analysis['cycle_resonance'],
                risk_level=1 - analysis['suggested_position'],
                market_env=analysis['market_environment'],
                trend_type=analysis['trend_type'],
                psychological_score=psychological_score,
                signal_quality=signal_quality
            )
            self.signals.append(signal)
            # 保存历史信号
            new_record = {
                'timestamp': signal.timestamp,
                'symbol': signal.symbol,
                'price': signal.price,
                'volume': signal.volume,
                'volatility': signal.volatility,
                'signal_quality': signal.signal_quality
            }
            self.historical_signals = pd.concat([self.historical_signals, pd.DataFrame([new_record])], ignore_index=True)
            return signal
        
        return None
        
    def _calculate_signal_quality(self, analysis: Dict) -> float:
        """计算信号质量分数
        综合考虑多个指标评估信号的可靠性
        """
        weights = {
            'trend_strength': 0.25,
            'volume_price_correlation': 0.2,
            'cycle_resonance': 0.2,
            'volatility': 0.15,
            'liquidity': 0.1,
            'policy_impact': 0.1
        }
        
        scores = {
            'trend_strength': min(abs(analysis['trend_strength']) * 10, 1.0),
            'volume_price_correlation': abs(analysis['volume_price_correlation']),
            'cycle_resonance': min(analysis['cycle_resonance'] * 5, 1.0),
            'volatility': 1.0 if 1.2 <= analysis['volatility_expansion'] <= 2.0 else 0.5,
            'liquidity': min(analysis['liquidity_score'] / self.min_liquidity_score, 1.0),
            'policy_impact': 1.0 if analysis['policy_signal'] else 0.5
        }
        
        return sum(weights[k] * scores[k] for k in weights)
    
    def _evaluate_psychological_state(self, df: pd.DataFrame) -> float:
        """评估市场心理状态
        分析市场情绪和交易行为的理性程度
        """
        # 计算价格波动的标准差
        returns = df['Close'].pct_change()
        volatility = returns.std()
        
        # 计算成交量的稳定性
        volume_stability = 1 - df['Volume'].pct_change().std()
        
        # 计算RSI指标
        rsi = ta.RSI(df['Close'].values, timeperiod=14)[-1]
        rsi_score = 1 - abs(rsi - 50) / 50
        
        # 综合评分
        stability_score = 1 - min(volatility * 10, 1.0)  # 价格稳定性得分
        volume_score = min(max(volume_stability, 0), 1)  # 成交量稳定性得分
        
        return (stability_score * 0.4 + volume_score * 0.3 + rsi_score * 0.3)
    
    def get_trading_suggestion(self, signal: MarketSignal) -> str:
        """生成交易建议，增加多维度分析和风险控制
        优化止盈止损计算和仓位管理，提高决策精度
        """
        try:
            # 使用缓存避免重复计算
            cache_key = f"{signal.symbol}_{signal.timestamp.isoformat()}"
            if hasattr(self, '_suggestion_cache') and cache_key in self._suggestion_cache:
                return self._suggestion_cache[cache_key]
                
            # 增强的风险控制 - 多重验证
            if signal.risk_level > 0.7 or signal.signal_quality < self.signal_quality_threshold:
                result = "风险过高或信号质量不足，建议观望"
                if not hasattr(self, '_suggestion_cache'):
                    self._suggestion_cache = {}
                self._suggestion_cache[cache_key] = result
                return result
            
            # 市场环境分析 - 增加更多市场环境判断
            if signal.market_env == MarketEnvironment.BEAR and signal.trend_type in [TrendType.WEAK_DOWN, TrendType.STRONG_DOWN]:
                result = "当前处于熊市下跌趋势，建议观望或谨慎持仓"
                if not hasattr(self, '_suggestion_cache'):
                    self._suggestion_cache = {}
                self._suggestion_cache[cache_key] = result
                return result
            
            # 强信号条件（增加更多验证和精细化条件）
            strong_signal = (
                signal.trend_strength > 0.05 and
                1.2 <= signal.volatility <= 2.0 and  # 限制波动率范围
                signal.signal_quality > 0.85 and
                signal.psychological_score > 0.8 and
                signal.cycle_resonance > 0.5 and  # 要求周期共振
                (signal.market_env == MarketEnvironment.BULL or  # 优先在牛市中交易
                 (signal.market_env == MarketEnvironment.RANGE and signal.trend_type in [TrendType.WEAK_UP, TrendType.STRONG_UP]))
            )
            
            # 弱信号条件（更严格的要求和更精细的判断）
            weak_signal = (
                signal.trend_strength > 0.02 and
                1.0 <= signal.volatility <= 1.5 and
                signal.signal_quality > self.signal_quality_threshold and
                signal.psychological_score > 0.6 and
                signal.market_env != MarketEnvironment.BEAR  # 避免在熊市中产生弱信号
            )
            
            # 动态止损计算 - 使用自适应ATR倍数
            # 动态ATR倍数（波动率越大倍数越高）
            atr_multiplier = 2.0 + (signal.volatility - 1.0) * 0.5
            atr_multiplier = min(max(atr_multiplier, 1.5), 3.5)
            
            # 这里应该有更多代码...
            
        except Exception as e:
            import logging
            logging.error(f"生成交易建议时发生错误: {str(e)}")
            return "处理交易信号时发生错误，建议观望"
            
            atr = signal.volatility * signal.price * 0.01  # 估算ATR值
            base_stop_loss = signal.price - (atr_multiplier * atr)  # 基础止损位
            
            # 根据趋势强度和市场环境动态调整止损
            trend_factor = 1 + abs(signal.trend_strength)
            market_env_factor = 1.0
            if signal.market_env == MarketEnvironment.BULL:
                market_env_factor = 0.9  # 牛市中可以设置更紧的止损
            elif signal.market_env == MarketEnvironment.BEAR:
                market_env_factor = 1.2  # 熊市中需要更宽松的止损
                
            stop_loss = max(base_stop_loss * trend_factor * market_env_factor, signal.price * 0.9)  # 确保止损不超过10%
            
            # 动态计算风险收益比
            if signal.signal_quality > 0.9:
                risk_reward_ratio = 3.0  # 高质量信号使用更高的风险收益比
            elif signal.signal_quality > 0.8:
                risk_reward_ratio = 2.5
            else:
                risk_reward_ratio = 2.0  # 较低质量信号使用保守的风险收益比
                
            # 计算止盈位
            take_profit = signal.price + (signal.price - stop_loss) * risk_reward_ratio
            
            # 计算风险调整后的仓位 - 考虑更多因素
            max_risk_per_trade = 0.02  # 单次交易最大风险2%
            position_size = max_risk_per_trade / ((signal.price - stop_loss) / signal.price)
            
            # 根据市场环境和信号质量综合调整仓位
            market_factor = 1.0
            if signal.market_env == MarketEnvironment.BULL:
                market_factor = 1.2
            elif signal.market_env == MarketEnvironment.BEAR:
                market_factor = 0.7
                
            quality_factor = 0.8 + (signal.signal_quality - 0.8) * 2  # 信号质量因子，0.8-1.2范围
            
            # 生成交易建议
            if strong_signal:
                # 强信号使用更激进的仓位，但有严格限制
                position = min(position_size * market_factor * quality_factor * 1.5, self.max_position_per_stock * 100)
                result = (
                    f"强信号触发 - {signal.trend_type.value}\n"
                    f"信号质量: {signal.signal_quality:.2f}\n"
                    f"市场环境: {signal.market_env.value}\n"
                    f"建议仓位: {position:.1f}%\n"
                    f"止损价格: {stop_loss:.2f}\n"
                    f"止盈价格: {take_profit:.2f}\n"
                    f"风险提示: 建议设置移动止损，保护盈利\n"
                    f"操作建议: 分批建仓，首次建议使用{position * 0.5:.1f}%仓位，可在回调时加仓"
                )
            elif weak_signal:
                # 弱信号使用保守仓位
                position = min(position_size * market_factor * quality_factor * 0.7, self.max_position_per_stock * 50)
                result = (
                    f"弱信号触发 - {signal.trend_type.value}\n"
                    f"信号质量: {signal.signal_quality:.2f}\n"
                    f"市场环境: {signal.market_env.value}\n"
                    f"建议仓位: {position:.1f}%\n"
                    f"止损价格: {stop_loss:.2f}\n"
                    f"止盈价格: {take_profit:.2f}\n"
                    f"风险提示: 注意设置止损，控制风险\n"
                    f"操作建议: 谨慎建仓，首次建议使用{position * 0.3:.1f}%仓位，观察确认趋势后再考虑加仓"
                )
            else:
                # 无明确信号
                result = (
                    f"当前无明确信号，建议观望\n"
                    f"市场环境: {signal.market_env.value}\n"
                    f"信号质量: {signal.signal_quality:.2f}\n"
                    f"关注价格: {signal.price:.2f}\n"
                    f"支撑位: {signal.price * 0.95:.2f}\n"
                    f"阻力位: {signal.price * 1.05:.2f}\n"
                    f"操作建议: 等待更明确的市场信号出现"
                )
            
            # 缓存结果
            if not hasattr(self, '_suggestion_cache'):
                self._suggestion_cache = {}
            self._suggestion_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            import logging
            logging.getLogger('JFTradingSystem').error(f"生成交易建议时发生错误：{str(e)}")
            return "生成交易建议时发生错误，建议观望"
    
    def check_multi_cycle_resonance(self, df: pd.DataFrame) -> float:
        """增强版多周期共振检测算法
        新增MACD趋势验证和布林带宽度分析
        """
        try:
            # 使用缓存避免重复计算
            cache_key = hash(tuple(df['Close'].tail(60).values.tolist()) if 'Close' in df.columns and len(df) >= 60 else 0)
            if hasattr(self, '_resonance_cache') and cache_key in self._resonance_cache:
                return self._resonance_cache[cache_key]

            # 数据验证
            if df is None or df.empty or len(df) < 60 or 'Close' not in df.columns:
                return 0.0

            # 计算多周期EMA（新增5日、30日、60日周期）
            close_values = df['Close'].ffill().bfill().values
            periods = [5, 10, 21, 30, 55, 60]
            ema_values = {
                f'ema_{p}': ta.EMA(close_values, timeperiod=p)
                for p in periods
            }

            # 趋势排列验证（要求至少3个周期形成趋势）
            trend_counts = 0
            for i in range(2, len(periods)):
                if (df['Close'].iloc[-1] > ema_values[f'ema_{periods[i-2]}'][-1] 
                    and ema_values[f'ema_{periods[i-2]}'][-1] > ema_values[f'ema_{periods[i-1]}'][-1] 
                    and ema_values[f'ema_{periods[i-1]}'][-1] > ema_values[f'ema_{periods[i]}'][-1]):
                    trend_counts += 1
                elif (df['Close'].iloc[-1] < ema_values[f'ema_{periods[i-2]}'][-1] 
                      and ema_values[f'ema_{periods[i-2]}'][-1] < ema_values[f'ema_{periods[i-1]}'][-1] 
                      and ema_values[f'ema_{periods[i-1]}'][-1] < ema_values[f'ema_{periods[i]}'][-1]):
                    trend_counts += 1

            # MACD趋势验证
            macd, macd_signal, _ = ta.MACD(close_values)
            macd_trend = macd[-1] > macd_signal[-1] if len(macd) > 0 else False

            # 布林带宽度分析
            upper, middle, lower = ta.BBANDS(close_values)
            bb_width = (upper[-1] - lower[-1]) / middle[-1] if middle[-1] != 0 else 0

            # 综合趋势强度计算（加入波动率因子）
            trend_strength = (sum(
                (ema_values[f'ema_{p}'][-1] - ema_values[f'ema_{p*2}'][-1]) / ema_values[f'ema_{p*2}'][-1]
                for p in [5, 10, 21] if p*2 in periods
            ) / 3) * (1 + bb_width)

            # 共振条件：至少3个周期趋势一致且MACD验证通过
            result = trend_strength if trend_counts >=3 and macd_trend else 0.0
            
            # 更新缓存
            if not hasattr(self, '_resonance_cache'):
                self._resonance_cache = {}
            self._resonance_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            import logging
            logging.getLogger('JFTradingSystem').error(f"计算多周期共振时发生错误: {str(e)}")
            return 0.0
    
    def calculate_kelly_position(self, win_rate: float, profit_ratio: float) -> float:
        """使用凯利公式计算仓位
        win_rate: 胜率
        profit_ratio: 盈亏比
        """
        q = 1 - win_rate
        f = (win_rate * profit_ratio - q) / profit_ratio
        
        # 考虑风险阈值限制
        return min(max(f, 0), self.risk_threshold)
    
    def analyze_policy_impact(self, df: pd.DataFrame, policy_heat: float = 1.0) -> Dict:
        """分析政策影响
        policy_heat: 政策热度系数，默认为1.0（无影响）
        """
        # 计算政策量能指标(PEV)
        df['PEV'] = df['Volume'] * policy_heat
        df['PEV_MA20'] = df['PEV'].rolling(window=20).mean()
        
        # 计算PEV分位数
        pev_percentile = (df['PEV'].iloc[-1] - df['PEV'].min()) / (df['PEV'].max() - df['PEV'].min()) * 100
        
        # 判断是否突破90分位
        pev_breakthrough = pev_percentile > 90
        
        return {
            'pev_value': df['PEV'].iloc[-1],
            'pev_percentile': pev_percentile,
            'pev_breakthrough': pev_breakthrough
        }
    
    def analyze_northbound_flow(self, df: pd.DataFrame, north_flow: float = 0) -> Dict:
        """分析北向资金流向
        north_flow: 北向资金净流入金额（亿元）
        """
        # 计算北向资金影响系数
        flow_impact = 1 + (north_flow / 100) if abs(north_flow) <= 100 else 2 if north_flow > 0 else 0.5
        
        # 检查流动性风险（使用数值类型：2=高风险，1=中等风险，0=低风险）
        liquidity_risk = 2 if north_flow < -80 else 1 if north_flow < -40 else 0
        
        return {
            'flow_impact': flow_impact,
            'liquidity_risk': liquidity_risk
        }

    def analyze_market_structure(self, df: pd.DataFrame, policy_heat: float = 1.0, north_flow: float = 0) -> Dict:
        """分析市场结构
        整合波动率扩张、多周期共振分析、政策影响和北向资金分析
        增加市场情绪和资金流向分析
        """
        # 基础市场结构分析
        volatility = self.analyze_volatility_expansion(df)
        resonance = self.check_multi_cycle_resonance(df)
        
        # 获取3L理论指标
        liquidity_score = df['Liquidity_Score'].iloc[-1] if 'Liquidity_Score' in df.columns else 1.0
        level_position = df['Level_Position'].iloc[-1] if 'Level_Position' in df.columns else 0.0
        trend_strength = df['Trend_Strength'].iloc[-1] if 'Trend_Strength' in df.columns else 0.0
        channel_width = df['Channel_Width'].iloc[-1] if 'Channel_Width' in df.columns else 10.0
        
        # 政策影响分析
        policy_analysis = self.analyze_policy_impact(df, policy_heat)
        
        # 北向资金分析
        flow_analysis = self.analyze_northbound_flow(df, north_flow)
        
        # 市场情绪分析
        rsi = ta.RSI(df['Close'].values, timeperiod=14)[-1]
        k, d = ta.STOCH(df['High'].values, df['Low'].values, df['Close'].values,
                        fastk_period=9, slowk_period=3, slowk_matype=0,
                        slowd_period=3, slowd_matype=0)
        sentiment_score = (50 - abs(rsi - 50)) / 50  # RSI越接近50，市场情绪越稳定
        
        # 计算资金流向强度
        volume_ma = df['Volume'].rolling(window=20).mean()
        price_change = df['Close'].pct_change()
        money_flow = (price_change * df['Volume'] / volume_ma).mean()
        
        # 计算综合胜率（考虑更多因素）
        base_win_rate = 0.19 if volatility > 1.5 and resonance > 0.02 else 0.5
        liquidity_bonus = 0.1 if liquidity_score > 1.5 else 0
        level_bonus = 0.1 if abs(level_position) < 1.0 else 0
        trend_bonus = 0.1 if trend_strength > 0.01 else 0
        sentiment_bonus = 0.1 if sentiment_score > 0.7 else 0
        flow_bonus = 0.1 if money_flow > 0 and flow_analysis['flow_impact'] > 1.2 else 0
        
        win_rate = min(max(
            base_win_rate + liquidity_bonus + level_bonus + trend_bonus + sentiment_bonus + flow_bonus,
            0.1
        ), 0.9)
        
        # 计算建议仓位（考虑通道宽度）
        position = self.calculate_kelly_position(win_rate, self.min_profit_ratio)
        position *= (1.0 / (1.0 + channel_width/100))  # 通道越宽，仓位越小
        
        # 根据北向资金流向调整仓位
        position *= flow_analysis['flow_impact']
        
        # 计算量价关系
        volume_price_correlation = df['Volume'].corr(df['Close'])
        volume_trend = df['Volume'].pct_change().mean()
        price_trend = df['Close'].pct_change().mean()
        
        # 计算市场环境和趋势类型
        market_env = (
            MarketEnvironment.BULL if trend_strength > 0.05 and volume_price_correlation > 0.6
            else MarketEnvironment.BEAR if trend_strength < -0.05 and volume_price_correlation < -0.6
            else MarketEnvironment.RANGE
        )
        
        trend_type = (
            TrendType.STRONG_UP if trend_strength > 0.05 and volume_trend > 0
            else TrendType.WEAK_UP if trend_strength > 0.02
            else TrendType.STRONG_DOWN if trend_strength < -0.05 and volume_trend < 0
            else TrendType.WEAK_DOWN if trend_strength < -0.02
            else TrendType.SIDEWAYS
        )
        
        return {
            'volatility_expansion': volatility,
            'cycle_resonance': resonance,
            'win_rate': win_rate,
            'suggested_position': position,
            'policy_signal': policy_analysis['pev_breakthrough'],
            'north_flow_risk': flow_analysis['liquidity_risk'],
            'liquidity_score': liquidity_score,
            'level_position': level_position,
            'trend_strength': trend_strength,
            'channel_width': channel_width,
            'volume_price_correlation': volume_price_correlation,
            'volume_trend': volume_trend,
            'price_trend': price_trend,
            'market_environment': market_env,
            'trend_type': trend_type
        }
    
    def generate_trading_signal(self, df: pd.DataFrame, symbol: str) -> Optional[MarketSignal]:
        """生成交易信号
        基于市场结构分析生成交易信号，增加多重验证机制
        """
        analysis = self.analyze_market_structure(df)
        
        # 计算信号质量分数
        signal_quality = self._calculate_signal_quality(analysis)
        
        # 计算心理状态评分
        psychological_score = self._evaluate_psychological_state(df)
        
        # 多重条件验证
        conditions = [
            analysis['volatility_expansion'] > 1.5,
            analysis['cycle_resonance'] > 0.02,
            signal_quality >= self.signal_quality_threshold,
            psychological_score >= self.psychological_threshold,
            analysis['volume_price_correlation'] >= self.volume_price_correlation_threshold,
            analysis['liquidity_score'] >= self.min_liquidity_score
        ]
        
        if all(conditions):
            signal = MarketSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                price=df['Close'].iloc[-1],
                volume=df['Volume'].iloc[-1],
                volatility=analysis['volatility_expansion'],
                trend_strength=analysis['trend_strength'],
                cycle_resonance=analysis['cycle_resonance'],
                risk_level=1 - analysis['suggested_position'],
                market_env=analysis['market_environment'],
                trend_type=analysis['trend_type'],
                psychological_score=psychological_score,
                signal_quality=signal_quality
            )
            self.signals.append(signal)
            # 保存历史信号
            new_record = {
                'timestamp': signal.timestamp,
                'symbol': signal.symbol,
                'price': signal.price,
                'volume': signal.volume,
                'volatility': signal.volatility,
                'signal_quality': signal.signal_quality
            }
            self.historical_signals = pd.concat([self.historical_signals, pd.DataFrame([new_record])], ignore_index=True)
            return signal
        
        return None
        
    def _calculate_signal_quality(self, analysis: Dict) -> float:
        """计算信号质量分数
        综合考虑多个指标评估信号的可靠性
        """
        weights = {
            'trend_strength': 0.25,
            'volume_price_correlation': 0.2,
            'cycle_resonance': 0.2,
            'volatility': 0.15,
            'liquidity': 0.1,
            'policy_impact': 0.1
        }
        
        scores = {
            'trend_strength': min(abs(analysis['trend_strength']) * 10, 1.0),
            'volume_price_correlation': abs(analysis['volume_price_correlation']),
            'cycle_resonance': min(analysis['cycle_resonance'] * 5, 1.0),
            'volatility': 1.0 if 1.2 <= analysis['volatility_expansion'] <= 2.0 else 0.5,
            'liquidity': min(analysis['liquidity_score'] / self.min_liquidity_score, 1.0),
            'policy_impact': 1.0 if analysis['policy_signal'] else 0.5
        }
        
        return sum(weights[k] * scores[k] for k in weights)
    
    def _evaluate_psychological_state(self, df: pd.DataFrame) -> float:
        """评估市场心理状态
        分析市场情绪和交易行为的理性程度
        """
        # 计算价格波动的标准差
        returns = df['Close'].pct_change()
        volatility = returns.std()
        
        # 计算成交量的稳定性
        volume_stability = 1 - df['Volume'].pct_change().std()
        
        # 计算RSI指标
        rsi = ta.RSI(df['Close'].values, timeperiod=14)[-1]
        rsi_score = 1 - abs(rsi - 50) / 50
        
        # 综合评分
        stability_score = 1 - min(volatility * 10, 1.0)  # 价格稳定性得分
        volume_score = min(max(volume_stability, 0), 1)  # 成交量稳定性得分
        
        return (stability_score * 0.4 + volume_score * 0.3 + rsi_score * 0.3)
    
    def get_trading_suggestion(self, signal: MarketSignal) -> str:
        """生成交易建议，增加多维度分析和风险控制
        优化止盈止损计算和仓位管理，提高决策精度
        """
        try:
            # 使用缓存避免重复计算
            cache_key = f"{signal.symbol}_{signal.timestamp.isoformat()}"
            if hasattr(self, '_suggestion_cache') and cache_key in self._suggestion_cache:
                return self._suggestion_cache[cache_key]
                
            # 增强的风险控制 - 多重验证
            if signal.risk_level > 0.7 or signal.signal_quality < self.signal_quality_threshold:
                result = "风险过高或信号质量不足，建议观望"
                if not hasattr(self, '_suggestion_cache'):
                    self._suggestion_cache = {}
                self._suggestion_cache[cache_key] = result
                return result
            
            # 市场环境分析 - 增加更多市场环境判断
            if signal.market_env == MarketEnvironment.BEAR and signal.trend_type in [TrendType.WEAK_DOWN, TrendType.STRONG_DOWN]:
                result = "当前处于熊市下跌趋势，建议观望或谨慎持仓"
                if not hasattr(self, '_suggestion_cache'):
                    self._suggestion_cache = {}
                self._suggestion_cache[cache_key] = result
                return result
            
            # 强信号条件（增加更多验证和精细化条件）
            # 增强交易信号条件（新增流动性评分和市场情绪指标）
            liquidity_score = signal.liquidity_score if hasattr(signal, 'liquidity_score') else 1.0
            market_sentiment = signal.market_sentiment if hasattr(signal, 'market_sentiment') else 0.5
            
            strong_signal = (
            signal.trend_strength > 0.05
            and 1.2 <= signal.volatility <= 2.0
            and signal.signal_quality > 0.85
            and liquidity_score > self.min_liquidity_score
            and market_sentiment > 0.6
            )
            
            # 优化仓位计算（新增流动性因子）
            liquidity_factor = min(liquidity_score / self.min_liquidity_score, 2.0)
            position = min(
            position_size * market_factor * quality_factor * liquidity_factor,
            self.max_position_per_stock * 100
            )
            
            # 增强缓存机制（新增缓存有效性验证）
            if hasattr(self, '_suggestion_cache') and cache_key in self._suggestion_cache:
                cached_time = time.time() - self._suggestion_cache[cache_key]['timestamp']
                if cached_time < 3600:  # 1小时缓存有效期
                    return self._suggestion_cache[cache_key]['result']
            
            # 新增详细日志记录
            logging.info(f"生成交易建议 {cache_key}: 流动性评分={liquidity_score:.2f} 市场情绪={market_sentiment:.2f}")
            
            # 动态止损计算 - 使用自适应ATR倍数
            # 动态ATR倍数（波动率越大倍数越高）
            atr_multiplier = 2.0 + (signal.volatility - 1.0) * 0.5
            atr_multiplier = min(max(atr_multiplier, 1.5), 3.5)
            
            # 这里应该有更多代码...
            
        except Exception as e:
            import logging
            logging.error(f"生成交易建议时发生错误: {str(e)}")
            return "处理交易信号时发生错误，建议观望"