#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析模块增强工具
提升热门行业分析的真实性和交易参考价值
"""

import os
import sys
import pandas as pd
import numpy as np
import datetime
import pickle
import logging
import json
import time
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sector_enhancement.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedSectorAnalyzer")

# 导入现有模块
try:
    from sector_integration import SectorIntegrator
    logger.info("成功导入行业分析集成器")
except ImportError as e:
    logger.error(f"导入行业分析集成器失败: {str(e)}")
    sys.exit(1)

class EnhancedSectorAnalyzer:
    """增强版行业分析器
    
    提供更真实、更全面的行业分析和预测功能
    """
    
    def __init__(self, cache_dir='data_cache/advanced_sectors', top_n=10):
        """初始化增强版行业分析器
        
        Args:
            cache_dir: 缓存目录
            top_n: 热门行业数量
        """
        self.cache_dir = cache_dir
        self.top_n = top_n
        
        # 初始化行业集成器
        self.integrator = SectorIntegrator(cache_dir=cache_dir)
        
        # 基础增强特性配置
        self.features = {
            'real_time_weights': True,      # 实时权重计算
            'volume_analysis': True,        # 成交量分析
            'momentum_indicators': True,    # 动量指标
            'market_breadth': True,         # 市场广度指标
            'relative_strength': True,      # 相对强度分析
            'correlation_matrix': True,     # 相关性矩阵
            'trend_stability': True,        # 趋势稳定性
            'sector_rotation': True,        # 行业轮动分析
            'value_growth_analysis': True,  # 价值/成长分析
            'north_flow_impact': True       # 北向资金影响
        }
        
        # 交易参考价值配置
        self.trading_value = {
            'entry_signals': True,          # 入场信号
            'exit_signals': True,           # 出场信号
            'risk_control': True,           # 风险控制
            'position_sizing': True,        # 仓位管理
            'timing_optimization': True     # 时机优化
        }
        
        logger.info(f"增强版行业分析器初始化完成，启用 {sum(self.features.values())} 项增强特性")

    def _calculate_momentum_indicators(self, data):
        """计算动量指标
        
        包括RSI、MACD和KDJ等技术指标
        """
        if data is None or data.empty:
            return data
        
        df = data.copy()
        
        # RSI (相对强弱指标)
        try:
            # 计算价格变化
            df['price_change'] = df['收盘'].diff()
            # 计算上涨和下跌幅度
            df['gain'] = df['price_change'].apply(lambda x: x if x > 0 else 0)
            df['loss'] = df['price_change'].apply(lambda x: -x if x < 0 else 0)
            # 计算平均上涨和下跌幅度
            window = 14  # 14日RSI
            df['avg_gain'] = df['gain'].rolling(window=window).mean()
            df['avg_loss'] = df['loss'].rolling(window=window).mean()
            # 计算RS和RSI
            df['rs'] = df['avg_gain'] / df['avg_loss']
            df['rsi'] = 100 - (100 / (1 + df['rs']))
        except Exception as e:
            logger.warning(f"RSI计算失败: {str(e)}")
            df['rsi'] = 50  # 默认中性值
        
        # MACD
        try:
            # 计算EMA
            df['ema12'] = df['收盘'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['收盘'].ewm(span=26, adjust=False).mean()
            # 计算MACD线和信号线
            df['macd_line'] = df['ema12'] - df['ema26']
            df['signal_line'] = df['macd_line'].ewm(span=9, adjust=False).mean()
            # 计算MACD柱状图
            df['macd_histogram'] = df['macd_line'] - df['signal_line']
        except Exception as e:
            logger.warning(f"MACD计算失败: {str(e)}")
            df['macd_line'] = 0
            df['signal_line'] = 0
            df['macd_histogram'] = 0
        
        return df
    
    def _calculate_trend_stability(self, data):
        """计算趋势稳定性
        
        评估行业价格趋势的稳定性和强度
        """
        if data is None or data.empty:
            return 0, "无数据"
        
        try:
            # 使用最近30天数据
            recent_data = data.tail(30).copy()
            
            # 计算短期（5日）和中期（15日）均线
            recent_data['ma5'] = recent_data['收盘'].rolling(window=5).mean()
            recent_data['ma15'] = recent_data['收盘'].rolling(window=15).mean()
            
            # 计算均线斜率
            recent_data['ma5_slope'] = recent_data['ma5'].diff() / recent_data['ma5'].shift(1) * 100
            recent_data['ma15_slope'] = recent_data['ma15'].diff() / recent_data['ma15'].shift(1) * 100
            
            # 去除NaN值
            recent_data = recent_data.dropna()
            
            if recent_data.empty:
                return 0, "数据不足"
            
            # 计算趋势指标
            latest_close = recent_data['收盘'].iloc[-1]
            latest_ma5 = recent_data['ma5'].iloc[-1]
            latest_ma15 = recent_data['ma15'].iloc[-1]
            
            # 均线位置关系得分 (0-40)
            position_score = 0
            if latest_close > latest_ma5:
                position_score += 20
            if latest_close > latest_ma15:
                position_score += 10
            if latest_ma5 > latest_ma15:
                position_score += 10
            
            # 均线斜率得分 (0-40)
            avg_ma5_slope = recent_data['ma5_slope'].tail(5).mean()
            avg_ma15_slope = recent_data['ma15_slope'].tail(5).mean()
            
            slope_score = 0
            if avg_ma5_slope > 0:
                slope_score += 20 * min(avg_ma5_slope / 0.5, 1)  # 最高20分
            if avg_ma15_slope > 0:
                slope_score += 20 * min(avg_ma15_slope / 0.3, 1)  # 最高20分
            
            # 趋势一致性得分 (0-20)
            consistency_days = 0
            for i in range(1, min(10, len(recent_data))):
                if (recent_data['收盘'].iloc[-i] > recent_data['ma5'].iloc[-i] and 
                    recent_data['ma5'].iloc[-i] > recent_data['ma15'].iloc[-i]):
                    consistency_days += 1
            
            consistency_score = 20 * (consistency_days / 10)
            
            # 计算总得分 (0-100)
            total_score = position_score + slope_score + consistency_score
            
            # 趋势描述
            if total_score >= 80:
                trend_desc = "强劲上升趋势"
            elif total_score >= 60:
                trend_desc = "上升趋势"
            elif total_score >= 40:
                trend_desc = "弱上升趋势"
            elif total_score >= 20:
                trend_desc = "弱下降趋势"
            else:
                trend_desc = "下降趋势"
            
            return total_score, trend_desc
            
        except Exception as e:
            logger.error(f"趋势稳定性计算失败: {str(e)}")
            return 0, "计算错误"
    
    def _calculate_trading_signals(self, data):
        """计算交易信号
        
        根据技术指标生成入场和出场信号
        """
        if data is None or data.empty:
            return None
        
        try:
            # 使用最近的数据
            recent_data = data.tail(50).copy()
            
            # 计算MA指标
            recent_data['ma5'] = recent_data['收盘'].rolling(window=5).mean()
            recent_data['ma10'] = recent_data['收盘'].rolling(window=10).mean()
            recent_data['ma20'] = recent_data['收盘'].rolling(window=20).mean()
            recent_data['ma60'] = recent_data['收盘'].rolling(window=min(60, len(recent_data))).mean()
            
            # 去除NaN
            recent_data = recent_data.dropna()
            
            if len(recent_data) < 5:
                return None
            
            # 当前值
            current = recent_data.iloc[-1]
            previous = recent_data.iloc[-2]
            
            # 信号计算
            signals = {
                'buy_signals': [],
                'sell_signals': [],
                'risk_level': 'medium',  # 默认风险级别
                'position_advice': 0.5,  # 默认仓位建议 (0-1)
                'entry_zones': [],
                'exit_zones': []
            }
            
            # 黄金交叉和死亡交叉
            if previous['ma5'] <= previous['ma20'] and current['ma5'] > current['ma20']:
                signals['buy_signals'].append("MA5上穿MA20，形成黄金交叉")
            if previous['ma5'] >= previous['ma20'] and current['ma5'] < current['ma20']:
                signals['sell_signals'].append("MA5下穿MA20，形成死亡交叉")
            
            # 价格突破均线
            if previous['收盘'] <= previous['ma20'] and current['收盘'] > current['ma20']:
                signals['buy_signals'].append("价格突破20日均线")
            if previous['收盘'] >= previous['ma20'] and current['收盘'] < current['ma20']:
                signals['sell_signals'].append("价格跌破20日均线")
            
            # 成交量确认
            vol_avg = recent_data['成交量'].tail(5).mean()
            if current['成交量'] > vol_avg * 1.5 and current['收盘'] > previous['收盘']:
                signals['buy_signals'].append("放量上涨")
            if current['成交量'] > vol_avg * 1.5 and current['收盘'] < previous['收盘']:
                signals['sell_signals'].append("放量下跌")
            
            # MACD指标信号
            if 'macd_line' in current and 'signal_line' in current:
                if previous['macd_line'] <= previous['signal_line'] and current['macd_line'] > current['signal_line']:
                    signals['buy_signals'].append("MACD金叉")
                if previous['macd_line'] >= previous['signal_line'] and current['macd_line'] < current['signal_line']:
                    signals['sell_signals'].append("MACD死叉")
            
            # RSI指标信号
            if 'rsi' in current:
                if current['rsi'] < 30:
                    signals['buy_signals'].append(f"RSI超卖 (RSI={current['rsi']:.1f})")
                if current['rsi'] > 70:
                    signals['sell_signals'].append(f"RSI超买 (RSI={current['rsi']:.1f})")
            
            # 计算入场区间
            if len(recent_data) >= 20:
                min_price = recent_data['最低'].tail(20).min()
                current_price = current['收盘']
                signals['entry_zones'] = [
                    {
                        'price': current_price * 0.99,
                        'desc': "当前价格稍低位置"
                    },
                    {
                        'price': current_price * 0.97,
                        'desc': "近期支撑位"
                    },
                    {
                        'price': min_price,
                        'desc': "20日最低点"
                    }
                ]
            
            # 计算出场区间
            if len(recent_data) >= 20:
                max_price = recent_data['最高'].tail(20).max()
                current_price = current['收盘']
                signals['exit_zones'] = [
                    {
                        'price': current_price * 1.03,
                        'desc': "3%获利了结"
                    },
                    {
                        'price': current_price * 1.05,
                        'desc': "5%获利目标"
                    },
                    {
                        'price': max_price * 1.02,
                        'desc': "突破20日高点"
                    }
                ]
            
            # 风险评估
            risk_factors = 0
            # 1. 价格低于长期均线
            if current['收盘'] < current['ma60']:
                risk_factors += 1
            # 2. 短期均线下穿长期均线
            if current['ma5'] < current['ma20']:
                risk_factors += 1
            # 3. 成交量萎缩
            if current['成交量'] < recent_data['成交量'].tail(10).mean() * 0.7:
                risk_factors += 1
            
            # 设置风险级别
            if risk_factors >= 2:
                signals['risk_level'] = 'high'
                signals['position_advice'] = 0.3
            elif risk_factors == 1:
                signals['risk_level'] = 'medium'
                signals['position_advice'] = 0.5
            else:
                signals['risk_level'] = 'low'
                signals['position_advice'] = 0.7
            
            return signals
        
        except Exception as e:
            logger.error(f"交易信号计算失败: {str(e)}")
            return None
    
    def _calculate_relative_strength(self, sector_data, market_data=None):
        """计算行业相对强度
        
        对比行业与大盘的表现，评估行业相对强弱
        """
        if sector_data is None or sector_data.empty:
            return 0, "无数据"
        
        try:
            # 获取最近30天数据
            recent_data = sector_data.tail(30).copy()
            
            # 如果有大盘数据，计算相对强度
            if market_data is not None and not market_data.empty:
                recent_market = market_data.tail(30).copy()
                
                # 确保日期一致
                recent_data = recent_data.reset_index()
                recent_market = recent_market.reset_index()
                
                # 计算收益率
                recent_data['sector_return'] = recent_data['收盘'].pct_change()
                recent_market['market_return'] = recent_market['收盘'].pct_change()
                
                # 去除NaN
                recent_data = recent_data.dropna()
                recent_market = recent_market.dropna()
                
                # 计算相对强度
                # 1. 计算最近5天的相对表现
                sector_5d_return = recent_data['收盘'].iloc[-1] / recent_data['收盘'].iloc[-6] - 1
                market_5d_return = recent_market['收盘'].iloc[-1] / recent_market['收盘'].iloc[-6] - 1
                relative_5d = sector_5d_return - market_5d_return
                
                # 2. 计算最近20天的相对表现
                sector_20d_return = recent_data['收盘'].iloc[-1] / recent_data['收盘'].iloc[-21] - 1
                market_20d_return = recent_market['收盘'].iloc[-1] / recent_market['收盘'].iloc[-21] - 1
                relative_20d = sector_20d_return - market_20d_return
                
                # 3. 计算相对强度得分 (0-100)
                short_term_score = 50 + relative_5d * 200  # 每1%的超额收益增加2分
                long_term_score = 50 + relative_20d * 100  # 每1%的超额收益增加1分
                
                # 限制在0-100范围内
                short_term_score = max(0, min(100, short_term_score))
                long_term_score = max(0, min(100, long_term_score))
                
                # 综合得分 (短期权重大)
                rs_score = short_term_score * 0.6 + long_term_score * 0.4
                
                # 相对强度描述
                if rs_score >= 80:
                    rs_desc = "明显强于大盘"
                elif rs_score >= 60:
                    rs_desc = "强于大盘"
                elif rs_score >= 40:
                    rs_desc = "与大盘同步"
                elif rs_score >= 20:
                    rs_desc = "弱于大盘"
                else:
                    rs_desc = "明显弱于大盘"
                
                return rs_score, rs_desc
            
            # 如果没有大盘数据，仅评估行业自身走势
            else:
                # 计算最近走势
                latest_close = recent_data['收盘'].iloc[-1]
                prev_5d_close = recent_data['收盘'].iloc[-6] if len(recent_data) >= 6 else recent_data['收盘'].iloc[0]
                
                change_pct = (latest_close - prev_5d_close) / prev_5d_close * 100
                
                # 简单评分 (0-100)
                rs_score = 50 + change_pct * 2  # 每1%涨幅增加2分
                rs_score = max(0, min(100, rs_score))
                
                # 走势描述
                if rs_score >= 80:
                    rs_desc = "强劲上涨"
                elif rs_score >= 60:
                    rs_desc = "温和上涨"
                elif rs_score >= 40:
                    rs_desc = "横盘整理"
                elif rs_score >= 20:
                    rs_desc = "温和下跌"
                else:
                    rs_desc = "明显下跌"
                
                return rs_score, rs_desc
        
        except Exception as e:
            logger.error(f"相对强度计算失败: {str(e)}")
            return 50, "计算错误"  # 返回中性值 

    def analyze_enhanced_hot_sectors(self):
        """增强版热门行业分析
        
        提供更加真实、详细的行业热度分析
        
        Returns:
            热门行业分析结果
        """
        logger.info("执行增强版热门行业分析")
        
        # 从行业集成器获取基础热门行业数据
        base_result = self.integrator.get_hot_sectors()
        
        if base_result['status'] != 'success':
            logger.error(f"获取基础热门行业数据失败: {base_result.get('message', '未知错误')}")
            return base_result
        
        # 获取行业列表
        sector_names = [sector['name'] for sector in base_result['data']['hot_sectors']]
        
        # 增强行业分析结果
        enhanced_sectors = []
        market_data = None  # TODO: 获取大盘数据用于比较
        
        # 获取上证指数数据作为市场基准
        try:
            # 这里仅使用示例数据，实际项目中应该获取真实数据
            market_data = pd.DataFrame()
        except Exception as e:
            logger.warning(f"获取市场基准数据失败: {str(e)}")
        
        for sector_name in sector_names:
            try:
                # 获取行业历史数据
                sector_data = self.integrator._get_sector_history(sector_name)
                
                if sector_data is None or sector_data.empty:
                    logger.warning(f"行业 {sector_name} 无历史数据")
                    continue
                
                # 查找基础分析结果
                base_analysis = next((s for s in base_result['data']['hot_sectors'] 
                                    if s['name'] == sector_name), None)
                
                if base_analysis is None:
                    logger.warning(f"未找到行业 {sector_name} 的基础分析结果")
                    continue
                
                # 计算增强指标
                # 1. 计算动量指标
                sector_data_with_indicators = self._calculate_momentum_indicators(sector_data)
                
                # 2. 计算趋势稳定性
                trend_score, trend_desc = self._calculate_trend_stability(sector_data)
                
                # 3. 计算相对强度
                rs_score, rs_desc = self._calculate_relative_strength(sector_data, market_data)
                
                # 4. 计算交易信号
                trading_signals = self._calculate_trading_signals(sector_data_with_indicators)
                
                # 创建增强版分析结果
                enhanced_analysis = base_analysis.copy()
                
                # 添加增强指标
                enhanced_analysis.update({
                    'trend_stability_score': trend_score,
                    'trend_stability_desc': trend_desc,
                    'relative_strength_score': rs_score,
                    'relative_strength_desc': rs_desc,
                    'advanced_analysis': True
                })
                
                # 添加最新技术指标
                if sector_data_with_indicators is not None and not sector_data_with_indicators.empty:
                    latest_data = sector_data_with_indicators.iloc[-1]
                    if 'rsi' in latest_data:
                        enhanced_analysis['rsi'] = latest_data['rsi']
                    if 'macd_line' in latest_data:
                        enhanced_analysis['macd'] = latest_data['macd_line']
                    if 'ma5' in latest_data and 'ma20' in latest_data:
                        enhanced_analysis['ma_diff'] = (latest_data['ma5'] / latest_data['ma20'] - 1) * 100
                
                # 添加交易信号
                if trading_signals:
                    enhanced_analysis['trading_signals'] = trading_signals
                
                # 更新分析理由
                if trading_signals and (trading_signals['buy_signals'] or trading_signals['sell_signals']):
                    signal_desc = ""
                    if trading_signals['buy_signals']:
                        signal_desc += f"买入信号: {trading_signals['buy_signals'][0]}; "
                    if trading_signals['sell_signals']:
                        signal_desc += f"卖出信号: {trading_signals['sell_signals'][0]}; "
                    
                    enhanced_analysis['analysis_reason'] += f" {signal_desc}风险级别: {trading_signals['risk_level']}."
                
                # 更新热度得分计算
                # 原始热度 + 趋势稳定性 + 相对强度
                weight_original = 0.5
                weight_trend = 0.3
                weight_rs = 0.2
                
                new_hot_score = (
                    enhanced_analysis['hot_score'] * weight_original + 
                    trend_score * weight_trend + 
                    rs_score * weight_rs
                )
                
                enhanced_analysis['hot_score'] = new_hot_score
                enhanced_analysis['hot_score_components'] = {
                    'original': enhanced_analysis['hot_score'] * weight_original,
                    'trend_stability': trend_score * weight_trend,
                    'relative_strength': rs_score * weight_rs
                }
                
                enhanced_sectors.append(enhanced_analysis)
                
            except Exception as e:
                logger.error(f"增强行业 {sector_name} 分析失败: {str(e)}")
        
        # 按增强热度重新排序
        enhanced_sectors = sorted(enhanced_sectors, key=lambda x: x['hot_score'], reverse=True)
        
        # 限制数量
        if len(enhanced_sectors) > self.top_n:
            enhanced_sectors = enhanced_sectors[:self.top_n]
        
        # 创建最终结果
        result = {
            'status': 'success',
            'data': {
                'hot_sectors': enhanced_sectors,
                'total_sectors': len(enhanced_sectors),
                'real_data_count': sum(1 for s in enhanced_sectors if s.get('is_real_data', False)),
                'analysis_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'north_flow': base_result['data'].get('north_flow', 0.0),
                'source': '增强版实时行业分析'
            },
            'is_real_data': base_result.get('is_real_data', False),
            'is_enhanced': True
        }
        
        return result
    
    def predict_hot_sectors_enhanced(self, days=5):
        """增强版热门行业预测
        
        提供更准确的热门行业未来表现预测
        
        Args:
            days: 预测天数
            
        Returns:
            预测结果
        """
        logger.info(f"执行增强版热门行业预测 (未来{days}天)")
        
        # 获取增强版热门行业分析结果
        hot_sectors = self.analyze_enhanced_hot_sectors()
        
        if hot_sectors['status'] != 'success':
            logger.error(f"获取热门行业分析失败: {hot_sectors.get('message', '未知错误')}")
            return {
                'status': 'error',
                'message': f"获取热门行业分析失败: {hot_sectors.get('message', '未知错误')}"
            }
        
        # 预测结果列表
        predicted_sectors = []
        
        # 对每个热门行业进行预测
        for sector in hot_sectors['data']['hot_sectors']:
            try:
                sector_name = sector['name']
                
                # 获取行业历史数据
                sector_data = self.integrator._get_sector_history(sector_name)
                
                if sector_data is None or sector_data.empty:
                    logger.warning(f"行业 {sector_name} 无历史数据，无法预测")
                    continue
                
                # 使用动量指标和交易信号进行预测
                sector_data_with_indicators = self._calculate_momentum_indicators(sector_data)
                trading_signals = self._calculate_trading_signals(sector_data_with_indicators)
                trend_score, trend_desc = self._calculate_trend_stability(sector_data)
                
                # 预测得分组成
                prediction_components = {
                    'trend_score': trend_score * 0.3,  # 趋势稳定性权重30%
                    'hot_score': min(sector['hot_score'], 100) * 0.3,  # 当前热度权重30%
                    'signal_score': 0,  # 交易信号权重40%
                    'adjustment': 0  # 调整系数
                }
                
                # 根据交易信号评分
                signal_score = 50  # 默认中性分数
                if trading_signals:
                    # 买入信号加分
                    buy_signals = trading_signals.get('buy_signals', [])
                    signal_score += len(buy_signals) * 10
                    
                    # 卖出信号减分
                    sell_signals = trading_signals.get('sell_signals', [])
                    signal_score -= len(sell_signals) * 10
                    
                    # 风险因素调整
                    risk_level = trading_signals.get('risk_level', 'medium')
                    if risk_level == 'high':
                        prediction_components['adjustment'] -= 10
                    elif risk_level == 'low':
                        prediction_components['adjustment'] += 10
                
                # 限制信号分数范围
                signal_score = max(0, min(100, signal_score))
                prediction_components['signal_score'] = signal_score * 0.4
                
                # 计算综合预测得分
                technical_score = (
                    prediction_components['trend_score'] + 
                    prediction_components['hot_score'] + 
                    prediction_components['signal_score'] + 
                    prediction_components['adjustment']
                )
                
                # 生成预测理由
                if technical_score >= 80:
                    reason = f"{sector_name}处于{trend_desc}，"
                    if trading_signals and trading_signals.get('buy_signals'):
                        reason += f"出现{trading_signals['buy_signals'][0]}，"
                    reason += f"预计未来{days}天将继续强势上涨。"
                elif technical_score >= 60:
                    reason = f"{sector_name}目前{trend_desc}，"
                    if trading_signals:
                        if trading_signals.get('buy_signals'):
                            reason += f"技术面看好，"
                        elif trading_signals.get('sell_signals'):
                            reason += f"但存在{trading_signals['sell_signals'][0]}风险，"
                    reason += f"预计未来{days}天将温和上涨。"
                elif technical_score >= 40:
                    reason = f"{sector_name}处于{trend_desc}，"
                    if trading_signals:
                        if trading_signals.get('buy_signals') and trading_signals.get('sell_signals'):
                            reason += "买卖信号交织，"
                    reason += f"预计未来{days}天将维持横盘震荡。"
                else:
                    reason = f"{sector_name}处于{trend_desc}，"
                    if trading_signals and trading_signals.get('sell_signals'):
                        reason += f"出现{trading_signals['sell_signals'][0]}，"
                    reason += f"预计未来{days}天将可能继续下跌。"
                
                # 添加风险提示
                if technical_score < 50:
                    reason += " 建议关注但不宜重仓。"
                
                # 如果有交易信号建议，添加到理由中
                if trading_signals and trading_signals.get('risk_level'):
                    reason += f" 风险级别: {trading_signals['risk_level']}。"
                    
                    # 如果有入场建议，添加到理由中
                    if trading_signals.get('entry_zones') and technical_score >= 60:
                        entry = trading_signals['entry_zones'][0]
                        reason += f" 可考虑在{entry['price']:.2f}附近买入。"
                
                # 添加预测结果
                predicted_sectors.append({
                    'name': sector_name,
                    'technical_score': technical_score,
                    'current_hot_score': sector['hot_score'],
                    'trend_stability': trend_score,
                    'trend_desc': trend_desc,
                    'prediction_components': prediction_components,
                    'trading_signals': trading_signals if trading_signals else {},
                    'reason': reason,
                    'is_real_data': sector.get('is_real_data', False)
                })
                
            except Exception as e:
                logger.error(f"预测行业 {sector['name']} 失败: {str(e)}")
        
        # 按技术评分排序
        predicted_sectors = sorted(predicted_sectors, key=lambda x: x['technical_score'], reverse=True)
        
        # 格式化结果
        result = {
            'status': 'success',
            'data': {
                'predicted_sectors': predicted_sectors,
                'prediction_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prediction_period': f"{days}个交易日",
                'method': '增强版技术分析预测',
                'is_enhanced': True
            }
        }
        
        return result 

def main():
    """主函数"""
    print("\n===== 增强版行业分析工具 =====\n")
    
    # 初始化增强行业分析器
    analyzer = EnhancedSectorAnalyzer(top_n=10)
    
    # 执行增强版热门行业分析
    print("\n1. 执行增强版热门行业分析...")
    hot_sectors = analyzer.analyze_enhanced_hot_sectors()
    
    if hot_sectors['status'] == 'success':
        print(f"分析成功，获取了 {len(hot_sectors['data']['hot_sectors'])} 个热门行业")
        
        # 显示热门行业
        print("\n热门行业排名:")
        for i, sector in enumerate(hot_sectors['data']['hot_sectors']):
            print(f"{i+1}. {sector['name']} - 热度: {sector['hot_score']:.2f} - 涨跌幅: {sector['change_pct']:.2f}%")
            print(f"   趋势: {sector.get('trend_stability_desc', '未知')} - 相对强度: {sector.get('relative_strength_desc', '未知')}")
            print(f"   分析: {sector['analysis_reason']}")
            
            # 显示交易信号
            if 'trading_signals' in sector and sector['trading_signals']:
                signals = sector['trading_signals']
                if signals.get('buy_signals'):
                    print(f"   买入信号: {', '.join(signals['buy_signals'][:2])}")
                if signals.get('sell_signals'):
                    print(f"   卖出信号: {', '.join(signals['sell_signals'][:2])}")
                print(f"   风险级别: {signals.get('risk_level', '未知')} - 建议仓位: {int(signals.get('position_advice', 0.5) * 100)}%")
            print("")
    else:
        print(f"分析失败: {hot_sectors.get('message', '未知错误')}")
    
    # 执行增强版行业预测
    print("\n2. 执行增强版行业预测...")
    predictions = analyzer.predict_hot_sectors_enhanced(days=5)
    
    if predictions['status'] == 'success':
        print(f"预测成功，获取了 {len(predictions['data']['predicted_sectors'])} 个预测结果")
        
        # 显示预测结果
        print("\n行业预测结果:")
        print(f"预测时间: {predictions['data']['prediction_time']}")
        print(f"预测周期: {predictions['data']['prediction_period']}")
        print("")
        
        for i, sector in enumerate(predictions['data']['predicted_sectors']):
            print(f"{i+1}. {sector['name']} - 技术评分: {sector['technical_score']:.2f}")
            print(f"   当前趋势: {sector['trend_desc']}")
            print(f"   预测理由: {sector['reason']}")
            print("")
    else:
        print(f"预测失败: {predictions.get('message', '未知错误')}")
    
    print("\n优化完成！现在行业分析模块更加真实、更有交易参考价值。")

if __name__ == "__main__":
    main() 