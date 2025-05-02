#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试PyQt5显示问题
"""

import sys
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                           QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtCore import Qt, PYQT_VERSION_STR, QT_VERSION_STR
from PyQt5.QtGui import QFont

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='qt_display_test.log',
    filemode='w'
)
logger = logging.getLogger('QtTest')

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("初始化测试窗口")
        
        # 窗口设置
        self.setWindowTitle('Qt显示测试')
        self.setGeometry(300, 300, 500, 400)
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建布局
        layout = QVBoxLayout(self.central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title = QLabel('PyQt5显示测试')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('PingFang SC', 18, QFont.Bold))
        layout.addWidget(title)
        
        # 添加显示信息按钮
        info_button = QPushButton('显示系统信息')
        info_button.clicked.connect(self.show_info)
        layout.addWidget(info_button)
        
        # 添加错误测试按钮
        error_button = QPushButton('测试错误处理')
        error_button.clicked.connect(self.test_error)
        layout.addWidget(error_button)
        
        # 添加退出按钮
        quit_button = QPushButton('退出')
        quit_button.clicked.connect(self.close)
        layout.addWidget(quit_button)
        
        # 添加状态标签
        self.status_label = QLabel('窗口已创建')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        logger.info("窗口初始化完成")
    
    def show_info(self):
        """显示系统信息"""
        logger.info("显示系统信息")
        try:
            info = f"Python版本: {sys.version}\n"
            info += f"PyQt版本: {PYQT_VERSION_STR}\n"
            info += f"Qt版本: {QT_VERSION_STR}\n"
            info += f"操作系统: {sys.platform}\n"
            info += f"当前目录: {os.getcwd()}\n"
            info += f"环境变量 DISPLAY: {os.environ.get('DISPLAY', '未设置')}\n"
            
            self.status_label.setText("已显示系统信息")
            QMessageBox.information(self, "系统信息", info)
            logger.info("系统信息已显示")
        except Exception as e:
            logger.error(f"显示系统信息时出错: {e}")
            self.status_label.setText(f"错误: {e}")
    
    def test_error(self):
        """测试错误处理"""
        logger.info("测试错误处理")
        try:
            # 故意制造一个错误
            result = 1 / 0
        except Exception as e:
            logger.error(f"测试错误: {e}")
            QMessageBox.critical(self, "错误测试", f"捕获到错误: {e}")
            self.status_label.setText("错误测试成功")

def main():
    """程序入口"""
    logger.info("应用程序启动")
    
    # 将日志同时输出到控制台
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    try:
        app = QApplication(sys.argv)
        logger.info("QApplication已创建")
        
        window = TestWindow()
        logger.info("准备显示窗口")
        
        window.show()
        logger.info("窗口已显示")
        
        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"应用程序出错: {e}")
        print(f"严重错误: {e}")

if __name__ == '__main__':
    main() 