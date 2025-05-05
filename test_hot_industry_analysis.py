#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试stock_analyzer_app.py中的热门行业分析功能
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from stock_analyzer_app import StockAnalyzerApp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_hot_industry.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestHotIndustry")

def main():
    """测试热门行业分析功能的主函数"""
    try:
        logger.info("开始测试热门行业分析功能...")
        
        # 初始化QApplication
        app = QApplication(sys.argv)
        
        # 创建股票分析应用实例
        stock_analyzer = StockAnalyzerApp()
        logger.info("成功创建StockAnalyzerApp实例")
        
        # 直接调用热门行业分析方法
        logger.info("调用热门行业分析方法...")
        stock_analyzer.analyze_hot_industries()
        
        # 等待用户确认测试结果
        input("请查看上面的热门行业分析结果，然后按Enter键继续...")
        
        logger.info("测试完成")
        return 0
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 