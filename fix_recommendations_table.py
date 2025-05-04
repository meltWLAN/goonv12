#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复智能推荐系统表格显示问题
专注于解决表格不显示股票的问题
"""

import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout

def fix_smart_recommendation_ui():
    """修复智能推荐UI中的表格显示问题"""
    target_file = "smart_recommendation_ui.py"
    backup_file = "smart_recommendation_ui.py.bak"
    
    print(f"正在备份 {target_file} 到 {backup_file}...")
    try:
        # 备份原文件
        with open(target_file, "r", encoding="utf-8") as f:
            original_content = f.read()
            
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(original_content)
        
        print(f"✓ 已备份原文件")
        
        # 修改load_recommendations方法，添加调试输出
        modified_lines = []
        inside_load_recommendations = False
        inside_filter_recommendations = False
        table_count_line_found = False
        
        for line in original_content.splitlines():
            modified_lines.append(line)
            
            # 识别是否在load_recommendations方法内
            if "def load_recommendations(self):" in line:
                inside_load_recommendations = True
                # 添加调试输出
                modified_lines.append('        print("执行load_recommendations方法...")')
                
            # 识别是否在filter_recommendations方法内
            elif "def filter_recommendations(self, recommendations):" in line:
                inside_filter_recommendations = True
                # 添加调试输出
                modified_lines.append('        print(f"过滤和排序 {len(recommendations)} 个推荐...")')
                
            # 在表格清空行后添加调试
            elif inside_load_recommendations and "self.recommendations_table.setRowCount(0)" in line:
                table_count_line_found = True
                modified_lines.append('        print("已清空表格，准备添加推荐数据")')
                
            # 在表格填充前添加调试
            elif inside_load_recommendations and "for i, rec in enumerate(filtered_recs):" in line:
                modified_lines.append(f'        print(f"开始填充表格，共有 {{len(filtered_recs)}} 个推荐要显示")')
                
            # 在表格填充过程中添加调试
            elif inside_load_recommendations and "self.recommendations_table.insertRow(i)" in line:
                modified_lines.append('            if i == 0: print(f"插入第一行: {rec.stock_code} {rec.stock_name}")')
                
            # 在排序过程中添加调试
            elif inside_filter_recommendations and "filtered.sort(" in line:
                modified_lines.append('        print(f"应用排序: {sort_option}, 排序前有 {len(filtered)} 个推荐")')
                
            # 在排序返回前添加调试
            elif inside_filter_recommendations and "return filtered" in line:
                modified_lines.append('        print(f"过滤和排序完成，返回 {len(filtered)} 个推荐")')
                inside_filter_recommendations = False
                
            # 结束load_recommendations方法跟踪
            elif inside_load_recommendations and line.strip().startswith("def "):
                inside_load_recommendations = False
        
        # 检查是否找到表格清空行，如果没找到，可能需要添加
        if not table_count_line_found:
            print("⚠️ 没有找到表格行数设置代码，可能需要手动检查")
        
        # 写入修改后的内容
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("\n".join(modified_lines))
            
        print(f"✓ 已修改 {target_file}，添加了调试输出")
        return True
    except Exception as e:
        print(f"✗ 修改文件时发生错误: {str(e)}")
        traceback.print_exc()
        return False

def create_test_table_app():
    """创建一个简单的测试应用来测试表格功能"""
    test_code = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

class TestTableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试表格显示")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["股票代码", "股票名称", "价格", "评分", "来源"])
        
        layout.addWidget(self.table)
        
        # 填充测试数据
        self.fill_test_data()
    
    def fill_test_data(self):
        print("开始填充测试数据...")
        
        # 测试数据
        test_data = [
            ("000001", "平安银行", "20.50", "95.0", "测试来源"),
            ("600036", "招商银行", "35.80", "92.0", "测试来源"),
            ("601318", "中国平安", "48.25", "90.0", "测试来源"),
            ("000858", "五粮液", "155.30", "88.0", "测试来源"),
            ("600519", "贵州茅台", "1800.00", "85.0", "测试来源")
        ]
        
        # 清空表格
        self.table.setRowCount(0)
        print(f"表格行数已设置为0")
        
        # 添加数据
        for i, (code, name, price, score, source) in enumerate(test_data):
            print(f"添加行 {i}: {code} {name}")
            self.table.insertRow(i)
            
            self.table.setItem(i, 0, QTableWidgetItem(code))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(price))
            self.table.setItem(i, 3, QTableWidgetItem(score))
            self.table.setItem(i, 4, QTableWidgetItem(source))
        
        print(f"已添加 {len(test_data)} 行数据")

def main():
    app = QApplication(sys.argv)
    window = TestTableApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
"""
    
    with open("test_table_app.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    print("✓ 已创建表格测试应用: test_table_app.py")
    print("可以运行 'python test_table_app.py' 来测试基本表格功能")
    return True

def main():
    """主函数"""
    print("===== 智能推荐系统表格显示修复工具 =====")
    
    print("修复智能推荐UI文件中的表格显示问题...")
    if fix_smart_recommendation_ui():
        print("✓ UI文件修复完成")
    else:
        print("✗ UI文件修复失败")
    
    print("创建表格功能测试应用...")
    if create_test_table_app():
        print("✓ 测试应用创建完成")
    else:
        print("✗ 测试应用创建失败")
    
    print("\n修复步骤完成，请按以下步骤进行测试:")
    print("1. 运行 'python test_table_app.py' 测试基本表格功能")
    print("2. 如果基本表格测试正常，运行 'python test_recommendations_display.py' 测试智能推荐系统")
    print("3. 如果问题依然存在，检查调试输出，查找可能的问题原因")

if __name__ == "__main__":
    main() 