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

def main():
    """主函数"""
    try:
        # 保存进程ID
        save_pid()
        
        # 记录启动信息
        logger.info("系统启动")
        
        # 启动GUI (如果启动参数不包含--no-gui)
        if '--no-gui' not in sys.argv:
            # 启动GUI
            from stock_analysis_gui import launch_gui
            
            # 启动GUI，删除行业分析器参数
            launch_gui()
            
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