#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接修复stock_analyzer_app.py中的换行符问题
"""

import re

def fix_newlines(file_path):
    """修复文件中的换行符问题"""
    print(f"开始修复 {file_path} 中的换行符问题...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份文件
    with open(f"{file_path}.newline.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复所有的"self.result_text.append("\n" 模式 (换行符直接放在字符串开头)
    patterns = [
        r'self\.result_text\.append\("\n',  # 匹配格式1
        r'self\.result_text\.append\(f"\n'  # 匹配格式2
    ]
    
    for pattern in patterns:
        # 使用正则表达式查找所有匹配项
        matches = re.findall(pattern, content)
        print(f"找到 {len(matches)} 个模式 '{pattern}' 匹配项")
        
        # 替换为正确的格式
        if pattern == r'self\.result_text\.append\("\n':
            content = content.replace('self.result_text.append("\n', 'self.result_text.append("\\n')
        elif pattern == r'self\.result_text\.append\(f"\n':
            content = content.replace('self.result_text.append(f"\n', 'self.result_text.append(f"\\n')
    
    # 将修复后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"完成 {file_path} 中的换行符问题修复")

if __name__ == "__main__":
    # 修复stock_analyzer_app.py文件
    fix_newlines("stock_analyzer_app.py")
    print("修复完成!") 