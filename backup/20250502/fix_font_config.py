#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复matplotlib字体配置和Unicode字符显示问题
"""

import os
import sys
import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import shutil
from pathlib import Path

def fix_matplotlib_chinese_fonts():
    """修复matplotlib中文字体显示问题"""
    print("正在检查和修复matplotlib字体配置...")
    
    # 获取系统中的字体列表
    font_names = [f.name for f in fm.fontManager.ttflist]
    chinese_fonts = [f for f in font_names if any(name in f for name in 
                    ['SimHei', 'Microsoft YaHei', 'SimSun', 'STHeiti', 'PingFang', 'Heiti', 'Hiragino Sans GB'])]
    
    print(f"系统中找到的中文字体: {chinese_fonts}")
    
    # 首选字体列表
    preferred_fonts = [
        'Microsoft YaHei', 
        'SimHei', 
        'SimSun', 
        'STHeiti', 
        'PingFang SC', 
        'Heiti SC', 
        'Hiragino Sans GB', 
        'Arial Unicode MS'
    ]
    
    # 查找可用的中文字体
    available_font = None
    for font in preferred_fonts:
        if font in font_names:
            available_font = font
            print(f"找到可用中文字体: {font}")
            break
    
    if available_font is None:
        print("未找到可用的中文字体，尝试安装默认字体...")
        # 如果没有找到中文字体，尝试使用matplotlib提供的DejaVu字体
        available_font = 'DejaVu Sans'
    
    # 创建自定义matplotlibrc文件
    mpl_config_dir = matplotlib.get_configdir()
    mpl_config_file = os.path.join(mpl_config_dir, 'matplotlibrc')
    
    config_text = f"""
font.family         : sans-serif
font.sans-serif     : {available_font}, DejaVu Sans, Bitstream Vera Sans, Arial, sans-serif
axes.unicode_minus  : False 
"""
    
    try:
        os.makedirs(mpl_config_dir, exist_ok=True)
        with open(mpl_config_file, 'w', encoding='utf-8') as f:
            f.write(config_text)
        print(f"已创建matplotlib配置文件: {mpl_config_file}")
    except Exception as e:
        print(f"创建matplotlib配置文件失败: {str(e)}")
    
    # 清除matplotlib字体缓存
    cache_dir = os.path.join(mpl_config_dir, 'font_cache')
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print("已清除matplotlib字体缓存")
        except Exception as e:
            print(f"清除字体缓存失败: {str(e)}")
    
    # 更新系统字体设置
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = [available_font, 'DejaVu Sans', 'Bitstream Vera Sans', 'Arial', 'sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("已更新当前会话的matplotlib字体配置")
    except Exception as e:
        print(f"更新字体配置失败: {str(e)}")
    
    return available_font

def fix_star_symbol_display():
    """修复Unicode星标符号显示问题"""
    print("正在修复Unicode星标符号(⭐)显示问题...")
    
    # 修改sector_visualization.py中的Unicode星号为替代字符
    sector_viz_file = 'sector_visualization.py'
    if os.path.exists(sector_viz_file):
        try:
            with open(sector_viz_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 将Unicode星号(⭐)替换为ASCII星号(*)
            modified_content = content.replace('⭐', '*')
            # 更新图例文本
            modified_content = modified_content.replace('\'⭐ 表示行业轮动分析预测即将进入景气周期\'', '\'* 表示行业轮动分析预测即将进入景气周期\'')
            
            with open(sector_viz_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"已修复 {sector_viz_file} 中的Unicode星号符号")
        except Exception as e:
            print(f"修复sector_visualization.py失败: {str(e)}")
    else:
        print(f"文件 {sector_viz_file} 不存在，跳过修复")
    
    return True

def test_font_configuration(font_name):
    """测试字体配置是否成功"""
    print("正在测试字体配置...")
    
    try:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
        ax.set_title(f'中文显示测试 - 使用 {font_name} 字体')
        ax.set_xlabel('横轴标签')
        ax.set_ylabel('纵轴标签')
        
        # 保存测试结果
        plt.savefig('font_test_result.png')
        plt.close()
        
        print(f"字体测试完成，结果已保存至 font_test_result.png")
        return True
    except Exception as e:
        print(f"字体测试失败: {str(e)}")
        return False

def main():
    print("开始修复字体配置问题...\n")
    
    # 修复matplotlib中文字体
    available_font = fix_matplotlib_chinese_fonts()
    
    # 修复Unicode星号符号显示问题
    fix_star_symbol_display()
    
    # 测试字体配置
    test_font_configuration(available_font)
    
    print("\n字体配置修复完成！请重新启动应用程序以应用更改。")

if __name__ == "__main__":
    main() 