#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sector_analyzer import SectorAnalyzer
import json

def print_dict(data, indent=0):
    """打印字典数据，便于查看层级结构"""
    for key, value in data.items():
        if isinstance(value, dict):
            print(" " * indent + f"{key}:")
            print_dict(value, indent + 4)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            print(" " * indent + f"{key}: [")
            for item in value[:2]:  # 只打印前两个
                print(" " * (indent + 4) + "{")
                print_dict(item, indent + 8)
                print(" " * (indent + 4) + "}")
            if len(value) > 2:
                print(" " * (indent + 4) + f"... ({len(value) - 2} more items)")
            print(" " * indent + "]")
        else:
            print(" " * indent + f"{key}: {value}")

def main():
    """测试行业分析器功能"""
    print("初始化行业分析器...")
    analyzer = SectorAnalyzer(top_n=5)  # 只获取前5个行业，减少输出
    
    print("\n=== 测试获取热门行业 ===")
    result = analyzer.analyze_hot_sectors()
    if result['status'] == 'success':
        print(f"成功获取热门行业数据，共有 {result['data']['total_sectors']} 个行业")
        print(f"北向资金流入: {result['data']['north_flow']:.2f} 亿元")
        print("\n热门行业数据结构:")
        print_dict(result['data'])
        
        # 检查热门行业详细数据
        print("\n热门行业前3名:")
        for i, sector in enumerate(result['data']['hot_sectors'][:3]):
            print(f"{i+1}. {sector['name']} - 热度: {sector['hot_score']:.2f} - 涨跌幅: {sector['change_pct']:.2f}%")
    else:
        print(f"获取热门行业失败: {result['message']}")
    
    print("\n=== 测试行业预测功能 ===")
    predict_result = analyzer.predict_next_hot_sectors()
    if predict_result['status'] == 'success':
        print(f"成功预测行业趋势，预测周期: {predict_result['data']['prediction_period']}")
        print("\n预测结果数据结构:")
        print_dict(predict_result['data'])
        
        # 检查预测详细数据
        print("\n预测行业前3名:")
        for i, sector in enumerate(predict_result['data']['predicted_sectors'][:3]):
            print(f"{i+1}. {sector['name']} - 预测评分: {sector.get('prediction_score', 0):.2f}")
            if 'reason' in sector:
                print(f"   理由: {sector['reason']}")
    else:
        print(f"行业预测失败: {predict_result['message']}")

if __name__ == "__main__":
    main() 