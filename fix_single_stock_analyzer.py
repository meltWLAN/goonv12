#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复single_stock_analyzer.py中的导入问题
"""

import os
import sys

def fix_import():
    """修复导入问题"""
    print("开始修复single_stock_analyzer.py中的导入问题...")
    
    # 读取文件内容
    with open("single_stock_analyzer.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改导入语句
    modified_content = content.replace(
        "from visual_stock_system import VisualStockSystem",
        "from minimal_visual_stock_system import VisualStockSystem"
    )
    
    # 备份原文件
    with open("single_stock_analyzer.py.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 保存修改后的文件
    with open("single_stock_analyzer.py", 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("已修复single_stock_analyzer.py中的导入问题")
    return True

if __name__ == "__main__":
    if fix_import():
        print("修复完成!")
    else:
        print("修复失败!") 