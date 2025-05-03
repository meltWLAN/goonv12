#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI调试程序
"""

import sys
import os
import platform
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt

def get_system_info():
    """获取系统信息"""
    info = []
    info.append(f"Python版本: {sys.version}")
    info.append(f"操作系统: {platform.system()} {platform.release()}")
    info.append(f"PyQt5版本: {get_pyqt_version()}")
    
    # 环境变量
    env_vars = []
    for key, value in os.environ.items():
        if key.startswith(('QT_', 'PYQT', 'PYTHON', 'DISPLAY')):
            env_vars.append(f"{key}={value}")
    
    if env_vars:
        info.append("\n环境变量:")
        info.extend(env_vars)
    
    return "\n".join(info)

def get_pyqt_version():
    """获取PyQt版本"""
    try:
        from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        return f"Qt: {QT_VERSION_STR}, PyQt: {PYQT_VERSION_STR}"
    except ImportError:
        return "未知"

def test_enhanced_sector():
    """测试增强版行业分析器"""
    try:
        from integrate_sector_analyzer import SectorAnalyzerIntegrator
        integrator = SectorAnalyzerIntegrator(prefer_enhanced=True)
        
        result = integrator.get_hot_sectors()
        if result['status'] == 'success':
            return f"增强版行业分析器测试成功\n热门行业数量: {len(result['data']['hot_sectors'])}"
        else:
            return f"增强版行业分析器测试失败: {result.get('message', '未知错误')}"
    except Exception as e:
        return f"增强版行业分析器测试异常: {str(e)}"

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI调试程序")
        self.setGeometry(100, 100, 800, 500)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标签页控件
        tabs = QTabWidget()
        
        # 系统信息标签页
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        # 系统信息
        system_info = QTextEdit()
        system_info.setReadOnly(True)
        system_info.setText(get_system_info())
        system_layout.addWidget(system_info)
        
        tabs.addTab(system_tab, "系统信息")
        
        # 组件测试标签页
        test_tab = QWidget()
        test_layout = QVBoxLayout(test_tab)
        
        # 增强版行业分析器测试
        test_sector_btn = QPushButton("测试增强版行业分析器")
        test_sector_result = QTextEdit()
        test_sector_result.setReadOnly(True)
        
        def on_test_sector():
            test_sector_result.setText("正在测试...")
            test_sector_result.repaint()
            result = test_enhanced_sector()
            test_sector_result.setText(result)
        
        test_sector_btn.clicked.connect(on_test_sector)
        
        test_layout.addWidget(test_sector_btn)
        test_layout.addWidget(test_sector_result)
        
        tabs.addTab(test_tab, "组件测试")
        
        main_layout.addWidget(tabs)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 