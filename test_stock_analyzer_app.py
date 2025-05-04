#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证主应用程序中的智能推荐系统功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from stock_analyzer_app import StockAnalyzerApp

def main():
    """测试主应用程序中的智能推荐系统功能"""
    print("===== 测试主应用程序中的智能推荐系统功能 =====")
    print("正在启动股票分析器应用...")
    
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 创建主窗口实例
        window = StockAnalyzerApp()
        
        # 显示窗口
        window.show()
        
        print("股票分析器应用已启动")
        print("请在界面中点击「智能推荐系统」按钮测试功能")
        print("测试步骤：")
        print("1. 点击主界面右侧的「智能推荐系统」按钮")
        print("2. 观察智能推荐系统窗口是否正常打开")
        print("3. 测试智能推荐系统中的功能")
        print("4. 关闭智能推荐系统窗口，返回主界面")
        print("5. 关闭主应用窗口结束测试")
        
        # 运行应用程序事件循环
        sys.exit(app.exec_())
    except Exception as e:
        print(f"启动应用程序时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 