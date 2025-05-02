#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用入口点
"""

import os
import sys
import time
import json
import signal
import logging
import traceback
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='system.log',
    filemode='a'
)
logger = logging.getLogger('AppMain')

def save_pid(pid_file: str = 'app.pid'):
    """保存进程ID到文件中
    
    Args:
        pid_file: PID文件路径
    """
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logger.error(f"保存PID文件失败: {e}")

def initialize_sector_analyzer(prefer_enhanced=True) -> Dict[str, Any]:
    """初始化行业分析器
    
    Args:
        prefer_enhanced: 是否优先使用增强版行业分析器
        
    Returns:
        初始化状态信息
    """
    try:
        # 导入行业分析器集成模块
        from integrate_sector_analyzer import SectorAnalyzerIntegrator
        
        # 初始化集成器
        integrator = SectorAnalyzerIntegrator(prefer_enhanced=prefer_enhanced)
        
        # 检查哪个版本可用
        simple_available = integrator.simple_available
        enhanced_available = integrator.enhanced_available
        
        if enhanced_available and prefer_enhanced:
            logger.info("系统将使用增强版行业分析器")
            analyzer_type = 'enhanced'
        elif simple_available:
            logger.info("系统将使用简化版行业分析器")
            analyzer_type = 'simple'
        else:
            logger.error("没有可用的行业分析器")
            analyzer_type = 'none'
        
        # 尝试获取热门行业以验证分析器工作正常
        result = integrator.get_hot_sectors()
        if result['status'] == 'success':
            hot_count = len(result['data']['hot_sectors'])
            logger.info(f"成功获取 {hot_count} 个热门行业")
            test_success = True
        else:
            logger.error(f"获取热门行业失败: {result.get('message')}")
            test_success = False
        
        return {
            'analyzer_type': analyzer_type,
            'simple_available': simple_available,
            'enhanced_available': enhanced_available,
            'test_success': test_success,
            'integrator': integrator if test_success else None
        }
    except Exception as e:
        logger.error(f"初始化行业分析器失败: {e}")
        logger.error(traceback.format_exc())
        return {
            'analyzer_type': 'none',
            'simple_available': False,
            'enhanced_available': False,
            'test_success': False,
            'integrator': None
        }

def main():
    """主函数"""
    try:
        # 保存进程ID
        save_pid()
        
        # 记录启动信息
        logger.info("系统启动")
        
        # 初始化行业分析器 (优先使用增强版)
        sector_info = initialize_sector_analyzer(prefer_enhanced=True)
        
        if sector_info['test_success']:
            logger.info(f"行业分析器初始化成功，类型: {sector_info['analyzer_type']}")
        else:
            logger.warning("行业分析器初始化失败或测试不通过")
        
        # 启动GUI (如果启动参数不包含--no-gui)
        if '--no-gui' not in sys.argv:
            # 启动GUI
            from stock_analysis_gui import launch_gui
            
            # 将行业分析器传递给GUI
            launch_gui(sector_integrator=sector_info.get('integrator'))
            
            logger.info("GUI已启动")
        else:
            logger.info("以无GUI模式启动")
            
            # 在此处添加命令行处理逻辑
            
            # 保持主线程运行
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("收到中断信号，系统退出")
    except Exception as e:
        logger.error(f"系统运行出错: {e}")
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 