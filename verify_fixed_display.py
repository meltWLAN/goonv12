#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel
from PyQt5.QtCore import QTimer, Qt
from smart_recommendation_ui import show_recommendation_ui

def main():
    print("===== 验证智能推荐系统显示修复 =====")
    
    app = QApplication(sys.argv)
    
    try:
        print("正在启动智能推荐系统...")
        window = show_recommendation_ui()
        
        # 定义验证函数
        def verify_display():
            widget = window.centralWidget()
            if not hasattr(widget, 'recommendations_table'):
                print("错误: 找不到推荐表格")
                QMessageBox.critical(window, "验证失败", "找不到推荐表格")
                return
                
            table = widget.recommendations_table
            row_count = table.rowCount()
            
            print(f"表格当前有 {row_count} 行数据")
            
            if row_count > 0:
                print("✓ 验证成功: 表格有数据显示!")
                
                # 显示前5行数据
                print("表格数据样本:")
                for row in range(min(5, row_count)):
                    code = table.item(row, 0).text() if table.item(row, 0) else "?"
                    name = table.item(row, 1).text() if table.item(row, 1) else "?"
                    score = table.item(row, 3).text() if table.item(row, 3) else "?"
                    print(f"  {code} {name} (评分: {score})")
                
                QMessageBox.information(
                    window, 
                    "验证成功", 
                    f"智能推荐系统表格显示正常，共显示 {row_count} 条推荐数据"
                )
            else:
                print("✗ 验证失败: 表格没有显示数据")
                QMessageBox.warning(
                    window,
                    "验证失败",
                    "表格没有显示数据，请尝试手动刷新"
                )
        
        # 设置延迟验证
        QTimer.singleShot(2000, verify_display)
        
        print("正在显示窗口...")
        return app.exec_()
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
