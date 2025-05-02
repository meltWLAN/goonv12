#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试增强型行业分析器V2
演示升级后的热门行业分析功能
"""

import logging
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pprint import pprint

# 导入V1版本作为基础
from enhanced_sector_analyzer import EnhancedSectorAnalyzer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_enhanced_sector_v2")

def test_sector_analysis():
    """测试V2版本的热门行业功能增强"""
    logger.info("开始测试V2行业分析器升级功能")
    
    # 使用V1版本获取基础数据
    base_analyzer = EnhancedSectorAnalyzer(top_n=10)
    
    logger.info("开始获取行业列表数据...")
    sectors = base_analyzer.get_sector_list()
    if not sectors:
        logger.error("获取行业列表失败，请检查网络或API接口")
        return
    
    logger.info(f"成功获取行业列表: {len(sectors)}个")
    
    # 测试V2的核心功能增强
    test_v2_enhancements(sectors)

def test_v2_enhancements(sectors):
    """测试V2版本的增强功能"""
    
    logger.info("==== V2核心功能增强演示 ====")
    
    # 1. 技术指标计算增强
    logger.info("1. 技术指标计算增强")
    
    # 选择一个示例行业
    sample_sector = sectors[0]
    logger.info(f"选择示例行业: {sample_sector['name']}")
    
    # 获取行业历史数据
    history_data = pd.DataFrame()
    try:
        import akshare as ak
        history_data = ak.stock_board_industry_hist_em(symbol=sample_sector['name'])
        logger.info(f"获取行业历史数据成功: {len(history_data)}行")
    except Exception as e:
        logger.error(f"获取行业历史数据失败: {e}")
        # 生成模拟数据用于演示
        dates = pd.date_range(end=datetime.now(), periods=60)
        history_data = pd.DataFrame({
            '日期': dates,
            '开盘': np.random.normal(100, 5, 60),
            '收盘': np.random.normal(100, 5, 60),
            '最高': np.random.normal(105, 5, 60),
            '最低': np.random.normal(95, 5, 60),
            '成交量': np.random.normal(1000000, 500000, 60),
        })
        
    # 演示技术指标计算
    tech_indicators = calculate_enhanced_indicators(history_data)
    logger.info("增强型技术指标计算结果:")
    pprint(tech_indicators)
    
    # 2. 自适应权重模型演示
    logger.info("\n2. 自适应权重模型")
    
    # 模拟不同市场情绪下的权重调整
    bullish_market = {'market_sentiment': 80, 'volatility': 15, 'north_flow': 60}
    bearish_market = {'market_sentiment': 20, 'volatility': 25, 'north_flow': -50}
    
    logger.info("强势市场下的自适应权重:")
    bullish_weights = calculate_adaptive_weights(bullish_market)
    pprint(bullish_weights)
    
    logger.info("弱势市场下的自适应权重:")
    bearish_weights = calculate_adaptive_weights(bearish_market)
    pprint(bearish_weights)
    
    # 3. 行业热度评分演示
    logger.info("\n3. 增强型行业热度评分")
    
    # 选择几个示例行业进行热度计算
    sample_sectors = sectors[:5]
    enhanced_scores = calculate_enhanced_hot_scores(sample_sectors, bullish_weights)
    
    # 输出热度评分结果
    logger.info("行业热度评分结果(按分数排序):")
    for sector in sorted(enhanced_scores, key=lambda x: x['hot_score'], reverse=True):
        logger.info(f"{sector['name']} - 热度: {sector['hot_score']:.2f} - 等级: {sector['hot_level']} - 理由: {sector['analysis_reason']}")
    
def calculate_enhanced_indicators(data):
    """计算增强型技术指标 (V2功能演示)"""
    try:
        # 标准化列名
        if '日期' in data.columns:
            data = data.sort_values('日期')
        elif 'date' in data.columns:
            data = data.sort_values('date')
            
        price_col = '收盘' if '收盘' in data.columns else 'close'
        volume_col = '成交量' if '成交量' in data.columns else 'volume'
        
        if price_col not in data.columns or len(data) < 30:
            return {'tech_score': 50}
            
        prices = data[price_col].values
        volumes = data[volume_col].values if volume_col in data.columns else np.ones_like(prices)
        
        # 简化技术指标计算
        # 实际V2版本应使用talib或自定义计算
        
        # 计算RSI
        delta = np.diff(prices)
        delta = np.insert(delta, 0, 0)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.mean(gain[-14:])
        avg_loss = np.mean(loss[-14:])
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 9999
        rsi = 100 - (100 / (1 + rs))
        
        # 计算均线趋势
        ma5 = np.mean(prices[-5:])
        ma20 = np.mean(prices[-20:])
        
        if ma5 > ma20 and prices[-1] > ma5:
            ma_trend = 1  # 均线向上
        elif ma5 < ma20 and prices[-1] < ma5:
            ma_trend = -1  # 均线向下
        else:
            ma_trend = 0  # 盘整
            
        # 计算成交量趋势
        vol_ma5 = np.mean(volumes[-5:])
        vol_ma20 = np.mean(volumes[-20:])
        
        vol_trend = 1 if vol_ma5 > vol_ma20 * 1.1 else -1 if vol_ma5 < vol_ma20 * 0.9 else 0
        
        # 计算综合技术得分
        tech_score = 50  # 基准分
        
        if prices[-1] > ma20:
            tech_score += 15  # 站上20日均线
        if ma5 > ma20:
            tech_score += 10  # 5日均线在20日均线上方
            
        if rsi > 70:
            tech_score -= 10  # RSI超买
        elif rsi < 30:
            tech_score += 15  # RSI超卖
            
        tech_score += vol_trend * 5
        
        # 限制得分范围
        tech_score = max(0, min(100, tech_score))
        
        return {
            'rsi': rsi,
            'ma_trend': ma_trend,
            'volume_trend': vol_trend,
            'tech_score': tech_score
        }
        
    except Exception as e:
        logger.error(f"计算技术指标失败: {e}")
        return {'tech_score': 50}

def calculate_adaptive_weights(market_data):
    """计算自适应权重 (V2功能演示)"""
    try:
        # 默认权重
        weights = {
            'change_pct': 0.25,  # 涨跌幅
            'volume': 0.20,      # 成交量
            'fund_flow': 0.20,   # 资金流向
            'north_flow': 0.15,  # 北向资金
            'technical': 0.20    # 技术指标
        }
        
        # 获取市场情绪和波动性
        market_sentiment = market_data.get('market_sentiment', 50)  # 50为中性
        volatility = market_data.get('volatility', 15)  # 默认波动率
        north_flow = market_data.get('north_flow', 0)  # 北向资金流向
        
        # 强势市场：技术和北向资金权重增加
        if market_sentiment > 70:  # 强势市场
            weights['technical'] = min(0.30, weights['technical'] * 1.5)
            weights['north_flow'] = min(0.25, weights['north_flow'] * 1.5)
            weights['change_pct'] = max(0.15, weights['change_pct'] * 0.75)
            
        # 弱势市场：资金流向和成交量权重增加
        elif market_sentiment < 30:  # 弱势市场
            weights['fund_flow'] = min(0.30, weights['fund_flow'] * 1.5)
            weights['volume'] = min(0.30, weights['volume'] * 1.5)
            weights['technical'] = max(0.15, weights['technical'] * 0.75)
            
        # 高波动市场：技术指标和北向资金权重增加
        if volatility > 25:  # 高波动
            weights['technical'] = min(0.30, weights['technical'] * 1.25)
            weights['north_flow'] = min(0.25, weights['north_flow'] * 1.25)
            weights['change_pct'] = max(0.15, weights['change_pct'] * 0.8)
            
        # 北向资金异常：增加北向资金权重
        if abs(north_flow) > 50:  # 北向资金大幅流入/流出
            weights['north_flow'] = min(0.30, weights['north_flow'] * 1.5)
            weights['technical'] = max(0.15, weights['technical'] * 0.8)
            
        # 确保权重和为1
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] /= total
                
        return weights
        
    except Exception as e:
        logger.error(f"计算自适应权重失败: {e}")
        # 默认权重
        return {
            'change_pct': 0.25,
            'volume': 0.20,
            'fund_flow': 0.20,
            'north_flow': 0.15,
            'technical': 0.20
        }

def calculate_enhanced_hot_scores(sectors, weights):
    """计算增强型行业热度评分 (V2功能演示)"""
    try:
        # 随机生成示例数据补充完善行业数据
        enhanced_sectors = []
        for sector in sectors:
            enhanced = sector.copy()
            
            # 添加缺失字段
            enhanced['fund_flow'] = np.random.normal(0, 3)
            enhanced['north_flow'] = np.random.normal(0, 0.2)
            enhanced['tech_score'] = np.random.normal(50, 15)
            enhanced['up_count'] = np.random.randint(0, 50)
            enhanced['down_count'] = np.random.randint(0, 50)
            enhanced['total_stocks'] = enhanced['up_count'] + enhanced['down_count']
            enhanced['up_down_ratio'] = f"{enhanced['up_count']}/{enhanced['down_count']}"
            
            # 计算热度评分
            base_score = enhanced['change_pct'] * 3 * weights['change_pct'] * 100
            
            volume_avg = np.mean([s['volume'] for s in sectors])
            volume_score = (enhanced['volume'] / volume_avg - 1) * 25 * weights['volume'] if volume_avg > 0 else 0
            
            fund_flow_score = enhanced['fund_flow'] * 5 * weights['fund_flow']
            
            north_flow_score = enhanced['north_flow'] * 20 * weights['north_flow']
            
            tech_score = (enhanced['tech_score'] - 50) * weights['technical']
            
            # 上涨家数占比得分
            up_ratio = enhanced['up_count'] / enhanced['total_stocks'] if enhanced['total_stocks'] > 0 else 0.5
            up_down_score = (up_ratio - 0.5) * 20
            
            # 计算综合得分
            enhanced['hot_score'] = base_score + volume_score + fund_flow_score + north_flow_score + tech_score + up_down_score
            
            # 确保评分在0-100之间
            enhanced['hot_score'] = max(0, min(100, enhanced['hot_score'] + 50))  # 基准分50分
            
            # 添加热度等级
            if enhanced['hot_score'] > 80:
                enhanced['hot_level'] = '极热'
            elif enhanced['hot_score'] > 65:
                enhanced['hot_level'] = '热门'
            elif enhanced['hot_score'] > 50:
                enhanced['hot_level'] = '温和'
            elif enhanced['hot_score'] > 35:
                enhanced['hot_level'] = '冷淡'
            else:
                enhanced['hot_level'] = '极冷'
                
            # 生成分析理由
            reasons = []
            
            if enhanced['change_pct'] > 3:
                reasons.append(f"涨幅强劲({enhanced['change_pct']:.2f}%)")
            elif enhanced['change_pct'] > 1:
                reasons.append(f"上涨趋势({enhanced['change_pct']:.2f}%)")
                
            if enhanced['fund_flow'] > 3:
                reasons.append("资金大幅流入")
            elif enhanced['fund_flow'] < -3:
                reasons.append("资金大幅流出")
                
            if enhanced['tech_score'] > 70:
                reasons.append("技术指标较强")
            elif enhanced['tech_score'] < 30:
                reasons.append("技术指标较弱")
                
            if up_ratio > 0.7:
                reasons.append(f"板块个股普涨({enhanced['up_down_ratio']})")
            elif up_ratio < 0.3:
                reasons.append(f"板块个股普跌({enhanced['up_down_ratio']})")
                
            enhanced['analysis_reason'] = "，".join(reasons) if reasons else "综合多项指标评估"
            
            enhanced_sectors.append(enhanced)
            
        return enhanced_sectors
        
    except Exception as e:
        logger.error(f"计算热度评分失败: {e}")
        return sectors

if __name__ == "__main__":
    test_sector_analysis() 