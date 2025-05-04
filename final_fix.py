#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能推荐系统表格显示最终修复工具
针对股票不显示的问题提供最终解决方案
"""

import os
import sys
import json
import traceback

def backup_file(filename):
    """备份文件"""
    backup_filename = f"{filename}.bak"
    print(f"备份 {filename} 到 {backup_filename}...")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        with open(backup_filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ 文件备份成功")
        return content
    except Exception as e:
        print(f"✗ 文件备份失败: {str(e)}")
        return None

def fix_ui_file():
    """修复智能推荐UI文件中的表格显示问题"""
    filename = "smart_recommendation_ui.py"
    content = backup_file(filename)
    if not content:
        return False
        
    print(f"正在修复 {filename}...")
    try:
        # 针对性修复表格相关方法
        lines = content.splitlines()
        modified_lines = []
        inside_load_recommendations = False
        inside_filter = False
        
        # 查找特定问题
        fixed_table_columns = False
        fixed_add_recommendation = False
        load_rec_definition_found = False
        
        for i, line in enumerate(lines):
            # 检测是否进入load_recommendations方法
            if "def load_recommendations(self):" in line:
                inside_load_recommendations = True
                load_rec_definition_found = True
            
            # 检测是否进入filter_recommendations方法    
            elif "def filter_recommendations(self, recommendations):" in line:
                inside_filter = True
                
            # 检查是否有表格列数设置问题
            elif "self.recommendations_table = QTableWidget(0, " in line:
                if "9)" not in line:  # 确认列数是否正确
                    print("⚠️ 表格列数可能不正确，正在修复...")
                    line = line.replace("QTableWidget(0, ", "QTableWidget(0, 9")
                    fixed_table_columns = True
            
            # 添加修复 - 确保表格被正确初始化并显示
            elif inside_load_recommendations and "self.recommendations_table.setRowCount(0)" in line:
                modified_lines.append(line)
                modified_lines.append('        print(f"表格已清空，准备填充 {len(filtered_recs)} 条记录")')
                modified_lines.append('        # 设置表格可见性，确保表格显示')
                modified_lines.append('        self.recommendations_table.setVisible(True)')
                modified_lines.append('        # 更新UI')
                modified_lines.append('        QApplication.processEvents()')
                continue
                
            # 修复表格单元格创建方法
            elif inside_load_recommendations and "self.recommendations_table.setItem" in line:
                if "QTableWidgetItem" not in line:
                    # 修复缺少QTableWidgetItem的问题
                    parts = line.split("(")
                    if len(parts) > 1:
                        item_value = parts[1].split(")")[0]
                        fixed_line = f"{parts[0]}(QTableWidgetItem({item_value}))"
                        line = fixed_line
                
            # 确保过滤方法正确返回结果    
            elif inside_filter and "return filtered" in line:
                inside_filter = False
                modified_lines.append('        print(f"过滤后的推荐数: {len(filtered)}")')
                
            # 结束load_recommendations方法的跟踪    
            elif inside_load_recommendations and line.strip().startswith("def "):
                inside_load_recommendations = False
            
            modified_lines.append(line)
        
        # 如果没有找到load_recommendations方法定义，需要添加检查
        if not load_rec_definition_found:
            print("⚠️ 未找到load_recommendations方法定义，需要进一步检查代码")
            
        # 添加必要的导入
        if "from PyQt5.QtCore import QTimer" not in content:
            for i, line in enumerate(modified_lines):
                if "from PyQt5.QtCore import " in line:
                    modified_lines[i] = line.rstrip() + ", QTimer\n"
                    break
                    
        # 写入修改后的文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(modified_lines))
            
        print(f"✓ 已修复 {filename}")
        if fixed_table_columns:
            print("  - 修复了表格列数设置")
        if fixed_add_recommendation:
            print("  - 修复了添加推荐方法")
        
        return True
    except Exception as e:
        print(f"✗ 修复文件失败: {str(e)}")
        traceback.print_exc()
        return False

def check_data_integrity():
    """检查推荐数据完整性"""
    data_file = "smart_recommendation_data/recommendations.json"
    print(f"检查数据文件 {data_file}...")
    
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        current_recs = data.get("current", {})
        if not current_recs:
            print("⚠️ 警告: 没有当前推荐数据")
            return False
            
        print(f"✓ 成功解析数据文件，包含 {len(current_recs)} 个推荐")
        
        # 检查一个样本推荐
        sample_key = next(iter(current_recs))
        sample = current_recs[sample_key]
        
        required_fields = ["stock_code", "stock_name", "recommendation_date", 
                           "entry_price", "target_price", "stop_loss", "tags"]
                           
        for field in required_fields:
            if field not in sample:
                print(f"⚠️ 警告: 推荐数据缺少必填字段 '{field}'")
                return False
                
        # 检查日期格式是否正确
        if "recommendation_date" in sample:
            date_str = sample["recommendation_date"]
            if not date_str or len(date_str) < 10:
                print(f"⚠️ 警告: 推荐日期格式可能有问题: {date_str}")
                
        print("✓ 推荐数据结构完整")
        return True
    except Exception as e:
        print(f"✗ 检查数据完整性失败: {str(e)}")
        return False

def create_verification_script():
    """创建验证脚本"""
    filename = "verify_fixed_display.py"
    print(f"创建验证脚本 {filename}...")
    
    script_content = """#!/usr/bin/env python
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
"""

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(script_content)
        print(f"✓ 已创建验证脚本 {filename}")
        return True
    except Exception as e:
        print(f"✗ 创建验证脚本失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("===== 智能推荐系统表格显示最终修复工具 =====")
    
    success = True
    
    print("\n步骤1: 检查数据完整性")
    if not check_data_integrity():
        success = False
        print("⚠️ 数据完整性检查失败，但会继续尝试修复UI文件")
    
    print("\n步骤2: 修复UI文件")
    if not fix_ui_file():
        success = False
        print("⚠️ UI文件修复失败")
    
    print("\n步骤3: 创建验证脚本")
    if not create_verification_script():
        success = False
        print("⚠️ 验证脚本创建失败")
    
    print("\n===== 修复结果 =====")
    if success:
        print("✓ 所有修复步骤完成")
        print("\n请使用以下命令验证修复效果:")
        print("python verify_fixed_display.py")
    else:
        print("⚠️ 部分修复步骤失败")
        print("仍然可以尝试运行验证脚本进行测试:")
        print("python verify_fixed_display.py")

if __name__ == "__main__":
    main() 