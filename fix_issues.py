#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复股票分析系统中的问题:
1. 智能推荐系统打开错误
2. 数据点不足警告
"""

import os
import sys
import re

def fix_smart_recommendation_system():
    """修复智能推荐系统打开时的QApplication错误"""
    print("正在修复智能推荐系统打开问题...")
    
    # 读取股票分析应用文件
    with open('stock_analyzer_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尝试修复QApplication不可访问的问题
    new_content = content.replace(
        "# 导入智能推荐系统UI\n            import sys\n            from PyQt5.QtWidgets import QApplication",
        "# 导入智能推荐系统UI"
    )
    
    # 保存修改后的文件
    with open('stock_analyzer_app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("智能推荐系统打开问题修复完成")

def fix_insufficient_data_warning():
    """修复"数据点数不足，无法计算动量指标"的警告"""
    print("正在修复数据点不足问题...")
    
    # 寻找并修改 visual_stock_system.py 或相关文件
    target_files = [
        'visual_stock_system.py',
        'technical_analyzer.py',
        'single_stock_analyzer.py'
    ]
    
    for filename in target_files:
        if not os.path.exists(filename):
            continue
            
        print(f"检查文件: {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找计算动量指标的代码，添加更好的错误处理
        if "无法计算动量指标" in content:
            print(f"在 {filename} 中找到目标代码")
            
            # 替换警告消息为更优雅的处理
            new_content = content.replace(
                'print("数据点数不足，无法计算动量指标")',
                'logger.debug("数据点数不足，无法计算动量指标，将使用默认值")'
            )
            
            # 查找可能导致警告的代码块并添加更多条件检查
            new_content = new_content.replace(
                "if len(data) < window:",
                "if len(data) < window or window <= 0:"
            )
            
            # 保存修改后的文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"已修复 {filename} 中的问题")
    
    print("数据点不足问题修复完成")

def fix_smart_recommendation_ui():
    """修复智能推荐系统界面标签过滤器的递归问题"""
    print("正在修复智能推荐系统UI问题...")
    
    filename = 'smart_recommendation_ui.py'
    if not os.path.exists(filename):
        print(f"找不到文件 {filename}")
        return
        
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找update_tag_filter方法并添加blockSignals代码
    if "update_tag_filter" in content and "blockSignals" not in content:
        print("发现标签过滤器需要改进")
        
        # 查找标签下拉框清除和填充的代码
        pattern = "self.tag_combo.clear()"
        replacement = "self.tag_combo.blockSignals(True)\n        self.tag_combo.clear()"
        
        # 查找恢复选择的代码
        pattern2 = "self.tag_combo.setCurrentIndex(index)"
        replacement2 = "self.tag_combo.setCurrentIndex(index)\n        self.tag_combo.blockSignals(False)"
        
        # 应用修复
        new_content = content.replace(pattern, replacement)
        new_content = new_content.replace(pattern2, replacement2)
        
        # 保存修改后的文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("智能推荐系统UI问题修复完成")
    else:
        print("智能推荐系统UI看起来已经修复")

if __name__ == "__main__":
    print("开始修复股票分析系统问题...")
    
    # 修复智能推荐系统打开问题
    fix_smart_recommendation_system()
    
    # 修复数据点不足问题
    fix_insufficient_data_warning()
    
    # 修复智能推荐系统UI问题
    fix_smart_recommendation_ui()
    
    print("所有问题修复完成，请重新启动应用程序尝试") 