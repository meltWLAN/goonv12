#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt5显示测试程序
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("PyQt5显示测试")
    window.setGeometry(100, 100, 400, 200)
    
    # 创建中央部件和布局
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # 添加标签
    label = QLabel("如果你能看到这个窗口，PyQt5显示功能正常工作！")
    layout.addWidget(label)
    
    window.setCentralWidget(central_widget)
    
    # 显示窗口
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 