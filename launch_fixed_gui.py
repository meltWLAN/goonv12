#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复版GUI启动脚本
设置必要的环境变量并启动GUI
"""

import os
import sys
import subprocess
import platform

def setup_environment():
    """设置运行环境"""
    # 获取操作系统信息
    os_name = platform.system()
    
    if os_name == 'Darwin':  # macOS
        # 设置QT环境变量，修复macOS显示问题
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    
    # 其他系统可以添加对应的环境变量设置
    
    # 如果需要指定其他环境变量，可以在这里添加
    # os.environ['变量名'] = '值'

def launch_gui():
    """启动GUI"""
    try:
        print("正在启动股票分析系统...")
        
        # 尝试直接导入并启动GUI
        try:
            from stock_analysis_gui import main
            main()
        except Exception as e:
            print(f"直接启动失败: {e}")
            
            # 回退方案：使用子进程启动
            print("尝试使用子进程启动...")
            subprocess.run([sys.executable, 'stock_analysis_gui.py'])
    
    except Exception as e:
        print(f"启动GUI失败: {e}")
        
        # 如果GUI启动失败，尝试启动主应用
        try:
            print("尝试启动主应用...")
            subprocess.run([sys.executable, 'app.py'])
        except Exception as e2:
            print(f"启动应用程序失败: {e2}")
            return 1
    
    return 0

if __name__ == "__main__":
    # 设置环境
    setup_environment()
    
    # 启动GUI
    sys.exit(launch_gui()) 