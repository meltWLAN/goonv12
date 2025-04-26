#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LazyStockAnalyzer整合测试脚本
验证所有模块的整合效果
"""

import os
import sys
import time
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntegrationTest")

def test_smart_review_core():
    """测试SmartReviewCore整合效果"""
    logger.info("测试SmartReviewCore整合效果...")
    
    try:
        from smart_review_core import SmartReviewCore
        
        # 使用按需计算模式
        start_time = time.time()
        core_lazy = SmartReviewCore(lazy_mode=True)
        lazy_init_time = time.time() - start_time
        
        # 使用全量计算模式
        start_time = time.time()
        core_full = SmartReviewCore(lazy_mode=False)
        full_init_time = time.time() - start_time
        
        logger.info(f"SmartReviewCore按需计算模式初始化时间: {lazy_init_time:.4f}秒")
        logger.info(f"SmartReviewCore全量计算模式初始化时间: {full_init_time:.4f}秒")
        
        # 检查分析器配置
        lazy_indicators = list(core_lazy.analyzer.required_indicators)
        full_indicators = list(core_full.analyzer.required_indicators)
        
        logger.info(f"按需计算模式指标数量: {len(lazy_indicators)}")
        logger.info(f"全量计算模式指标数量: {len(full_indicators)}")
        
        print(f"SmartReviewCore整合测试通过 ✓")
        print(f"- 按需计算模式指标: {', '.join(lazy_indicators[:5])}...")
        print(f"- 全量计算模式指标数量: {len(full_indicators)}")
        
        return True
    except Exception as e:
        logger.error(f"SmartReviewCore测试失败: {str(e)}")
        print(f"SmartReviewCore整合测试失败 ✗ - {str(e)}")
        return False

def test_strategy_optimization_engine():
    """测试StrategyOptimizationEngine整合效果"""
    logger.info("测试StrategyOptimizationEngine整合效果...")
    
    try:
        from strategy_optimization_engine import StrategyOptimizationEngine
        
        # 初始化引擎
        engine = StrategyOptimizationEngine()
        
        # 检查是否有LazyStockAnalyzer属性
        has_analyzer = hasattr(engine, 'lazy_analyzer')
        
        # 检查辅助方法
        has_helper = hasattr(engine, '_get_strategy_required_indicators')
        
        if has_analyzer and has_helper:
            # 获取不同策略所需指标
            vp_indicators = engine._get_strategy_required_indicators('volume_price')
            ma_indicators = engine._get_strategy_required_indicators('moving_average_crossover')
            rsi_indicators = engine._get_strategy_required_indicators('rsi_strategy')
            
            logger.info(f"量价策略所需指标: {vp_indicators}")
            logger.info(f"均线交叉策略所需指标: {ma_indicators}")
            logger.info(f"RSI策略所需指标: {rsi_indicators}")
            
            print(f"StrategyOptimizationEngine整合测试通过 ✓")
            print(f"- 拥有LazyStockAnalyzer: {has_analyzer}")
            print(f"- 拥有策略指标选择器: {has_helper}")
            print(f"- 量价策略指标: {', '.join(vp_indicators) if isinstance(vp_indicators, list) else vp_indicators}")
            
            return True
        else:
            logger.error(f"StrategyOptimizationEngine缺少必要组件: analyzer={has_analyzer}, helper={has_helper}")
            print(f"StrategyOptimizationEngine整合测试失败 ✗ - 缺少必要组件")
            return False
    except Exception as e:
        logger.error(f"StrategyOptimizationEngine测试失败: {str(e)}")
        print(f"StrategyOptimizationEngine整合测试失败 ✗ - {str(e)}")
        return False

def test_enhanced_backtester():
    """测试EnhancedBacktester整合效果"""
    logger.info("测试EnhancedBacktester整合效果...")
    
    try:
        from enhanced_backtesting import EnhancedBacktester
        
        # 初始化回测器
        backtester = EnhancedBacktester()
        
        # 检查是否有LazyStockAnalyzer属性
        has_analyzer = hasattr(backtester, 'lazy_analyzer')
        
        # 检查辅助方法
        has_helper = hasattr(backtester, '_prepare_data_with_indicators')
        
        if has_analyzer and has_helper:
            logger.info("EnhancedBacktester已正确整合LazyStockAnalyzer")
            print(f"EnhancedBacktester整合测试通过 ✓")
            print(f"- 拥有LazyStockAnalyzer: {has_analyzer}")
            print(f"- 拥有数据预处理方法: {has_helper}")
            return True
        else:
            logger.error(f"EnhancedBacktester缺少必要组件: analyzer={has_analyzer}, helper={has_helper}")
            print(f"EnhancedBacktester整合测试失败 ✗ - 缺少必要组件")
            return False
    except Exception as e:
        logger.error(f"EnhancedBacktester测试失败: {str(e)}")
        print(f"EnhancedBacktester整合测试失败 ✗ - {str(e)}")
        return False

def test_volume_price_strategy():
    """测试VolumePriceStrategy整合效果"""
    logger.info("测试VolumePriceStrategy整合效果...")
    
    try:
        from volume_price_strategy import VolumePriceStrategy
        import pandas as pd
        import numpy as np
        
        # 创建策略实例
        strategy = VolumePriceStrategy()
        
        # 检查策略代码中LazyStockAnalyzer的使用
        with open('./volume_price_strategy.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        uses_lazy = 'from lazy_analyzer import LazyStockAnalyzer' in code
        uses_analyze = 'analyzer = LazyStockAnalyzer(' in code
        
        if uses_lazy and uses_analyze:
            logger.info("VolumePriceStrategy已正确整合LazyStockAnalyzer")
            print(f"VolumePriceStrategy整合测试通过 ✓")
            print(f"- 导入LazyStockAnalyzer: {uses_lazy}")
            print(f"- 使用LazyStockAnalyzer: {uses_analyze}")
            return True
        else:
            logger.error(f"VolumePriceStrategy缺少必要组件: import={uses_lazy}, usage={uses_analyze}")
            print(f"VolumePriceStrategy整合测试失败 ✗ - 缺少必要组件")
            return False
    except Exception as e:
        logger.error(f"VolumePriceStrategy测试失败: {str(e)}")
        print(f"VolumePriceStrategy整合测试失败 ✗ - {str(e)}")
        return False

def test_smart_review_main():
    """测试SmartReviewMain整合效果"""
    logger.info("测试SmartReviewMain整合效果...")
    
    try:
        # 检查主程序代码中LazyStockAnalyzer的使用
        with open('./smart_review_main.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        has_lazy_arg = '--lazy-mode' in code
        uses_lazy_param = 'lazy_mode=args.lazy_mode' in code
        
        if has_lazy_arg and uses_lazy_param:
            logger.info("SmartReviewMain已正确整合LazyStockAnalyzer")
            print(f"SmartReviewMain整合测试通过 ✓")
            print(f"- 添加lazy_mode命令行选项: {has_lazy_arg}")
            print(f"- 使用lazy_mode参数: {uses_lazy_param}")
            return True
        else:
            logger.error(f"SmartReviewMain缺少必要组件: arg={has_lazy_arg}, param={uses_lazy_param}")
            print(f"SmartReviewMain整合测试失败 ✗ - 缺少必要组件")
            return False
    except Exception as e:
        logger.error(f"SmartReviewMain测试失败: {str(e)}")
        print(f"SmartReviewMain整合测试失败 ✗ - {str(e)}")
        return False

def test_stock_review_integration():
    """Test the integration of LazyStockAnalyzer with StockReview"""
    # Initialize the integration by first running the integration script
    try:
        import integrate_lazy_analyzer
        integrate_lazy_analyzer.main()
        print("Integration script executed successfully!")
    except Exception as e:
        print(f"Integration script execution failed: {str(e)}")
        return

    try:
        # Import necessary modules
        from stock_review import StockReview
        from visual_stock_system import VisualStockSystem

        # Initialize StockReview
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        review = StockReview(token)
        
        # Test stocks
        test_symbols = ['000001.SZ', '600000.SH', '000002.SZ']
        
        print("\n===== TESTING STOCK REVIEW ANALYZE_PERFORMANCE =====")
        for symbol in test_symbols:
            print(f"\nAnalyzing {symbol}...")
            
            # Time the performance
            start_time = time.time()
            result = review.analyze_performance(symbol)
            end_time = time.time()
            
            # Check for errors
            if 'error' in result:
                print(f"Error analyzing {symbol}: {result['error']}")
                continue
                
            # Print the results
            print(f"Analysis completed in {end_time - start_time:.2f} seconds")
            print(f"Symbol: {result['symbol']}")
            print(f"Name: {result['name']}")
            print(f"Trend: {result['trend']}")
            print(f"Strength: {result['strength']:.2f}")
            print(f"Last close: {result['last_close']}")
            print(f"Volume: {result['volume']}")
            
            # Print other interesting metrics if available
            if 'analysis' in result and isinstance(result['analysis'], dict):
                analysis = result['analysis']
                print("\nTechnical Indicators:")
                
                if 'rsi14' in analysis:
                    print(f"RSI(14): {analysis['rsi14']:.2f}")
                    
                if 'macd' in analysis and 'macd_signal' in analysis:
                    print(f"MACD: {analysis['macd']:.4f}, Signal: {analysis['macd_signal']:.4f}")
                    
                if 'boll_upper' in analysis and 'boll_lower' in analysis:
                    print(f"Bollinger Bands: Upper: {analysis['boll_upper']:.2f}, Lower: {analysis['boll_lower']:.2f}")
                    
                if 'adx' in analysis:
                    print(f"ADX: {analysis['adx']:.2f}")
                    
                if 'volume_ratio' in analysis:
                    print(f"Volume ratio: {analysis['volume_ratio']:.2f}")
        
        print("\n===== TEST COMPLETE =====")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Test failed: {str(e)}")
        return False

def compare_analysis_methods():
    """Compare original analyze_stock with LazyStockAnalyzer"""
    try:
        # Import necessary modules
        from visual_stock_system import VisualStockSystem
        from lazy_analyzer import LazyStockAnalyzer
        import types
        
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        vss = VisualStockSystem(token, headless=True)
        
        # Test stock
        symbol = '000001.SZ'
        
        print("\n===== COMPARING ANALYSIS METHODS =====")
        
        # Time the original method
        print(f"\nTesting original analyze_stock method...")
        
        # Store current method
        original_method = vss.analyze_stock
        
        # Restore original method temporarily
        from visual_stock_system import VisualStockSystem as VSS
        vss.analyze_stock = types.MethodType(VSS.analyze_stock, vss)
        
        # Test performance
        start_time = time.time()
        result_original, rec_original = vss.analyze_stock(symbol)
        end_time = time.time()
        original_time = end_time - start_time
        
        print(f"Original method completed in {original_time:.2f} seconds")
        print(f"Original result contains {len(result_original) if isinstance(result_original, dict) else 'unknown'} data fields")
        print(f"Original recommendation: {rec_original}")
        
        # Import and run integration
        import integrate_lazy_analyzer
        integrate_lazy_analyzer.integrate_with_visual_stock_system()
        
        # Time the lazy analyzer method
        print(f"\nTesting LazyStockAnalyzer method...")
        start_time = time.time()
        result_lazy = vss.analyze_stock(symbol)
        end_time = time.time()
        lazy_time = end_time - start_time
        
        print(f"LazyStockAnalyzer method completed in {lazy_time:.2f} seconds")
        print(f"Lazy result contains {len(result_lazy) if isinstance(result_lazy, dict) else 'unknown'} data fields")
        print(f"Lazy recommendation: {result_lazy.get('recommendation', 'unknown')}")
        
        # Compare performance
        speedup = original_time / lazy_time if lazy_time > 0 else 0
        print(f"\nPerformance comparison: LazyStockAnalyzer is {speedup:.2f}x faster")
        
        print("\n===== COMPARISON COMPLETE =====")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Comparison test failed: {str(e)}")
        return False

def run_tests():
    """运行所有测试"""
    print("\n===== LazyStockAnalyzer整合测试 =====\n")
    
    results = {
        'SmartReviewCore': test_smart_review_core(),
        'StrategyOptimizationEngine': test_strategy_optimization_engine(),
        'EnhancedBacktester': test_enhanced_backtester(),
        'VolumePriceStrategy': test_volume_price_strategy(),
        'SmartReviewMain': test_smart_review_main()
    }
    
    # 打印总结
    print("\n===== 测试结果摘要 =====")
    
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    for module, success in results.items():
        status = "✓" if success else "✗"
        print(f"{module}: {status}")
    
    print(f"\n总体结果: {success_count}/{total_count} 通过")
    
    # 返回整体结果
    return all(results.values())

if __name__ == "__main__":
    print("Starting integration tests...")
    test_stock_review_integration()
    compare_analysis_methods()
    print("All tests completed.")
    sys.exit(0 if run_tests() else 1) 