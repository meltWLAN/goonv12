#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复visual_stock_system.py中的缩进问题
"""

import re

def fix_indentation(file_path):
    """修复文件中的缩进问题"""
    print(f"开始修复 {file_path} 的缩进问题...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    with open(f"{file_path}.indent.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复_create_fallback_indicator方法中的缩进问题
    pattern = r"def _create_fallback_indicator\(self, df, indicator, close_column\):\n\s+\"\"\"为缺失的指标创建替代列\"\"\"\n\s+if indicator == 'EMA21':"
    replacement = "def _create_fallback_indicator(self, df, indicator, close_column):\n        \"\"\"为缺失的指标创建替代列\"\"\"\n        if indicator == 'EMA21':"
    content = re.sub(pattern, replacement, content)
    
    # 修复if语句的缩进
    content = content.replace("                    if indicator == 'EMA21':", "        if indicator == 'EMA21':")
    content = content.replace("            df['EMA21'] = df[close_column]", "            df['EMA21'] = df[close_column]")
    content = content.replace("                    elif indicator == 'MACD':", "        elif indicator == 'MACD':")
    content = content.replace("            df['MACD'] = 0.0", "            df['MACD'] = 0.0")
    content = content.replace("                    elif indicator == 'MACD_Signal':", "        elif indicator == 'MACD_Signal':")
    content = content.replace("                            df['MACD_Signal'] = 0.0", "            df['MACD_Signal'] = 0.0")
    content = content.replace("                    elif indicator == 'MACD_Hist':", "        elif indicator == 'MACD_Hist':")
    content = content.replace("                            df['MACD_Hist'] = 0.0", "            df['MACD_Hist'] = 0.0")
    
    # 修复_create_all_fallback_indicators方法中的缩进问题
    content = content.replace("                            df['MACD_Signal'] = 0.0", "        df['MACD_Signal'] = 0.0")
    content = content.replace("                            df['MACD_Hist'] = 0.0", "        df['MACD_Hist'] = 0.0")
    
    # 修复analyze_volume_price方法中的try-except缩进问题
    pattern = r"try:\n        # 确保日期索引"
    replacement = "        try:\n            # 确保日期索引"
    content = re.sub(pattern, replacement, content)
    
    # 将修复后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"文件 {file_path} 的缩进问题已修复")

if __name__ == "__main__":
    # 修复visual_stock_system.py文件
    fix_indentation('visual_stock_system.py')
    print("修复完成!") 