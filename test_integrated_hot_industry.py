#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试集成到主系统的热门行业分析功能
不启动完整的GUI界面，只测试热门行业分析功能
"""

import os
import sys
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_hot_industry_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("IntegratedHotIndustryTest")

def main():
    """测试集成到主系统的热门行业分析功能"""
    try:
        logger.info("开始测试集成到主系统的热门行业分析功能...")
        
        # 导入必要的模块
        try:
            from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QTextEdit
            from PyQt5.QtCore import Qt
            app = QApplication(sys.argv)
            logger.info("PyQt5环境初始化成功")
        except ImportError as e:
            logger.error(f"PyQt5导入失败: {str(e)}")
            return 1
        
        # 导入股票分析器应用
        try:
            from stock_analyzer_app import StockAnalyzerApp
            logger.info("成功导入StockAnalyzerApp")
        except ImportError as e:
            logger.error(f"导入StockAnalyzerApp失败: {str(e)}")
            return 1
            
        # 1. 测试优化版行业分析器单独使用
        logger.info("1. 测试优化版行业分析器单独使用...")
        try:
            from optimized_sector_analyzer import OptimizedSectorAnalyzer
            analyzer = OptimizedSectorAnalyzer(top_n=10, provider_type='akshare')
            logger.info(f"已创建优化版行业分析器: {analyzer.__class__.__name__}")
            
            # 分析热门行业
            logger.info("正在分析热门行业...")
            start_time = time.time()
            result = analyzer.analyze_hot_sectors()
            end_time = time.time()
            
            # 检查结果
            if 'error' in result:
                logger.error(f"分析热门行业失败: {result['error']}")
            else:
                sectors = result['data']['sectors']
                logger.info(f"成功获取热门行业, 耗时: {end_time - start_time:.2f}秒, 共 {len(sectors)} 个行业")
                logger.info(f"前3个热门行业:")
                for i, sector in enumerate(sectors[:3], 1):
                    logger.info(f"{i}. {sector['name']} ({sector['code']}) - 评分: {sector['score']} - 趋势强度: {sector['trend_strength']}")
                
                # 测试预测功能
                logger.info("测试预测功能...")
                prediction = analyzer.predict_hot_sectors()
                if 'error' in prediction:
                    logger.error(f"预测热门行业失败: {prediction['error']}")
                else:
                    predicted_sectors = prediction['data']['predicted_sectors']
                    logger.info(f"成功预测热门行业, 共 {len(predicted_sectors)} 个预测")
        except Exception as e:
            logger.error(f"测试优化版行业分析器失败: {str(e)}")
            logger.error("继续下一阶段测试...")
        
        # 2. 测试集成在主应用中的热门行业分析功能
        logger.info("\n2. 测试集成在主应用中的热门行业分析功能...")
        
        # 创建简化版测试窗口
        class TestWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("热门行业分析集成测试")
                self.setGeometry(100, 100, 800, 600)
                self.centralWidget = QLabel()
                self.setCentralWidget(self.centralWidget)
                
                # 创建布局
                layout = QVBoxLayout(self.centralWidget)
                
                # 创建结果文本框
                self.result_text = QTextEdit()
                self.result_text.setReadOnly(True)
                layout.addWidget(self.result_text)
                
                # 启动分析
                self.run_analysis()
            
            def run_analysis(self):
                self.result_text.append("正在初始化股票分析器应用...")
                
                try:
                    # 创建股票分析器应用实例，但不显示界面
                    self.analyzer_app = StockAnalyzerApp()
                    self.result_text.append("已创建StockAnalyzerApp实例")
                    
                    # 保存原始的result_text引用
                    original_result_text = self.analyzer_app.result_text
                    
                    # 替换为我们的结果文本框
                    self.analyzer_app.result_text = self.result_text
                    
                    # 运行热门行业分析
                    self.result_text.append("开始运行热门行业分析...")
                    self.analyzer_app.analyze_hot_industries()
                    
                    # 恢复原始引用
                    self.analyzer_app.result_text = original_result_text
                    
                    self.result_text.append("\n测试完成!")
                except Exception as e:
                    self.result_text.append(f"运行分析时出错: {str(e)}")
                    logger.error(f"运行分析时出错: {str(e)}", exc_info=True)
        
        # 运行测试窗口
        window = TestWindow()
        window.show()
        
        logger.info("测试窗口已启动")
        return app.exec_()
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 