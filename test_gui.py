#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

def main():
    """测试PyQt5 GUI显示"""
    app = QApplication(sys.argv)
    
    # 创建窗口
    window = QWidget()
    window.setWindowTitle('PyQt5测试')
    window.setGeometry(100, 100, 400, 200)
    
    # 创建布局
    layout = QVBoxLayout()
    
    # 添加标签
    label = QLabel('这是一个PyQt5测试程序')
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    
    # 设置窗口布局
    window.setLayout(layout)
    
    # 显示窗口
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 