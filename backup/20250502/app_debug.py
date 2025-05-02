#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统统一入口 - 调试版本
带有增强的日志记录和错误处理
"""

import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from stock_analyzer_app import StockAnalyzerApp

# 创建日志目录
if not os.path.exists('./logs'):
    os.makedirs('./logs')

# 设置更详细的全局日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/app_debug.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AppDebug')

def check_dependencies():
    """检查必要的依赖"""
    try:
        logger.info("正在检查依赖项...")
        
        # 检查PyQt
        from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
        logger.info(f"PyQt5版本: {PYQT_VERSION_STR}")
        logger.info(f"Qt版本: {QT_VERSION_STR}")
        
        # 检查pandas
        import pandas as pd
        logger.info(f"Pandas版本: {pd.__version__}")
        
        # 检查numpy
        import numpy as np
        logger.info(f"NumPy版本: {np.__version__}")
        
        # 检查matplotlib
        import matplotlib
        logger.info(f"Matplotlib版本: {matplotlib.__version__}")
        
        # 检查tushare
        try:
            import tushare
            logger.info(f"Tushare版本: {tushare.__version__}")
        except ImportError:
            logger.warning("未找到Tushare库")
        
        # 检查其他模块是否存在
        required_modules = [
            'fix_sector_analyzer',
            'integrate_sector_analyzer',
            'visual_stock_system',
            'china_stock_provider'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
                logger.info(f"模块已找到: {module_name}")
            except ImportError as e:
                logger.error(f"模块检查失败: {module_name} - {e}")
                return False
        
        # 初始化行业分析器集成工具
        logger.info("初始化行业分析器...")
        from integrate_sector_analyzer import SectorAnalyzerIntegrator
        integrator = SectorAnalyzerIntegrator()
        
        # 记录分析器状态
        logger.info(f"行业分析器状态 - 简化版: {integrator.simple_available}")
        if not integrator.simple_available:
            logger.warning("警告：简化版行业分析器不可用，系统可能无法提供完整功能")
        else:
            logger.info("将使用简化版行业分析器")
            
        # 检查是否存在必要的目录
        logger.info("检查数据目录...")
        data_dirs = ['./data_cache', './data', './logs']
        for d in data_dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                logger.info(f"创建数据目录: {d}")
                
        return True
    except Exception as e:
        logger.error(f"依赖检查异常: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数入口"""
    try:
        logger.info("股票分析系统调试版本启动中...")
        
        # 检查系统环境
        logger.info(f"操作系统: {sys.platform}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {os.getcwd()}")
        display_env = os.environ.get('DISPLAY', '未设置')
        logger.info(f"DISPLAY环境变量: {display_env}")
        
        # 检查依赖
        if not check_dependencies():
            logger.error("依赖检查失败，系统退出")
            return 1
        
        # 设置PYTHONPATH环境变量，确保模块可以被找到
        logger.info("设置PYTHONPATH环境变量...")
        current_dir = os.getcwd()
        python_path = os.environ.get('PYTHONPATH', '')
        if current_dir not in python_path:
            os.environ['PYTHONPATH'] = f"{current_dir}:{python_path}"
        
        # 初始化应用
        logger.info("创建QApplication...")
        app = QApplication(sys.argv)
        
        logger.info("创建主应用窗口...")
        analyzer_app = StockAnalyzerApp()
        
        logger.info("显示主应用窗口...")
        analyzer_app.show()
        
        logger.info("应用程序进入主循环...")
        return app.exec_()
        
    except Exception as e:
        logger.critical(f"应用程序初始化失败: {e}")
        traceback.print_exc()
        
        # 如果可能，尝试创建一个QApplication来显示错误消息
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "启动失败", f"应用程序初始化失败: {e}")
        except:
            # 如果无法显示GUI错误消息，至少打印到控制台
            print(f"严重错误: 应用程序初始化失败: {e}")
            
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info(f"应用程序已退出，退出代码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"未捕获的异常: {e}")
        traceback.print_exc()
        sys.exit(1) 