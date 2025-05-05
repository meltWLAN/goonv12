#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最终测试脚本，验证热门行业分析功能是否能在主系统中正常运行
"""

import os
import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("final_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("FinalTest")

def main():
    """主函数"""
    try:
        logger.info("开始最终测试...")
        
        # 导入股票分析器应用
        try:
            from stock_analyzer_app import StockAnalyzerApp
            logger.info("成功导入StockAnalyzerApp")
        except ImportError as e:
            logger.error(f"导入StockAnalyzerApp失败: {str(e)}")
            return 1
        
        # 初始化QApplication
        app = QApplication(sys.argv)
        
        # 创建股票分析器应用
        analyzer_app = StockAnalyzerApp()
        logger.info("成功创建StockAnalyzerApp实例")
        
        # 显示应用
        analyzer_app.show()
        logger.info("已显示StockAnalyzerApp界面")
        
        # 执行热门行业分析
        analyzer_app.analyze_hot_industries()
        logger.info("已执行热门行业分析功能")
        
        # 运行应用
        logger.info("开始运行应用主循环")
        return app.exec_()
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 