#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试热门行业分析功能
不依赖于主程序的GUI界面
"""

import os
import sys
import logging
import pandas as pd
from pprint import pprint

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hot_sectors_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HotSectorsTest")

def main():
    """测试热门行业分析功能"""
    try:
        logger.info("开始测试热门行业分析功能...")
        
        # 导入优化版行业分析器
        from optimized_sector_analyzer import OptimizedSectorAnalyzer
        
        # 创建行业分析器实例，使用AKShare作为数据源
        analyzer = OptimizedSectorAnalyzer(top_n=10, provider_type='akshare')
        logger.info(f"已创建行业分析器实例：{analyzer.__class__.__name__}")
        
        # 分析热门行业
        logger.info("正在分析热门行业...")
        result = analyzer.analyze_hot_sectors()
        
        # 检查结果
        if 'error' in result:
            logger.error(f"分析热门行业失败：{result['error']}")
            return 1
        
        # 打印热门行业
        print("\n===== 热门行业 TOP 10 =====")
        hot_sectors = result['data']['sectors']
        for i, sector in enumerate(hot_sectors, 1):
            print(f"{i}. {sector['name']} ({sector['code']})")
            print(f"   评分: {sector['score']} | 趋势强度: {sector['trend_strength']}")
            print(f"   5日涨幅: {sector['change_rate_5d']}% | 20日涨幅: {sector['change_rate_20d']}%")
            print(f"   数据来源: {sector.get('data_source', 'unknown')} | 真实数据: {sector.get('is_real_data', True)}")
            print()
        
        # 打印市场概况
        market_info = result['data']['market_info']
        print("\n===== 市场概况 =====")
        print(f"市场情绪: {market_info['market_sentiment']}")
        print(f"上证指数涨跌幅: {market_info['shanghai_change_pct']}%")
        print(f"深证成指涨跌幅: {market_info['shenzhen_change_pct']}%")
        print(f"市场平均涨跌幅: {market_info['market_avg_change']}%")
        print(f"平均波动率: {market_info['volatility']}%")
        
        # 预测热门行业
        logger.info("正在预测未来热门行业...")
        prediction = analyzer.predict_hot_sectors()
        
        # 检查预测结果
        if 'error' in prediction:
            logger.error(f"预测热门行业失败：{prediction['error']}")
            return 1
        
        # 打印预测结果
        print("\n===== 热门行业预测 =====")
        predicted_sectors = prediction['data']['predicted_sectors']
        for i, sector in enumerate(predicted_sectors, 1):
            print(f"{i}. {sector['name']} ({sector['code']})")
            print(f"   预测5日涨幅: {sector['predicted_5d_change']}%")
            print(f"   预测20日涨幅: {sector['predicted_20d_change']}%")
            print(f"   预测置信度: {sector['prediction_confidence']}%")
            print()
        
        logger.info("测试完成")
        return 0
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 