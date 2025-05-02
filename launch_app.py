#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统启动器
用于解决可能的GUI显示问题
"""

import os
import sys
import logging
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QProcess

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='launcher.log',
    filemode='w'
)
logger = logging.getLogger('AppLauncher')

class AppLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口
        self.setWindowTitle('股票分析系统启动器')
        self.setGeometry(300, 300, 400, 200)
        
        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标签
        title = QLabel('股票分析系统启动器')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 18px; font-weight: bold;')
        layout.addWidget(title)
        
        # 添加启动按钮
        self.launch_button = QPushButton('启动股票分析系统')
        self.launch_button.setStyleSheet('padding: 10px; font-size: 14px;')
        self.launch_button.clicked.connect(self.launch_app)
        layout.addWidget(self.launch_button)
        
        # 添加状态标签
        self.status_label = QLabel('等待启动...')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 初始化进程
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.finished.connect(self.handle_finish)
        
    def launch_app(self):
        """启动主应用程序"""
        try:
            self.status_label.setText('正在启动...')
            self.launch_button.setEnabled(False)
            
            logger.info('尝试启动应用程序')
            
            # 在当前目录启动app.py
            self.process.start('python', ['app.py'])
            
            self.status_label.setText('应用程序已启动！')
            logger.info('应用程序已启动')
            
        except Exception as e:
            logger.error(f'启动失败: {e}')
            self.status_label.setText(f'启动失败: {e}')
            self.launch_button.setEnabled(True)
    
    def handle_output(self):
        """处理标准输出"""
        data = self.process.readAllStandardOutput().data().decode()
        logger.info(f'应用输出: {data.strip()}')
    
    def handle_error(self):
        """处理错误输出"""
        data = self.process.readAllStandardError().data().decode()
        logger.error(f'应用错误: {data.strip()}')
    
    def handle_finish(self, exit_code, exit_status):
        """处理应用结束"""
        logger.info(f'应用程序已结束，退出代码: {exit_code}')
        self.status_label.setText(f'应用程序已结束，退出代码: {exit_code}')
        self.launch_button.setEnabled(True)

def main():
    """启动器入口点"""
    app = QApplication(sys.argv)
    launcher = AppLauncher()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 