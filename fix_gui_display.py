#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复GUI显示问题的脚本
"""

import os
import sys
import signal
import subprocess
import platform
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='gui_fix.log',
    filemode='w'
)
logger = logging.getLogger('GUIFix')

def signal_handler(sig, frame):
    """信号处理"""
    logger.info("收到中断信号，程序退出")
    sys.exit(0)

def setup_environment():
    """设置环境变量"""
    logger.info("设置环境变量")
    
    os_name = platform.system()
    logger.info(f"操作系统: {os_name}")
    
    # macOS特有的Qt显示问题修复
    if os_name == 'Darwin':
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
        
        # 设置应用程序名称，避免dock图标问题
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = 'venv/lib/python3.13/site-packages/PyQt5/Qt5/plugins/platforms'
        
        logger.info("已设置macOS特有环境变量")
    
    # 通用设置
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    return True

def fix_app_display():
    """尝试修复应用程序显示问题"""
    try:
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        
        # 设置环境变量
        if not setup_environment():
            logger.error("设置环境变量失败")
            return False
        
        # 修复GUI问题的简单测试程序
        logger.info("创建简单测试窗口")
        fix_code = """
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# 创建应用程序
app = QApplication(sys.argv)

# 创建主窗口
window = QMainWindow()
window.setWindowTitle("GUI修复测试")
window.setGeometry(100, 100, 400, 200)

# 创建中央部件和布局
central_widget = QWidget()
layout = QVBoxLayout(central_widget)

# 添加标签
label = QLabel("如果你看到这个窗口，说明GUI显示正常！")
label.setAlignment(Qt.AlignCenter)
layout.addWidget(label)

# 添加按钮
launch_btn = QPushButton("启动股票分析系统")
layout.addWidget(launch_btn)

# 定义启动函数
def launch_main_app():
    window.close()
    import subprocess
    import sys
    subprocess.Popen([sys.executable, 'app.py'])

# 连接按钮点击事件
launch_btn.clicked.connect(launch_main_app)

window.setCentralWidget(central_widget)
window.show()

sys.exit(app.exec_())
"""
        
        # 保存测试程序
        with open('gui_test_fix.py', 'w') as f:
            f.write(fix_code)
        
        # 运行测试程序
        logger.info("运行测试程序")
        subprocess.Popen([sys.executable, 'gui_test_fix.py'])
        
        return True
        
    except Exception as e:
        logger.error(f"修复应用程序显示问题时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("正在修复GUI显示问题...")
    success = fix_app_display()
    
    if success:
        print("已成功启动GUI测试窗口。请根据测试窗口中的提示继续操作。")
    else:
        print("修复GUI显示问题失败，请查看gui_fix.log获取详细信息。") 