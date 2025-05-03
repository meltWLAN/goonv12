#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复enhanced_stock_review.py中的缩进问题
该脚本读取原文件，修复缩进，并保存到新文件
"""

import re
import os
import sys
from datetime import datetime

def fix_enhanced_stock_review():
    """修复enhanced_stock_review.py文件中的缩进问题"""
    
    # 文件路径
    original_file = 'enhanced_stock_review.py'
    backup_file = f'enhanced_stock_review_{datetime.now().strftime("%Y%m%d%H%M%S")}.py.bak'
    fixed_file = 'enhanced_stock_review.py.new'
    
    # 确保原文件存在
    if not os.path.exists(original_file):
        print(f"错误：找不到文件 {original_file}")
        return False
    
    # 创建备份
    try:
        with open(original_file, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"已创建备份：{backup_file}")
    except Exception as e:
        print(f"创建备份失败：{str(e)}")
        return False
    
    # 读取文件内容
    try:
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败：{str(e)}")
        return False
    
    # 查找类定义结束位置
    class_pattern = r'class EnhancedStockReview\(StockReview\):'
    match = re.search(class_pattern, content)
    if not match:
        print("错误：找不到 EnhancedStockReview 类定义")
        return False
    
    class_start = match.start()
    
    # 查找类内部的最后一个正确缩进的方法
    methods = [
        'integrate_with_ui',
        'get_enhanced_performance_summary',
        'visualize_enhanced_performance'
    ]
    
    last_method_pattern = None
    for method in methods:
        pattern = r'def ' + method + r'\(self,.*?\):'
        match = re.search(pattern, content)
        if match and (last_method_pattern is None or match.start() > last_method_pattern.start()):
            last_method_pattern = match
    
    if last_method_pattern is None:
        print("错误：找不到类内部方法")
        return False
    
    # 查找最后一个正确方法的代码块
    indent_pattern = r'^(\s+)def'
    indentation = ""
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if last_method_pattern.group(0) in line:
            for j in range(i+1, len(lines)):
                match = re.match(indent_pattern, lines[j])
                if match:  # 找到了下一个方法定义
                    break
                if lines[j].strip() == "":  # 空行
                    continue
                # 找到方法内部的第一行代码，获取缩进
                indentation = re.match(r'^(\s+)', lines[j])
                if indentation:
                    indentation = indentation.group(1)
                    break
            break
    
    if not indentation:
        print("错误：无法确定缩进格式")
        return False
    
    # 找到需要修复的方法
    problem_methods = [
        'analyze_with_volume_price_strategy',
        '_get_market_status_from_analysis',
        'integrate_with_ui'
    ]
    
    # 替换不正确缩进的方法
    fixed_content = content
    for method in problem_methods:
        pattern = r'^def ' + method + r'\(self,.*?\):'
        match = re.search(pattern, fixed_content, re.MULTILINE)
        if match:
            # 替换方法定义行的缩进
            fixed_content = fixed_content.replace(match.group(0), indentation + match.group(0)[4:])
            
            # 查找方法体
            method_start = match.start()
            next_method_pattern = r'^def '
            next_method_match = re.search(next_method_pattern, fixed_content[method_start+1:], re.MULTILINE)
            
            if next_method_match:
                method_end = method_start + 1 + next_method_match.start()
            else:
                method_end = len(fixed_content)
            
            method_body = fixed_content[method_start:method_end]
            
            # 给方法体的每一行添加适当的缩进
            fixed_method_body = ""
            for line in method_body.split('\n'):
                if line.startswith('def '):
                    fixed_method_body += indentation + line[4:] + '\n'
                elif line.strip() == "":
                    fixed_method_body += line + '\n'
                else:
                    fixed_method_body += indentation + indentation + line.lstrip() + '\n'
            
            # 替换方法体
            fixed_content = fixed_content[:method_start] + fixed_method_body.rstrip('\n') + fixed_content[method_end:]
    
    # 保存修复后的文件
    try:
        with open(fixed_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"已保存修复后的文件：{fixed_file}")
    except Exception as e:
        print(f"保存文件失败：{str(e)}")
        return False
    
    # 替换原文件
    try:
        os.replace(fixed_file, original_file)
        print(f"已用修复后的文件替换原文件")
        return True
    except Exception as e:
        print(f"替换原文件失败：{str(e)}")
        return False

# 执行修复
if __name__ == "__main__":
    print("开始修复 enhanced_stock_review.py 文件...")
    if fix_enhanced_stock_review():
        print("修复成功！")
        sys.exit(0)
    else:
        print("修复失败！")
        sys.exit(1) 