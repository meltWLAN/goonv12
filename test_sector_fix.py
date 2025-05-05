#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试热门行业分析模块的修复
特别关注market_info错误是否已解决
"""

import sys
import json
import inspect
from sector_analyzer import SectorAnalyzer
from PyQt5.QtWidgets import QApplication
import traceback

def test_hot_sectors_basic():
    """测试热门行业分析基本功能"""
    print("=== 测试热门行业基本分析功能 ===")
    
    try:
        # 初始化分析器
        analyzer = SectorAnalyzer()
        print("✅ 分析器初始化成功")
        
        # 获取行业列表
        sectors = analyzer.get_sector_list()
        if isinstance(sectors, list) and len(sectors) > 0:
            print(f"✅ 获取行业列表成功，共{len(sectors)}个行业")
        else:
            print("❌ 获取行业列表失败")
            return False
        
        # 分析热门行业
        result = analyzer.analyze_hot_sectors()
        
        if result['status'] == 'success':
            hot_sectors = result['data']['hot_sectors']
            print(f"✅ 分析热门行业成功，返回{len(hot_sectors)}个热门行业")
            
            # 打印前3个热门行业
            print("\n前3个热门行业:")
            for i, sector in enumerate(hot_sectors[:3]):
                print(f"{i+1}. {sector['name']} - 热度: {sector['hot_score']:.2f} - 涨跌幅: {sector['change_pct']:.2f}%")
                
            return True
        else:
            print(f"❌ 分析热门行业失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        traceback.print_exc()
        return False

def test_market_info_error_fix():
    """测试market_info错误修复"""
    print("\n=== 测试market_info错误修复 ===")
    
    try:
        # 导入股票分析应用
        sys.path.append('.')
        from stock_analyzer_app import StockAnalyzerApp
        
        # 创建QApplication实例（不显示UI）
        app = QApplication(sys.argv)
        
        # 实例化分析应用
        analyzer_app = StockAnalyzerApp()
        
        # 使用重写的analyze_hot_industries方法调用
        print("调用analyze_hot_industries方法...")
        
        # 尝试模拟热门行业分析按钮点击
        try:
            analyzer_app.analyze_hot_industries()
            print("✅ 热门行业分析方法调用成功，没有引发market_info错误")
            return True
        except KeyError as e:
            if 'market_info' in str(e):
                print(f"❌ 依然存在market_info错误: {e}")
                return False
            else:
                print(f"⚠️ 存在其他KeyError错误: {e}")
                return False
        except Exception as e:
            print(f"⚠️ 存在其他类型错误: {e}")
            print(traceback.format_exc())
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        traceback.print_exc()
        return False

def test_tushare_fallback():
    """测试Tushare回退到AKShare的机制"""
    print("\n=== 测试Tushare和AKShare回退机制 ===")
    
    try:
        analyzer = SectorAnalyzer()
        
        # 检查回退机制的实现，而不是实际的数据获取结果
        code_path = inspect.getsource(analyzer._get_sector_history)
        
        if "tushare_available" in code_path and "ak." in code_path:
            print("✅ 确认_get_sector_history方法同时包含Tushare和AKShare获取逻辑")
            
            # 检查更多细节
            if "if hist_data is None:" in code_path and "if self.tushare_available" in code_path:
                print("✅ 确认存在清晰的数据源回退流程")
                
                # 测试内存缓存机制
                if hasattr(analyzer, '_cache') and isinstance(analyzer._cache, dict):
                    print("✅ 确认内存缓存机制已实现")
                    
                    # 检查磁盘缓存机制
                    if hasattr(analyzer, 'cache_file') and hasattr(analyzer, '_save_cache_to_disk'):
                        print("✅ 确认磁盘缓存机制已实现")
                        return True
                    else:
                        print("❌ 磁盘缓存机制未正确实现")
                        return False
                else:
                    print("❌ 内存缓存机制未正确实现")
                    return False
            else:
                print("❌ 数据源回退流程不完整或不正确")
                return False
        else:
            print("❌ _get_sector_history方法未同时包含Tushare和AKShare获取逻辑")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("====== 热门行业分析修复验证 ======\n")
    
    # 测试基本功能
    basic_test = test_hot_sectors_basic()
    
    # 测试market_info错误修复
    market_info_test = test_market_info_error_fix()
    
    # 测试数据源回退机制
    fallback_test = test_tushare_fallback()
    
    # 输出总结
    print("\n====== 测试结果总结 ======")
    print(f"基本功能测试: {'通过 ✅' if basic_test else '失败 ❌'}")
    print(f"market_info错误修复测试: {'通过 ✅' if market_info_test else '失败 ❌'}")
    print(f"数据源回退机制测试: {'通过 ✅' if fallback_test else '失败 ❌'}")
    
    if basic_test and market_info_test and fallback_test:
        print("\n🎉 所有测试通过，热门行业分析模块修复成功！")
    else:
        print("\n⚠️ 部分测试失败，可能仍需进一步修复。") 