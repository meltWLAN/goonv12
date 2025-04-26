#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试StockReview与LazyStockAnalyzer的集成修复
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 添加控制台处理器
        logging.FileHandler('stock_review_fix_test.log')  # 添加文件处理器
    ]
)

logger = logging.getLogger("StockReviewFixTest")

def test_stock_review_integration():
    """测试StockReview与LazyStockAnalyzer的集成修复"""
    try:
        logger.info("开始测试StockReview与LazyStockAnalyzer的集成修复")
        
        # 先运行集成脚本
        import integrate_lazy_analyzer
        success = integrate_lazy_analyzer.main()
        if not success:
            logger.error("集成脚本运行失败")
            return False
        
        logger.info("集成脚本运行成功")
        
        # 导入所需的类
        from stock_review import StockReview
        
        # 初始化StockReview
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        try:
            # 尝试使用可选的headless参数
            import inspect
            has_headless = 'headless' in inspect.signature(StockReview.__init__).parameters
            
            if has_headless:
                review = StockReview(token=token, headless=True)
                logger.info("StockReview以headless模式初始化")
            else:
                review = StockReview(token=token)
                logger.info("StockReview以普通模式初始化")
        except Exception as init_e:
            logger.error(f"初始化StockReview失败: {str(init_e)}")
            review = StockReview(token=token)
            logger.info("StockReview以普通模式初始化(回退)")
        
        # 测试股票
        symbol = '000001.SZ'  # 平安银行
        
        # 获取当前日期和90天前的日期
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        logger.info(f"分析股票 {symbol}，时间范围: {start_date} 至 {end_date}")
        
        # 检查analyze_performance方法是否存在
        if not hasattr(review, 'analyze_performance'):
            logger.error("StockReview类中不存在analyze_performance方法")
            return False
            
        logger.info("找到analyze_performance方法，开始分析...")
        
        # 计时分析过程
        start_time = time.time()
        result = review.analyze_performance(symbol, start_date, end_date)
        end_time = time.time()
        
        # 检查结果是否包含错误
        if isinstance(result, dict) and 'error' in result:
            logger.error(f"分析失败: {result['error']}")
            return False
        
        logger.info(f"分析完成，耗时 {end_time - start_time:.2f} 秒")
        
        # 记录结果详情
        if isinstance(result, dict):
            # 检查必要字段是否存在
            required_fields = [
                'symbol', 'name', 'trend', 'strength', 'last_close', 
                'volume', 'volume_trend', 'ma5', 'ma10', 'ma20', 
                'macd', 'signal', 'hist', 'rsi', 'start_date', 'end_date'
            ]
            
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                logger.error(f"结果缺少以下字段: {missing_fields}")
                logger.info(f"结果包含的字段: {list(result.keys())}")
                return False
            
            # 如果所有字段都存在，记录一些关键值
            logger.info(f"股票代码: {result['symbol']}")
            logger.info(f"股票名称: {result['name']}")
            logger.info(f"价格趋势: {result['trend']}")
            logger.info(f"趋势强度: {result['strength']:.2f}")
            logger.info(f"收盘价: {result['last_close']:.2f}")
            logger.info(f"成交量: {result['volume']}")
            logger.info(f"成交量趋势: {result['volume_trend']}")
            
            logger.info("技术指标:")
            logger.info(f"  MA5: {result['ma5']:.2f}")
            logger.info(f"  MA10: {result['ma10']:.2f}")
            logger.info(f"  MA20: {result['ma20']:.2f}")
            logger.info(f"  MACD: {result['macd']:.2f}")
            logger.info(f"  Signal: {result['signal']:.2f}")
            logger.info(f"  Histogram: {result['hist']:.2f}")
            logger.info(f"  RSI: {result['rsi']:.2f}")
            
            # 检查analysis字段
            if 'analysis' in result and isinstance(result['analysis'], dict):
                logger.info(f"分析结果包含 {len(result['analysis'])} 个指标")
            
            logger.info("StockReview集成测试成功完成")
            return True
        else:
            logger.error(f"结果不是字典: {type(result)}")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置工作目录为脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # 初始化QApplication以防止GUI相关错误
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication(sys.argv)
            logger.info("QApplication初始化成功")
        except ImportError:
            logger.warning("无法导入PyQt5，GUI组件可能无法工作")
    
        success = test_stock_review_integration()
        
        if success:
            logger.info("========================")
            logger.info("✅ 测试成功 - StockReview与LazyStockAnalyzer集成修复有效")
            logger.info("========================")
            sys.exit(0)
        else:
            logger.error("========================")
            logger.error("❌ 测试失败 - StockReview与LazyStockAnalyzer集成修复无效")
            logger.error("========================")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"测试脚本运行出错: {str(e)}")
        traceback.print_exc()
        sys.exit(1) 