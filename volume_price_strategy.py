import pandas as pd
import numpy as np
from datetime import datetime
import logging


from lazy_analyzer import LazyStockAnalyzer
class VolumePriceStrategy:
    """体积价格分析策略
    通过分析成交量和价格的关系来识别市场趋势和交易机会
    """
    def __init__(self):
        self.logger = logging.getLogger('VolumePriceStrategy')
    
    def analyze(self, data):
        """分析股票的成交量和价格数据
        
        Args:
            data: DataFrame，包含OHLCV数据
            
        Returns:
            dict: 分析结果
        """
        try:
            results = {
                'volume_price_ratio': self._calculate_volume_price_ratio(data),
                'volume_trend': self._analyze_volume_trend(data),
                'price_volume_divergence': self._check_price_volume_divergence(data),
                'volume_breakout': self._check_volume_breakout(data),
                'accumulation_distribution': self._calculate_accumulation_distribution(data)
            }
            
            # 计算综合得分
            score = self._calculate_strategy_score(results)
            results['strategy_score'] = score
            
            return results
            
        except Exception as e:
            self.logger.error(f"分析过程中出错: {str(e)}")
            return None
    
    def _calculate_volume_price_ratio(self, data):
        """计算成交量价格比率"""
        try:
            # 计算每日成交量与价格的比率
            volume = data['成交量']
            close = data['收盘']
            vpr = volume / close
            
            # 计算移动平均
            vpr_ma5 = vpr.rolling(window=5).mean()
            vpr_ma20 = vpr.rolling(window=20).mean()
            
            return {
                'current_ratio': vpr.iloc[-1],
                'ma5': vpr_ma5.iloc[-1],
                'ma20': vpr_ma20.iloc[-1],
                'trend': 'up' if vpr_ma5.iloc[-1] > vpr_ma20.iloc[-1] else 'down'
            }
            
        except Exception as e:
            self.logger.error(f"计算成交量价格比率时出错: {str(e)}")
            return None
    
    def _analyze_volume_trend(self, data):
        """分析成交量趋势"""
        try:
            volume = data['成交量']
            close = data['收盘']
            
            # 计算成交量变化
            volume_change = volume.pct_change()
            volume_ma5 = volume.rolling(window=5).mean()
            volume_ma20 = volume.rolling(window=20).mean()
            
            # 判断成交量趋势
            recent_volume_trend = 'increasing' if volume_ma5.iloc[-1] > volume_ma20.iloc[-1] else 'decreasing'
            volume_strength = volume.iloc[-1] / volume_ma20.iloc[-1]
            
            return {
                'trend': recent_volume_trend,
                'strength': volume_strength,
                'above_ma20': volume.iloc[-1] > volume_ma20.iloc[-1],
                'volume_change': volume_change.iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"分析成交量趋势时出错: {str(e)}")
            return None
    
    def _check_price_volume_divergence(self, data):
        """检查价格和成交量背离"""
        try:
            close = data['收盘']
            volume = data['成交量']
            
            # 计算价格和成交量的变化率
            price_change = close.pct_change()
            volume_change = volume.pct_change()
            
            # 检查最近5天的背离
            divergence = {
                'exists': False,
                'type': None,
                'strength': 0
            }
            
            # 判断背离
            if price_change.iloc[-1] > 0 and volume_change.iloc[-1] < 0:
                divergence['exists'] = True
                divergence['type'] = 'negative'
                divergence['strength'] = abs(price_change.iloc[-1] - volume_change.iloc[-1])
            elif price_change.iloc[-1] < 0 and volume_change.iloc[-1] > 0:
                divergence['exists'] = True
                divergence['type'] = 'positive'
                divergence['strength'] = abs(price_change.iloc[-1] - volume_change.iloc[-1])
            
            return divergence
            
        except Exception as e:
            self.logger.error(f"检查价格成交量背离时出错: {str(e)}")
            return None
    
    def _check_volume_breakout(self, data):
        """检查成交量突破"""
        try:
            volume = data['成交量']
            volume_ma20 = volume.rolling(window=20).mean()
            volume_std = volume.rolling(window=20).std()
            
            # 计算成交量突破
            breakout = {
                'exists': False,
                'strength': 0,
                'type': None
            }
            
            # 判断是否突破2个标准差
            if volume.iloc[-1] > volume_ma20.iloc[-1] + 2 * volume_std.iloc[-1]:
                breakout['exists'] = True
                breakout['type'] = 'up'
                breakout['strength'] = (volume.iloc[-1] - volume_ma20.iloc[-1]) / volume_std.iloc[-1]
            elif volume.iloc[-1] < volume_ma20.iloc[-1] - 2 * volume_std.iloc[-1]:
                breakout['exists'] = True
                breakout['type'] = 'down'
                breakout['strength'] = (volume_ma20.iloc[-1] - volume.iloc[-1]) / volume_std.iloc[-1]
            
            return breakout
            
        except Exception as e:
            self.logger.error(f"检查成交量突破时出错: {str(e)}")
            return None
    
    def _calculate_accumulation_distribution(self, data):
        """计算积累分布指标"""
        try:
            high = data['最高']
            low = data['最低']
            close = data['收盘']
            volume = data['成交量']
            
            # 计算CLV (Close Location Value)
            clv = ((close - low) - (high - close)) / (high - low)
            clv = clv.fillna(0)
            
            # 计算A/D线
            ad = (clv * volume).cumsum()
            
            # 计算A/D线的移动平均
            ad_ma5 = ad.rolling(window=5).mean()
            ad_ma20 = ad.rolling(window=20).mean()
            
            return {
                'current': ad.iloc[-1],
                'ma5': ad_ma5.iloc[-1],
                'ma20': ad_ma20.iloc[-1],
                'trend': 'up' if ad_ma5.iloc[-1] > ad_ma20.iloc[-1] else 'down'
            }
            
        except Exception as e:
            self.logger.error(f"计算积累分布指标时出错: {str(e)}")
            return None
    
    def _calculate_strategy_score(self, results):
        """计算策略综合得分"""
        try:
            # 权重配置
            weights = {
                'volume_price_ratio': 0.25,
                'volume_trend': 0.25,
                'price_volume_divergence': 0.2,
                'volume_breakout': 0.2,
                'accumulation_distribution': 0.1
            }
            
            score = 0.0
            
            # 成交量价格比率得分
            vpr = results['volume_price_ratio']
            if vpr['trend'] == 'up':
                score += weights['volume_price_ratio'] * (vpr['current_ratio'] / vpr['ma20'])
            
            # 成交量趋势得分
            vt = results['volume_trend']
            if vt['trend'] == 'increasing':
                score += weights['volume_trend'] * vt['strength']
            
            # 价格成交量背离得分
            pvd = results['price_volume_divergence']
            if pvd['divergence_type'] == 'bullish':
                score += weights['price_volume_divergence'] * pvd['strength']
            
            # 成交量突破得分
            vb = results['volume_breakout']
            if vb['breakout']:
                score += weights['volume_breakout'] * vb['strength']
            
            # 累积分布得分
            ad = results['accumulation_distribution']
            if ad['trend'] == 'accumulation':
                score += weights['accumulation_distribution'] * ad['strength']
            
            # 市场环境调整
            market_condition = self._analyze_market_condition()
            score *= market_condition['adjustment_factor']
            
            return {
                'total_score': round(score, 2),
                'signal_quality': 'high' if score > 0.7 else 'medium' if score > 0.4 else 'low',
                'market_condition': market_condition['status'],
                'confidence_level': round(min(score * 100, 100), 1)
            }
            
        except Exception as e:
            self.logger.error(f"计算策略得分时出错: {str(e)}")
            return None
    
    def _analyze_market_condition(self):
        """分析市场环境"""
        try:
            # 这里可以添加更多市场环境分析指标
            market_status = 'neutral'  # 可以是bullish, bearish, neutral
            adjustment_factor = 1.0
            
            return {
                'status': market_status,
                'adjustment_factor': adjustment_factor
            }
        except Exception as e:
            self.logger.error(f"分析市场环境时出错: {str(e)}")
            return {'status': 'unknown', 'adjustment_factor': 1.0}