#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from smart_recommendation_ui import show_recommendation_ui, SmartRecommendationWidget

class TestHelper:
    """测试辅助类，提供工具方法"""
    
    @staticmethod
    def verify_table_content(widget):
        """验证表格内容"""
        print("\n正在验证表格内容...")
        if not hasattr(widget, 'recommendations_table'):
            print("错误: 控件没有recommendations_table属性")
            return False
            
        table = widget.recommendations_table
        row_count = table.rowCount()
        col_count = table.columnCount()
        
        print(f"表格大小: {row_count}行 x {col_count}列")
        
        if row_count == 0:
            print("警告: 表格没有行数据!")
            return False
            
        # 检查前几行数据
        max_rows = min(5, row_count)
        print(f"前{max_rows}行数据:")
        for row in range(max_rows):
            row_data = []
            for col in range(min(4, col_count)):  # 只显示前4列
                item = table.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("空")
            print(f"  行{row}: {' | '.join(row_data)}")
            
        return row_count > 0

    @staticmethod
    def force_table_refresh(widget):
        """强制表格刷新"""
        print("正在强制刷新表格...")
        if hasattr(widget, 'load_recommendations'):
            try:
                print("调用load_recommendations强制刷新...")
                widget.load_recommendations()
                return True
            except Exception as e:
                print(f"刷新失败: {str(e)}")
                return False
        else:
            print("错误: 控件没有load_recommendations方法")
            return False

def main():
    print("===== 测试智能推荐系统显示 =====")
    print("正在启动测试...")
    
    try:
        app = QApplication(sys.argv)
        
        # 添加调试信息
        print("正在创建推荐系统窗口...")
        main_window = show_recommendation_ui()
        
        # 获取中央控件(SmartRecommendationWidget)
        recommendation_widget = main_window.centralWidget()
        if not isinstance(recommendation_widget, SmartRecommendationWidget):
            print(f"错误: 中央控件类型不正确: {type(recommendation_widget)}")
            return
            
        print("智能推荐控件创建成功")
        
        # 设置延迟检查计时器
        def check_table():
            print("\n执行表格检查...")
            if not TestHelper.verify_table_content(recommendation_widget):
                print("表格内容验证失败，尝试强制刷新...")
                TestHelper.force_table_refresh(recommendation_widget)
                
                # 再次检查
                if TestHelper.verify_table_content(recommendation_widget):
                    print("强制刷新后表格显示正常")
                    QMessageBox.information(main_window, "测试成功", "表格显示正常，已成功展示收录的股票")
                else:
                    print("强制刷新后表格仍然为空")
                    QMessageBox.warning(main_window, "测试失败", "表格未显示推荐数据，请检查调试输出")
            else:
                print("表格内容验证成功")
                QMessageBox.information(main_window, "测试成功", "表格显示正常，已成功展示收录的股票")
        
        # 延迟2秒后检查表格，确保UI完全加载
        QTimer.singleShot(2000, check_table)
        
        print("窗口创建成功，等待显示...")
        print("程序将继续运行，请检查窗口是否正确显示股票推荐")
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
