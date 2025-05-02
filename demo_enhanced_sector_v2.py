#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强型行业分析器V2演示脚本
用于展示V2版本的主要功能和改进
"""

import pandas as pd
import numpy as np
import logging
import sys
import time
from pprint import pprint
from datetime import datetime

# 导入V2版本行业分析器
from enhanced_sector_analyzer_v2 import EnhancedSectorAnalyzerV2

# 设置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sector_v2_demo.log')
    ]
)
logger = logging.getLogger("EnhancedSectorV2Demo")


def demo_basic_features():
    """演示V2版本基础功能"""
    logger.info("===== 增强型行业分析器V2 基础功能演示 =====")
    
    # 初始化分析器
    logger.info("初始化分析器...")
    analyzer = EnhancedSectorAnalyzerV2(
        top_n=10,                  # 返回前10个热门行业
        cache_dir="./cache",       # 缓存目录
        enable_multithreading=True,  # 启用多线程
        max_workers=5              # 最大线程数
    )
    
    # 获取行业列表
    logger.info("获取行业列表...")
    start_time = time.time()
    sectors = analyzer.get_sector_list()
    elapsed = time.time() - start_time
    
    logger.info(f"成功获取行业列表，共 {len(sectors)} 个行业 (耗时: {elapsed:.2f}秒)")
    
    # 显示前5个行业数据
    logger.info("行业列表示例 (前5个):")
    for i, sector in enumerate(sectors[:5]):
        logger.info(f"{i+1}. {sector['name']} - 涨跌幅: {sector['change_pct']:.2f}% - 成交量: {sector['volume']:.2f}亿")
    
    return analyzer, sectors


def demo_hot_sectors(analyzer):
    """演示热门行业分析功能"""
    logger.info("\n===== 热门行业分析功能演示 =====")
    
    # 获取热门行业
    logger.info("分析热门行业...")
    start_time = time.time()
    result = analyzer.analyze_hot_sectors()
    elapsed = time.time() - start_time
    
    if result['status'] == 'success':
        hot_sectors = result['data']['hot_sectors']
        logger.info(f"成功获取热门行业，共 {len(hot_sectors)} 个 (耗时: {elapsed:.2f}秒)")
        
        # 显示热门行业
        logger.info("热门行业排名:")
        for i, sector in enumerate(hot_sectors[:10]):
            logger.info(f"{i+1}. {sector['name']} - 热度: {sector['hot_score']:.2f} - "
                      f"等级: {sector['hot_level']} - 分析: {sector['analysis_reason']}")
    else:
        logger.error(f"获取热门行业失败: {result['message']}")


def demo_technical_indicators(analyzer, sectors):
    """演示技术指标计算功能"""
    logger.info("\n===== 技术指标计算功能演示 =====")
    
    # 选择一个示例行业
    sample_sector = sectors[0]
    logger.info(f"选择示例行业: {sample_sector['name']}")
    
    # 获取行业历史数据
    logger.info(f"获取{sample_sector['name']}历史数据...")
    history_data = analyzer._get_sector_history(sample_sector['name'], days=60)
    
    if history_data is not None and not history_data.empty:
        logger.info(f"成功获取历史数据，共 {len(history_data)} 行")
        
        # 计算技术指标
        logger.info("计算技术指标...")
        indicators = analyzer._calculate_technical_indicators(history_data)
        
        logger.info("技术指标计算结果:")
        pprint(indicators)
    else:
        logger.error("获取历史数据失败")


def demo_adaptive_weights(analyzer):
    """演示自适应权重功能"""
    logger.info("\n===== 自适应权重功能演示 =====")
    
    # 获取市场情绪数据
    market_data = analyzer._get_market_sentiment()
    logger.info(f"当前市场情绪: {market_data}")
    
    # 计算自适应权重
    logger.info("计算当前市场下的自适应权重...")
    weights = analyzer._adaptive_weight_calculation(market_data)
    
    logger.info("自适应权重计算结果:")
    pprint(weights)
    
    # 模拟不同市场情况下的权重
    logger.info("\n不同市场情况下的权重变化:")
    
    # 牛市情况
    bull_market = {'market_sentiment': 80, 'volatility': 15, 'north_flow': 50}
    logger.info("牛市情况 (市场情绪高、波动适中、北向资金流入):")
    bull_weights = analyzer._adaptive_weight_calculation(bull_market)
    pprint(bull_weights)
    
    # 熊市情况
    bear_market = {'market_sentiment': 20, 'volatility': 25, 'north_flow': -30}
    logger.info("熊市情况 (市场情绪低、波动较高、北向资金流出):")
    bear_weights = analyzer._adaptive_weight_calculation(bear_market)
    pprint(bear_weights)
    
    # 震荡市情况
    normal_market = {'market_sentiment': 50, 'volatility': 10, 'north_flow': 5}
    logger.info("震荡市情况 (市场情绪中性、波动较低、北向资金小幅流入):")
    normal_weights = analyzer._adaptive_weight_calculation(normal_market)
    pprint(normal_weights)


def main():
    """演示主函数"""
    logger.info("开始增强型行业分析器V2演示")
    
    try:
        # 基础功能演示
        analyzer, sectors = demo_basic_features()
        
        # 热门行业分析演示
        demo_hot_sectors(analyzer)
        
        # 技术指标计算演示
        demo_technical_indicators(analyzer, sectors)
        
        # 自适应权重演示
        demo_adaptive_weights(analyzer)
        
        logger.info("\n演示完成!")
        
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}", exc_info=True)
        
    logger.info("增强型行业分析器V2演示结束")


if __name__ == "__main__":
    main() 