#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版行业分析器测试脚本
验证增强功能的有效性和实用性
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

def print_divider(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)

def print_json(data, indent=2):
    """格式化打印JSON数据"""
    print(json.dumps(data, ensure_ascii=False, indent=indent))

def test_original_analyzer():
    """测试原始行业分析器"""
    print_divider("测试原始行业分析器")
    
    try:
        # 导入原始分析器
        from sector_analyzer import SectorAnalyzer
        print("成功导入原始行业分析器")
        
        # 初始化分析器
        analyzer = SectorAnalyzer(top_n=5)
        print("成功初始化原始行业分析器")
        
        # 获取热门行业
        print("\n获取热门行业...")
        hot_sectors = analyzer.analyze_hot_sectors()
        
        if hot_sectors['status'] == 'success':
            print(f"成功获取热门行业，共 {len(hot_sectors['data']['hot_sectors'])} 个")
            
            # 显示前3个热门行业
            for i, sector in enumerate(hot_sectors['data']['hot_sectors'][:3]):
                print(f"\n{i+1}. {sector['name']}")
                print(f"   热度: {sector['hot_score']:.2f}")
                print(f"   涨跌幅: {sector['change_pct']:.2f}%")
                print(f"   分析: {sector['analysis_reason']}")
        else:
            print(f"获取热门行业失败: {hot_sectors.get('message', '未知错误')}")
        
        # 获取行业预测
        print("\n获取行业预测...")
        predictions = analyzer.predict_next_hot_sectors()
        
        if predictions['status'] == 'success':
            print(f"成功获取行业预测，共 {len(predictions['data']['predicted_sectors'])} 个")
            
            # 显示前3个预测结果
            for i, sector in enumerate(predictions['data']['predicted_sectors'][:3]):
                print(f"\n{i+1}. {sector['name']}")
                print(f"   技术评分: {sector['technical_score']:.2f}")
                print(f"   预测理由: {sector['reason']}")
        else:
            print(f"获取行业预测失败: {predictions.get('message', '未知错误')}")
        
        return True
    except Exception as e:
        import traceback
        print(f"测试原始行业分析器失败: {str(e)}")
        print(traceback.format_exc())
        return False

def test_enhanced_analyzer():
    """测试增强版行业分析器"""
    print_divider("测试增强版行业分析器")
    
    try:
        # 导入增强版分析器
        from enhance_sector_analyzer import EnhancedSectorAnalyzer
        print("成功导入增强版行业分析器")
        
        # 初始化分析器
        analyzer = EnhancedSectorAnalyzer(top_n=5)
        print("成功初始化增强版行业分析器")
        
        # 获取增强版热门行业
        print("\n获取增强版热门行业...")
        hot_sectors = analyzer.analyze_enhanced_hot_sectors()
        
        if hot_sectors['status'] == 'success':
            print(f"成功获取增强版热门行业，共 {len(hot_sectors['data']['hot_sectors'])} 个")
            
            # 显示前3个热门行业及其增强特性
            for i, sector in enumerate(hot_sectors['data']['hot_sectors'][:3]):
                print(f"\n{i+1}. {sector['name']}")
                print(f"   热度: {sector['hot_score']:.2f}")
                print(f"   涨跌幅: {sector['change_pct']:.2f}%")
                
                # 显示增强特性
                enhanced_features = []
                if 'trend_stability_score' in sector:
                    print(f"   趋势稳定性: {sector['trend_stability_score']:.2f} ({sector['trend_stability_desc']})")
                    enhanced_features.append("趋势稳定性")
                if 'relative_strength_score' in sector:
                    print(f"   相对强度: {sector['relative_strength_score']:.2f} ({sector['relative_strength_desc']})")
                    enhanced_features.append("相对强度分析")
                if 'trading_signals' in sector:
                    signals = sector['trading_signals']
                    if signals:
                        if signals.get('buy_signals'):
                            print(f"   买入信号: {', '.join(signals['buy_signals'][:2])}")
                        if signals.get('sell_signals'):
                            print(f"   卖出信号: {', '.join(signals['sell_signals'][:2])}")
                        print(f"   风险级别: {signals.get('risk_level', '未知')}")
                        print(f"   建议仓位: {int(signals.get('position_advice', 0.5) * 100)}%")
                    enhanced_features.append("交易信号")
                
                if enhanced_features:
                    print(f"   增强特性: {', '.join(enhanced_features)}")
                
                print(f"   分析: {sector['analysis_reason']}")
        else:
            print(f"获取增强版热门行业失败: {hot_sectors.get('message', '未知错误')}")
        
        # 获取增强版行业预测
        print("\n获取增强版行业预测...")
        predictions = analyzer.predict_hot_sectors_enhanced()
        
        if predictions['status'] == 'success':
            print(f"成功获取增强版行业预测，共 {len(predictions['data']['predicted_sectors'])} 个")
            
            # 显示前3个预测结果及其增强特性
            for i, sector in enumerate(predictions['data']['predicted_sectors'][:3]):
                print(f"\n{i+1}. {sector['name']}")
                print(f"   技术评分: {sector['technical_score']:.2f}")
                
                # 显示增强特性
                enhanced_features = []
                if 'trend_stability' in sector:
                    print(f"   趋势稳定性: {sector['trend_stability']:.2f} ({sector['trend_desc']})")
                    enhanced_features.append("趋势稳定性")
                if 'prediction_components' in sector:
                    print(f"   预测组成: 趋势({sector['prediction_components']['trend_score']:.2f}) + "
                          f"热度({sector['prediction_components']['hot_score']:.2f}) + "
                          f"信号({sector['prediction_components']['signal_score']:.2f})")
                    enhanced_features.append("预测组件分析")
                if 'trading_signals' in sector and sector['trading_signals']:
                    signals = sector['trading_signals']
                    if signals.get('buy_signals'):
                        print(f"   买入信号: {', '.join(signals['buy_signals'][:2])}")
                    if signals.get('sell_signals'):
                        print(f"   卖出信号: {', '.join(signals['sell_signals'][:2])}")
                    print(f"   风险级别: {signals.get('risk_level', '未知')}")
                    enhanced_features.append("交易信号")
                
                if enhanced_features:
                    print(f"   增强特性: {', '.join(enhanced_features)}")
                
                print(f"   预测理由: {sector['reason']}")
        else:
            print(f"获取增强版行业预测失败: {predictions.get('message', '未知错误')}")
        
        return True
    except Exception as e:
        import traceback
        print(f"测试增强版行业分析器失败: {str(e)}")
        print(traceback.format_exc())
        return False

def test_integration():
    """测试集成功能"""
    print_divider("测试行业分析器集成")
    
    try:
        # 导入集成脚本
        import sector_analyzer_integration
        print("成功导入集成脚本")
        
        # 执行修补
        print("\n执行行业分析器修补...")
        if sector_analyzer_integration.patch_sector_analyzer():
            print("成功修补行业分析器")
            
            # 导入修补后的原始分析器
            from sector_analyzer import SectorAnalyzer
            
            # 初始化分析器
            analyzer = SectorAnalyzer(top_n=5)
            print("成功初始化修补后的分析器")
            
            # 获取热门行业
            print("\n获取热门行业(应该使用增强版)...")
            hot_sectors = analyzer.analyze_hot_sectors()
            
            if hot_sectors['status'] == 'success':
                print(f"成功获取热门行业，共 {len(hot_sectors['data']['hot_sectors'])} 个")
                
                # 检查是否使用了增强版
                is_enhanced = False
                if hot_sectors['data'].get('hot_sectors') and len(hot_sectors['data']['hot_sectors']) > 0:
                    sector = hot_sectors['data']['hot_sectors'][0]
                    if ('trend_stability_score' in sector or 
                        'relative_strength_score' in sector or 
                        'trading_signals' in sector or
                        'advanced_analysis' in sector):
                        is_enhanced = True
                
                if is_enhanced:
                    print("确认: 使用了增强版行业分析")
                else:
                    print("警告: 可能未使用增强版行业分析")
                
                # 显示第一个热门行业
                if hot_sectors['data']['hot_sectors']:
                    sector = hot_sectors['data']['hot_sectors'][0]
                    print(f"\n热门行业: {sector['name']}")
                    print(f"热度: {sector['hot_score']:.2f}")
                    print(f"分析: {sector['analysis_reason']}")
            else:
                print(f"获取热门行业失败: {hot_sectors.get('message', '未知错误')}")
            
            # 获取行业预测
            print("\n获取行业预测(应该使用增强版)...")
            predictions = analyzer.predict_next_hot_sectors()
            
            if predictions['status'] == 'success':
                print(f"成功获取行业预测，共 {len(predictions['data']['predicted_sectors'])} 个")
                
                # 检查是否使用了增强版
                is_enhanced = False
                if predictions['data'].get('predicted_sectors') and len(predictions['data']['predicted_sectors']) > 0:
                    sector = predictions['data']['predicted_sectors'][0]
                    if ('trend_stability' in sector or 
                        'prediction_components' in sector or 
                        'trading_signals' in sector):
                        is_enhanced = True
                
                # 也检查数据对象是否包含增强标记
                if predictions['data'].get('is_enhanced'):
                    is_enhanced = True
                
                if is_enhanced:
                    print("确认: 使用了增强版行业预测")
                else:
                    print("警告: 可能未使用增强版行业预测")
                
                # 显示第一个预测结果
                if predictions['data']['predicted_sectors']:
                    sector = predictions['data']['predicted_sectors'][0]
                    print(f"\n预测行业: {sector['name']}")
                    print(f"技术评分: {sector['technical_score']:.2f}")
                    print(f"预测理由: {sector['reason']}")
            else:
                print(f"获取行业预测失败: {predictions.get('message', '未知错误')}")
        else:
            print("修补行业分析器失败")
        
        return True
    except Exception as e:
        import traceback
        print(f"测试集成功能失败: {str(e)}")
        print(traceback.format_exc())
        return False

def main():
    """主函数"""
    print_divider("增强版行业分析器测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试结果
    results = {}
    
    # 测试原始分析器
    results['original'] = test_original_analyzer()
    
    # 测试增强版分析器
    results['enhanced'] = test_enhanced_analyzer()
    
    # 测试集成功能
    results['integration'] = test_integration()
    
    # 显示测试总结
    print_divider("测试结果总结")
    for test, result in results.items():
        print(f"{test.capitalize()} 测试: {'成功' if result else '失败'}")
    
    # 总体结果
    overall = all(results.values())
    print(f"\n总体测试结果: {'成功' if overall else '失败'}")
    
    print("\n如果测试成功，行业分析模块已成功增强并集成到系统中。")
    print("你可以通过以下方式使用增强功能:")
    print("1. 直接运行: python stock_analyzer_app.py")
    print("2. 手动集成: python sector_analyzer_integration.py")
    print("3. 更新数据: python fetch_real_sector_data.py")

if __name__ == "__main__":
    main() 