#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统统一入口
本文件是系统的唯一官方入口点
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from stock_analyzer_app import StockAnalyzerApp

# 设置全局日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='system.log'
)
logger = logging.getLogger('MainApp')

def check_dependencies():
    """检查必要的依赖"""
    try:
        # 初始化行业分析器集成工具
        from integrate_sector_analyzer import SectorAnalyzerIntegrator
        integrator = SectorAnalyzerIntegrator()
        
        # 记录分析器状态
        logger.info(f"行业分析器状态 - 简化版: {integrator.simple_available}")
        if not integrator.simple_available:
            logger.warning("警告：简化版行业分析器不可用，系统可能无法提供完整功能")
        else:
            logger.info("将使用简化版行业分析器")
            
        # 检查是否存在必要的目录
        data_dirs = ['./data_cache', './data']
        for d in data_dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                logger.info(f"创建数据目录: {d}")
                
        return True
    except Exception as e:
        logger.error(f"依赖检查失败: {e}")
        return False

def main():
    """主函数入口"""
    logger.info("股票分析系统启动中...")
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败，系统退出")
        return 1
    
    # 初始化应用
    app = QApplication(sys.argv)
    analyzer_app = StockAnalyzerApp()
    
    # 启动应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 