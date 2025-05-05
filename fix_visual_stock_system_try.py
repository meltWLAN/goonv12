#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面修复visual_stock_system.py中的try-except语句结构问题
"""

import re

def fix_try_except_structure(file_path):
    """修复文件中的try-except语句结构问题"""
    print(f"开始全面修复 {file_path} 的try-except语句结构问题...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 备份原文件
    with open(f"{file_path}.tryfix.bak", 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # 定位并修复第365行左右的try-except结构问题
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 修复第一个问题区域 - 动量分析函数中的问题
        if 'if macd is not None and signal is not None and hist is not None:' in line:
            # 保存当前行
            fixed_lines.append(line)
            i += 1
            
            # 找到下一行 df['MACD'] = macd
            while i < len(lines) and 'df[\'MACD\'] = macd' not in lines[i]:
                fixed_lines.append(lines[i])
                i += 1
            
            # 这是问题行，需要添加额外的缩进
            if i < len(lines):
                line = lines[i]
                # 增加缩进
                fixed_lines.append((' ' * 8) + line.lstrip())
                i += 1
                
                # 对接下来的两行也增加缩进
                for _ in range(2):
                    if i < len(lines):
                        line = lines[i]
                        fixed_lines.append((' ' * 8) + line.lstrip())
                        i += 1
            
            # 添加缺失的 try 对应的 except 块的结束
            fixed_lines.append('                except Exception as e:\n')
            fixed_lines.append('                    print(f"使用talib计算指标失败: {str(e)}，使用替代方法")\n')
            fixed_lines.append('                    self._calculate_simplified_indicators(df, close_column)\n')
        
        # 修复第二个问题区域 - analyze_volume_price 函数中的问题
        elif '# 检查Volume列是否有有效值' in line and '                try:' in lines[i+10:i+20]:
            # 保存当前区域直到try语句
            while i < len(lines) and 'try:' not in lines[i]:
                fixed_lines.append(lines[i])
                i += 1
            
            # 修复try语句的缩进
            if i < len(lines) and 'try:' in lines[i]:
                # 替换为正确缩进
                fixed_lines.append('        try:\n')
                i += 1
                
                # 之后的行需要正确缩进
                while i < len(lines) and '# 确保日期索引' in lines[i]:
                    line = lines[i]
                    # 增加缩进
                    fixed_lines.append('            ' + line.lstrip())
                    i += 1
        
        # 修复第三个问题区域 - _create_all_fallback_indicators 函数中的问题
        elif 'def _create_all_fallback_indicators' in line:
            fixed_lines.append(line)
            i += 1
            
            # 添加函数体
            fixed_lines.append('        """创建所有必要的替代指标"""\n')
            fixed_lines.append('        df[\'EMA21\'] = df[close_column]\n')
            fixed_lines.append('        df[\'MACD\'] = 0.0\n')
            fixed_lines.append('        df[\'MACD_Signal\'] = 0.0\n')
            fixed_lines.append('        df[\'MACD_Hist\'] = 0.0\n')
            
            # 跳过原来错误缩进的内容
            while i < len(lines) and 'def analyze_volume_price' not in lines[i]:
                i += 1
        
        # 修复第四个问题区域 - _create_fallback_indicator 函数中的问题
        elif 'def _create_fallback_indicator' in line:
            fixed_lines.append(line)
            i += 1
            
            # 添加函数体
            fixed_lines.append('        """为缺失的指标创建替代列"""\n')
            fixed_lines.append('        if indicator == \'EMA21\':\n')
            fixed_lines.append('            df[\'EMA21\'] = df[close_column]\n')
            fixed_lines.append('        elif indicator == \'MACD\':\n')
            fixed_lines.append('            df[\'MACD\'] = 0.0\n')
            fixed_lines.append('        elif indicator == \'MACD_Signal\':\n')
            fixed_lines.append('            df[\'MACD_Signal\'] = 0.0\n')
            fixed_lines.append('        elif indicator == \'MACD_Hist\':\n')
            fixed_lines.append('            df[\'MACD_Hist\'] = 0.0\n')
            
            # 跳过原来错误缩进的内容
            while i < len(lines) and 'def _create_all_fallback_indicators' not in lines[i]:
                i += 1
        
        else:
            fixed_lines.append(line)
            i += 1
    
    # 将修复后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"文件 {file_path} 的try-except语句结构问题已修复")

if __name__ == "__main__":
    # 修复visual_stock_system.py文件
    fix_try_except_structure('visual_stock_system.py')
    print("修复完成!") 