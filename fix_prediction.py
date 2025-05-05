#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复行业走势预测功能并显示预测结果
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 导入行业分析器
try:
    from sector_analyzer import SectorAnalyzer
    print("成功导入行业分析器")
except ImportError as e:
    print(f"导入行业分析器失败: {str(e)}")
    sys.exit(1)

def print_divider(title):
    """打印分隔线"""
    print("\n" + "="*50)
    print(f" {title} ")
    print("="*50)

def main():
    """主函数"""
    print_divider("行业预测修复工具")
    
    # 初始化行业分析器
    print("初始化行业分析器...")
    analyzer = SectorAnalyzer(top_n=10)
    
    # 获取行业热点分析
    print("\n获取当前行业热点...")
    hot_sectors = analyzer.analyze_hot_sectors()
    
    if hot_sectors['status'] == 'success':
        print(f"成功获取热门行业数据，共 {len(hot_sectors['data']['hot_sectors'])} 个行业")
        
        # 显示热门行业
        print_divider("当前热门行业")
        for i, sector in enumerate(hot_sectors['data']['hot_sectors']):
            print(f"{i+1}. {sector['name']} - 热度: {sector['hot_score']:.2f} - 涨跌幅: {sector['change_pct']:.2f}%")
    else:
        print(f"获取热门行业失败: {hot_sectors.get('message', '未知错误')}")
        return
    
    # 尝试执行修复后的预测函数
    print("\n执行修复后的行业预测...")
    try:
        predictions = analyzer.predict_next_hot_sectors()
        
        if predictions['status'] == 'success':
            print(f"预测成功完成，共 {len(predictions['data']['predicted_sectors'])} 个预测结果")
            
            # 显示预测结果
            print_divider("行业预测结果")
            print(f"预测时间: {predictions['data']['prediction_time']}")
            print(f"预测周期: {predictions['data']['prediction_period']}")
            print("")
            
            for i, sector in enumerate(predictions['data']['predicted_sectors']):
                print(f"{i+1}. {sector['name']} - 技术评分: {sector['technical_score']:.2f}")
                print(f"   理由: {sector['reason']}")
                print("")
                
            print("\n预测功能修复成功!")
        else:
            print(f"预测执行失败: {predictions.get('message', '未知错误')}")
    except Exception as e:
        import traceback
        print(f"预测过程发生错误: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 