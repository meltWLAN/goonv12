#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版股票分析器，仅包含必要的代码来支持热门行业分析功能
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt

# 导入优化版行业分析器
from optimized_sector_analyzer import OptimizedSectorAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stock_analyzer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MinimalStockAnalyzer")

class MinimalStockAnalyzerApp(QMainWindow):
    """简化版股票分析应用，仅支持热门行业分析功能"""
    
    def __init__(self):
        """初始化应用"""
        super().__init__()
        self.setWindowTitle("股票分析系统 - 热门行业分析")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建文本输出区域
        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)
        self.setCentralWidget(self.result_text)
        
        # 设置日志
        self.logger = logging.getLogger('MinimalStockAnalyzerApp')
        
        # 初始化完成
        self.logger.info("简化版股票分析应用初始化完成")
    
    def show_error_message(self, title, message):
        """显示错误消息对话框"""
        QMessageBox.warning(self, title, message)
    
    def analyze_hot_industries(self):
        """热门行业分析和预测功能"""
        try:
            self.result_text.clear()
            self.result_text.append("正在分析热门行业数据，请稍候...")
            QApplication.processEvents()  # 更新UI
            
            # 初始化行业分析器 - 使用优化版行业分析器
            try:
                # 优先使用优化版行业分析器
                sector_analyzer = OptimizedSectorAnalyzer(top_n=15, provider_type='akshare')
                self.logger.info("使用优化版行业分析器(AKShare)")
            except Exception as e:
                # 如果优化版分析器初始化失败，直接显示错误
                self.logger.error(f"行业分析器初始化失败: {str(e)}")
                self.show_error_message('初始化失败', f"行业分析器初始化失败: {str(e)}")
                return
            
            # 获取热门行业分析结果
            self.result_text.append("正在获取行业列表及计算热度...")
            QApplication.processEvents()  # 更新UI
            result = sector_analyzer.analyze_hot_sectors()
            
            # 处理结果
            if 'error' in result:
                self.show_error_message('分析失败', f"热门行业分析失败: {result['error']}")
                return
                
            # 获取热门行业列表
            hot_sectors = result['data']['sectors']
            
            # 获取市场信息
            market_info = result['data'].get('market_info', {
                'market_sentiment': 0,
                'north_flow': 0,
                'volatility': 0,
                'shanghai_change_pct': 0,
                'shenzhen_change_pct': 0,
                'market_avg_change': 0
            })
            
            # 生成热门行业分析报告
            self.result_text.append("\n===== 热门行业分析报告 =====")
            self.result_text.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.result_text.append(f"市场情绪指数: {market_info.get('market_sentiment', 0):.2f}")
            self.result_text.append(f"北向资金流入(亿元): {market_info.get('north_flow', 0):.2f}")
            self.result_text.append(f"市场波动率: {market_info.get('volatility', 0):.2f}%")
            
            # 显示热门行业排名
            self.result_text.append("\n【热门行业排名】")
            for i, sector in enumerate(hot_sectors[:10]):  # 显示前10个行业
                # 格式化输出，确保所有必要字段存在
                score = sector.get('score', 0)
                change_1d = sector.get('change_rate_1d', 0)
                
                self.result_text.append(f"{i+1}. {sector['name']} ({sector['code']}) - "
                                      f"评分: {score:.2f} - 涨跌幅: {change_1d:.2f}%")
                
                # 显示更多详细信息
                self.result_text.append(f"   5日涨幅: {sector.get('change_rate_5d', 0):.2f}% | "
                                      f"20日涨幅: {sector.get('change_rate_20d', 0):.2f}% | "
                                      f"趋势强度: {sector.get('trend_strength', 0):.2f}")
            
            # 获取行业预测结果
            self.result_text.append("\n正在预测未来行业走势...")
            QApplication.processEvents()  # 更新UI
            
            try:
                prediction_result = sector_analyzer.predict_hot_sectors()
                
                if 'error' in prediction_result:
                    self.result_text.append(f"\n预测分析失败: {prediction_result['error']}")
                else:
                    # 获取预测行业列表
                    predicted_sectors = prediction_result['data']['predicted_sectors']
                    
                    # 显示预测结果
                    self.result_text.append("\n【行业走势预测】")
                    
                    for i, pred in enumerate(predicted_sectors[:5]):  # 显示前5个预测
                        self.result_text.append(f"{i+1}. {pred['name']} ({pred['code']}) - "
                                             f"预测5日涨幅: {pred.get('predicted_5d_change', 0):.2f}% - "
                                             f"置信度: {pred.get('prediction_confidence', 0):.2f}%")
            except Exception as e:
                self.logger.error(f"预测热门行业时出错: {str(e)}")
                self.result_text.append(f"\n预测分析失败: {str(e)}")
            
            # 强调风险提示
            self.result_text.append("\n⚠️ 风险提示: 行业分析仅供参考，投资决策需结合多方面因素，注意控制风险。")
            
        except Exception as e:
            import traceback
            self.logger.error(f"热门行业分析出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.show_error_message('分析错误', f"热门行业分析过程中出错: {str(e)}")
            self.result_text.append(f"分析发生错误: {str(e)}")

def main():
    """主函数"""
    try:
        # 初始化QApplication
        app = QApplication(sys.argv)
        
        # 创建并显示应用
        analyzer_app = MinimalStockAnalyzerApp()
        analyzer_app.show()
        
        # 自动运行热门行业分析
        analyzer_app.analyze_hot_industries()
        
        # 运行应用
        return app.exec_()
    except Exception as e:
        print(f"启动应用出错: {str(e)}")
        logging.error(f"启动应用出错: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 