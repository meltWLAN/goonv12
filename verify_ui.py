#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证智能推荐系统显示修复
确认"智能推荐系统"现在能够正确显示收录的股票
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from smart_recommendation_ui import show_recommendation_ui, SmartRecommendationWidget

def verify_recommendations_display():
    """验证推荐显示是否正常"""
    print("\n===== 验证智能推荐系统显示 =====")
    print("正在启动应用...")
    
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 创建主窗口
        print("创建智能推荐系统窗口...")
        window = show_recommendation_ui()
        
        # 获取中央部件
        recommendation_widget = window.centralWidget()
        if not isinstance(recommendation_widget, SmartRecommendationWidget):
            print(f"错误: 中央控件类型不正确: {type(recommendation_widget)}")
            return 1
            
        print("智能推荐控件创建成功")
        
        # 定义验证函数
        def verify_table():
            print("\n执行表格验证...")
            if not hasattr(recommendation_widget, 'recommendations_table'):
                print("错误: 控件没有recommendations_table属性")
                QMessageBox.critical(window, "验证失败", "找不到推荐表格")
                return
                
            table = recommendation_widget.recommendations_table
            row_count = table.rowCount()
            col_count = table.columnCount()
            
            print(f"表格大小: {row_count}行 x {col_count}列")
            
            if row_count > 0:
                print("✓ 验证成功: 表格有数据显示!")
                
                # 显示前5行数据
                print("表格数据样本:")
                for row in range(min(5, row_count)):
                    data = []
                    for col in range(min(5, col_count)):
                        item = table.item(row, col)
                        if item:
                            data.append(item.text())
                        else:
                            data.append("?")
                    print(f"  行{row}: {' | '.join(data)}")
                
                QMessageBox.information(
                    window, 
                    "验证成功", 
                    f"智能推荐系统表格显示正常，共显示 {row_count} 条推荐数据"
                )
            else:
                print("✗ 验证失败: 表格没有显示数据")
                
                # 尝试强制刷新
                print("尝试强制刷新表格...")
                recommendation_widget.load_recommendations()
                
                # 再次检查
                time.sleep(1)  # 等待刷新完成
                new_row_count = table.rowCount()
                if new_row_count > 0:
                    print(f"✓ 强制刷新成功，现在有 {new_row_count} 行数据")
                    QMessageBox.information(
                        window,
                        "强制刷新成功",
                        f"表格现在有 {new_row_count} 条推荐数据"
                    )
                else:
                    print("✗ 强制刷新后仍无数据")
                    QMessageBox.warning(
                        window,
                        "验证失败",
                        "表格没有显示数据，即使强制刷新后"
                    )
        
        # 延迟验证，等待UI完全加载
        QTimer.singleShot(2000, verify_table)
        
        print("窗口创建成功，等待显示...")
        return app.exec_()
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(verify_recommendations_display()) 