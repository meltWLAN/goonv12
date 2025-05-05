#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试热门行业分析功能是否正常工作
"""

import sys
import json
from enhanced_sector_analyzer import EnhancedSectorAnalyzer
from sector_visualization import SectorVisualizationDialog
from PyQt5.QtWidgets import QApplication

def test_hot_sectors():
    """测试热门行业分析"""
    print("开始测试热门行业分析...")
    
    try:
        # 初始化分析器
        analyzer = EnhancedSectorAnalyzer()
        print("分析器已初始化")
        
        # 分析热门行业
        print("正在分析热门行业...")
        result = analyzer.analyze_hot_sectors(top_n=10, force_refresh=True)
        
        # 打印结果状态
        print(f"分析结果状态: {result['status']}")
        
        if result['status'] == 'success':
            # 检查数据结构
            data = result['data']
            print(f"数据键: {list(data.keys())}")
            
            hot_sectors = data.get('hot_sectors', [])
            prediction_data = data.get('prediction_data', [])
            
            print(f"热门行业数量: {len(hot_sectors)}")
            print(f"预测数据项数: {len(prediction_data)}")
            
            # 打印第一个预测数据的详细信息
            if prediction_data:
                print("\n第一个预测数据详情:")
                first_pred = prediction_data[0]
                for key, value in first_pred.items():
                    print(f"  {key}: {value}")
            
            # 打印前3个热门行业
            if hot_sectors:
                print("\n前3个热门行业:")
                for i, sector in enumerate(hot_sectors[:3]):
                    print(f"{i+1}. {sector['name']} - 热度分数: {sector['hot_score']}")
            
            # 打印预测数据
            if prediction_data:
                print("\n预测数据:")
                for i, pred in enumerate(prediction_data[:3]):
                    print(f"{i+1}. {pred['name']} - 技术评分: {pred.get('technical_score', 'N/A')}")
            
            return True
        else:
            print(f"分析失败: {result.get('message', '未知错误')}")
            return False
    
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_visualization():
    """测试可视化功能"""
    print("\n开始测试行业分析可视化...")
    
    try:
        # 初始化分析器
        analyzer = EnhancedSectorAnalyzer()
        print("分析器已初始化")
        
        # 获取分析数据
        print("获取分析数据...")
        result = analyzer.analyze_hot_sectors()
        print(f"分析结果状态: {result['status']}")
        
        if result['status'] == 'success':
            # 检查prediction_data是否存在
            if 'prediction_data' in result['data']:
                print(f"prediction_data存在，包含 {len(result['data']['prediction_data'])} 项")
            else:
                print("警告: prediction_data不存在!")
            
            # 初始化Qt应用
            print("初始化Qt应用...")
            app = QApplication(sys.argv)
            
            # 创建可视化对话框
            print("创建可视化对话框...")
            dialog = SectorVisualizationDialog(viz_data=result)
            
            # 显示对话框
            dialog.show()
            
            print("可视化对话框已创建，请关闭窗口继续测试...")
            
            # 运行事件循环
            return app.exec_()
        else:
            print(f"获取分析数据失败: {result.get('message', '未知错误')}")
            return False
    
    except Exception as e:
        print(f"可视化测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 热门行业分析功能测试 ===\n")
    
    # 测试热门行业分析
    if test_hot_sectors():
        print("\n✅ 热门行业分析测试通过")
    else:
        print("\n❌ 热门行业分析测试失败")
    
    # 测试可视化功能
    print("\n是否要测试可视化功能？(y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        if test_visualization() == 0:  # 0表示正常退出
            print("\n✅ 可视化功能测试通过")
        else:
            print("\n❌ 可视化功能测试失败")
    
    print("\n测试完成。") 