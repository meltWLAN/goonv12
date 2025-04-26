#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import logging
import time
from datetime import datetime

# 导入LazyStockAnalyzer和股票数据提供者
from lazy_analyzer import LazyStockAnalyzer
from china_stock_provider import ChinaStockProvider
from visual_stock_system import VisualStockSystem

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestSmartAnalyzer")

def test_analyze_stock(symbol, required_indicators=None):
    """测试使用LazyStockAnalyzer分析单只股票
    
    Args:
        symbol: 股票代码
        required_indicators: 需要计算的指标列表
    """
    # 初始化组件
    token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    provider = ChinaStockProvider(token)
    visual_system = VisualStockSystem(token, headless=True)
    
    # 创建不同模式的分析器
    if required_indicators:
        analyzer = LazyStockAnalyzer(required_indicators=required_indicators)
        mode = "指定指标模式"
    else:
        analyzer = LazyStockAnalyzer(required_indicators='all')
        mode = "全量指标模式"
    
    logger.info(f"开始分析股票 {symbol} ({mode})")
    
    try:
        # 获取股票数据
        logger.info(f"获取 {symbol} 的历史数据")
        df = visual_system.get_stock_data(symbol)
        
        if df is None or len(df) < 20:
            logger.error(f"无法获取足够的股票数据: {symbol}")
            return None
        
        # 使用LazyStockAnalyzer进行分析
        start_time = time.time()
        analysis = analyzer.analyze(df)
        analysis_time = time.time() - start_time
        
        # 打印分析结果
        print(f"\n股票 {symbol} 分析完成! 耗时: {analysis_time:.4f}秒")
        print(f"共计算了 {len(analysis)} 个指标")
        
        print("\n关键指标:")
        key_indicators = ['close', 'volume', 'ma5', 'ma20', 'rsi', 'macd', 'macd_hist', 
                          'trend_direction', 'volume_ratio', 'k', 'd', 'j']
        
        for key in key_indicators:
            if key in analysis:
                print(f"{key}: {analysis[key]}")
            else:
                print(f"{key}: 未计算")
        
        # 根据分析结果生成推荐级别
        trend = 'uptrend' if analysis.get('trend_direction', 0) > 0 else 'downtrend' if analysis.get('trend_direction', 0) < 0 else 'sideways'
        volume_ratio = analysis.get('volume_ratio', 1.0)
        macd_hist = analysis.get('macd_hist', 0)
        
        if trend == 'uptrend' and volume_ratio > 1.5 and macd_hist > 0:
            recommendation = '强烈推荐买入'
        elif trend == 'uptrend' and volume_ratio > 1.2:
            recommendation = '建议买入'
        elif trend == 'downtrend' and volume_ratio > 1.5 and macd_hist < 0:
            recommendation = '强烈建议卖出'
        elif trend == 'downtrend':
            recommendation = '建议卖出'
        else:
            recommendation = '观望'
        
        print(f"\n趋势: {trend}")
        print(f"成交量比率: {volume_ratio}")
        print(f"推荐级别: {recommendation}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"分析股票时出错: {str(e)}")
        return None

def test_compare_analysis_modes():
    """对比不同分析模式的性能差异"""
    symbol = '000001.SZ'  # 平安银行
    
    # 全量指标模式
    print("\n===== 测试全量指标模式 =====")
    start_time = time.time()
    all_indicators = test_analyze_stock(symbol, 'all')
    all_time = time.time() - start_time
    
    # 指定关键指标模式
    required_indicators = ['ma', 'ema', 'rsi', 'macd']
    print(f"\n===== 测试指定指标模式 ({', '.join(required_indicators)}) =====")
    start_time = time.time()
    partial_indicators = test_analyze_stock(symbol, required_indicators)
    partial_time = time.time() - start_time
    
    # 打印性能对比
    print("\n===== 性能对比 =====")
    print(f"全量指标模式总耗时: {all_time:.4f}秒，包含 {len(all_indicators) if all_indicators else 0} 个指标")
    print(f"指定指标模式总耗时: {partial_time:.4f}秒，包含 {len(partial_indicators) if partial_indicators else 0} 个指标")
    
    if all_time > 0 and partial_time > 0:
        speedup = all_time / partial_time
        print(f"性能提升: {speedup:.2f}倍")

if __name__ == "__main__":
    # 测试不同模式性能对比
    test_compare_analysis_modes() 