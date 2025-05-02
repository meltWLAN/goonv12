#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from lazy_analyzer import LazyStockAnalyzer
from china_stock_provider import ChinaStockProvider
from visual_stock_system import VisualStockSystem

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartReviewTest")

class SmartReviewTester:
    """智能复盘测试类，使用LazyStockAnalyzer进行分析"""
    
    def __init__(self, token=None):
        """初始化测试环境
        
        Args:
            token: API令牌
        """
        self.token = token or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.test_dir = './test_results'
        
        # 确保测试目录存在
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 初始化组件
        logger.info("初始化数据提供者和分析器")
        self.data_provider = ChinaStockProvider(self.token)
        self.visual_system = VisualStockSystem(self.token, headless=True)
        
        # 创建两种分析器：全量分析和按需分析
        self.full_analyzer = LazyStockAnalyzer(required_indicators='all')
        self.lazy_analyzer = LazyStockAnalyzer(required_indicators=[
            'ma', 'ema', 'macd', 'rsi'  # 默认只计算这些必要指标
        ])
        
        logger.info("测试环境初始化完成")
    
    def test_stock_analysis(self, symbol, use_lazy=True):
        """测试股票分析
        
        Args:
            symbol: 股票代码
            use_lazy: 是否使用按需分析器
        
        Returns:
            分析结果
        """
        logger.info(f"分析股票 {symbol}，使用{'按需' if use_lazy else '全量'}分析器")
        
        try:
            # 获取股票数据
            df = self.visual_system.get_stock_data(symbol)
            
            if df is None or len(df) < 20:
                logger.warning(f"无法获取足够的股票数据: {symbol}")
                return None
            
            # 选择分析器
            analyzer = self.lazy_analyzer if use_lazy else self.full_analyzer
            
            # 执行分析
            start_time = datetime.now()
            analysis = analyzer.analyze(df)
            end_time = datetime.now()
            
            # 计算分析时间
            analysis_time = (end_time - start_time).total_seconds()
            
            # 添加元信息
            analysis['_meta'] = {
                'symbol': symbol,
                'analysis_time': analysis_time,
                'indicator_count': len(analysis),
                'analyzer_type': 'lazy' if use_lazy else 'full',
                'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 生成推荐
            analysis['recommendation'] = self._generate_recommendation(analysis)
            
            logger.info(f"分析完成，耗时: {analysis_time:.4f}秒，计算了 {len(analysis)} 个指标")
            return analysis
            
        except Exception as e:
            logger.error(f"分析股票时出错: {str(e)}")
            return None
    
    def _generate_recommendation(self, analysis):
        """根据分析结果生成推荐级别
        
        Args:
            analysis: 分析结果
            
        Returns:
            推荐级别
        """
        # 提取关键指标
        trend = 'uptrend' if analysis.get('trend_direction', 0) > 0 else 'downtrend' if analysis.get('trend_direction', 0) < 0 else 'sideways'
        volume_ratio = analysis.get('volume_ratio', 1.0)
        macd_hist = analysis.get('macd_hist', 0)
        rsi = analysis.get('rsi', 50)
        
        # 根据指标生成推荐
        if trend == 'uptrend' and volume_ratio > 1.5 and macd_hist > 0:
            return '强烈推荐买入'
        elif trend == 'uptrend' and volume_ratio > 1.2:
            return '建议买入'
        elif trend == 'downtrend' and volume_ratio > 1.5 and macd_hist < 0:
            return '强烈建议卖出'
        elif trend == 'downtrend':
            return '建议卖出'
        elif rsi < 30:
            return '超卖，可考虑买入'
        elif rsi > 70:
            return '超买，可考虑卖出'
        else:
            return '观望'
    
    def compare_analyzers(self, symbol):
        """比较不同分析器的性能
        
        Args:
            symbol: 股票代码
            
        Returns:
            比较结果
        """
        logger.info(f"比较全量分析器和按需分析器对 {symbol} 的分析性能")
        
        # 使用全量分析器
        full_start = datetime.now()
        full_result = self.test_stock_analysis(symbol, use_lazy=False)
        full_time = (datetime.now() - full_start).total_seconds()
        
        # 使用按需分析器
        lazy_start = datetime.now()
        lazy_result = self.test_stock_analysis(symbol, use_lazy=True)
        lazy_time = (datetime.now() - lazy_start).total_seconds()
        
        if not full_result or not lazy_result:
            logger.error("比较失败，至少一个分析器返回了空结果")
            return None
        
        # 比较结果
        comparison = {
            'symbol': symbol,
            'full_analyzer': {
                'time': full_time,
                'indicator_count': len(full_result),
                'recommendation': full_result.get('recommendation')
            },
            'lazy_analyzer': {
                'time': lazy_time,
                'indicator_count': len(lazy_result),
                'recommendation': lazy_result.get('recommendation')
            },
            'speedup': full_time / lazy_time if lazy_time > 0 else 0,
            'same_recommendation': full_result.get('recommendation') == lazy_result.get('recommendation')
        }
        
        logger.info(f"比较完成: 全量分析耗时 {full_time:.4f}秒，按需分析耗时 {lazy_time:.4f}秒")
        logger.info(f"性能提升: {comparison['speedup']:.2f}倍")
        logger.info(f"推荐一致性: {'一致' if comparison['same_recommendation'] else '不一致'}")
        
        return comparison
    
    def test_portfolio_analysis(self, symbols):
        """测试对股票组合的分析
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            分析结果列表
        """
        logger.info(f"分析股票组合，共 {len(symbols)} 只股票")
        
        results = []
        
        # 全量分析时间
        full_start = datetime.now()
        for symbol in symbols:
            result = self.test_stock_analysis(symbol, use_lazy=False)
            if result:
                results.append(result)
        full_time = (datetime.now() - full_start).total_seconds()
        
        # 按需分析时间
        lazy_results = []
        lazy_start = datetime.now()
        for symbol in symbols:
            result = self.test_stock_analysis(symbol, use_lazy=True)
            if result:
                lazy_results.append(result)
        lazy_time = (datetime.now() - lazy_start).total_seconds()
        
        # 统计结果
        summary = {
            'total_stocks': len(symbols),
            'successful_analyses': len(results),
            'full_analysis_time': full_time,
            'lazy_analysis_time': lazy_time,
            'speedup': full_time / lazy_time if lazy_time > 0 else 0,
            'buy_recommendations': sum(1 for r in results if '买入' in r.get('recommendation', '')),
            'sell_recommendations': sum(1 for r in results if '卖出' in r.get('recommendation', '')),
            'hold_recommendations': sum(1 for r in results if '观望' in r.get('recommendation', ''))
        }
        
        logger.info(f"组合分析完成: 全量分析总耗时 {full_time:.4f}秒，按需分析总耗时 {lazy_time:.4f}秒")
        logger.info(f"性能提升: {summary['speedup']:.2f}倍")
        
        return {
            'summary': summary,
            'results': results
        }

def main():
    """主测试函数"""
    print("===== 开始智能复盘系统测试 =====")
    
    # 创建测试实例
    tester = SmartReviewTester()
    
    # 测试单个股票的分析器性能对比
    test_symbols = ['000001.SZ', '600519.SH', '000858.SZ']
    
    print("\n1. 单股分析性能测试:")
    for symbol in test_symbols:
        print(f"\n测试股票: {symbol}")
        comparison = tester.compare_analyzers(symbol)
        if comparison:
            print(f"全量分析: {comparison['full_analyzer']['time']:.4f}秒, {comparison['full_analyzer']['indicator_count']} 个指标")
            print(f"按需分析: {comparison['lazy_analyzer']['time']:.4f}秒, {comparison['lazy_analyzer']['indicator_count']} 个指标")
            print(f"性能提升: {comparison['speedup']:.2f}倍")
            print(f"全量分析推荐: {comparison['full_analyzer']['recommendation']}")
            print(f"按需分析推荐: {comparison['lazy_analyzer']['recommendation']}")
    
    # 测试组合分析性能
    portfolio = ['000001.SZ', '600519.SH', '000858.SZ', '601318.SH', '600036.SH']
    
    print("\n2. 股票组合分析测试:")
    portfolio_result = tester.test_portfolio_analysis(portfolio)
    
    if portfolio_result:
        summary = portfolio_result['summary']
        print(f"共分析 {summary['successful_analyses']}/{summary['total_stocks']} 只股票")
        print(f"全量分析总耗时: {summary['full_analysis_time']:.4f}秒")
        print(f"按需分析总耗时: {summary['lazy_analysis_time']:.4f}秒")
        print(f"性能提升: {summary['speedup']:.2f}倍")
        print(f"推荐分布: 买入 {summary['buy_recommendations']}，卖出 {summary['sell_recommendations']}，观望 {summary['hold_recommendations']}")
    
    print("\n===== 测试完成 =====")

if __name__ == "__main__":
    main() 