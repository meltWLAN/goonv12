#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证热门行业分析和可视化功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from enhanced_sector_analyzer import EnhancedSectorAnalyzer
from sector_visualization import SectorVisualizationDialog

def main():
    """主函数"""
    print("开始验证热门行业分析与可视化功能...")
    
    # 初始化QApplication
    app = QApplication(sys.argv)
    
    # 分析热门行业
    analyzer = EnhancedSectorAnalyzer()
    print("正在执行行业分析...")
    result = analyzer.analyze_hot_sectors(top_n=10, force_refresh=True)
    
    if result['status'] == 'success':
        print(f"行业分析成功! 找到 {len(result['data']['hot_sectors'])} 个热门行业")
        print(f"预测数据中包含 {len(result['data']['prediction_data'])} 项预测")
        
        # 创建可视化对话框
        dialog = SectorVisualizationDialog(viz_data=result)
        dialog.setWindowTitle("热门行业分析可视化 (验证)")
        dialog.show()
        
        print("\n可视化对话框已创建，请检查：")
        print("1. 预测结果标签页是否正常显示")
        print("2. 热度分布图表是否正常显示")
        print("3. 行业轮动图表是否正常显示")
        print("\n关闭对话框后程序将退出")
        
        return app.exec_()
    else:
        print(f"行业分析失败: {result.get('message', '未知错误')}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 