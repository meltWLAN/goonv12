#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版行业分析验证脚本
检查数据完整性和功能正常性
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VerifyEnhancedSectors")

def print_divider(title):
    """打印分隔线"""
    width = max(60, len(title) + 10)
    print("\n" + "="*width)
    print(f" {title} ".center(width))
    print("="*width)

def verify_data_completeness():
    """验证数据的完整性"""
    print_divider("验证数据完整性")
    
    try:
        # 导入必要模块
        from sector_integration import SectorIntegrator
        
        # 初始化集成器
        integrator = SectorIntegrator()
        
        # 获取行业列表
        sectors = integrator.get_sector_list()
        
        if not sectors or len(sectors) == 0:
            print("❌ 行业列表获取失败")
            return False
        
        print(f"✅ 成功获取行业列表，共 {len(sectors)} 个行业")
        
        # 检查一些关键行业是否存在
        key_sectors = ["计算机", "银行", "医药生物", "电子", "食品饮料"]
        missing_sectors = [s for s in key_sectors if s not in sectors]
        
        if missing_sectors:
            print(f"⚠️ 缺少以下关键行业: {', '.join(missing_sectors)}")
        else:
            print("✅ 所有关键行业都存在")
        
        # 抽样检查几个行业的历史数据
        sample_sectors = sectors[:5]  # 取前5个行业
        data_stats = []
        
        for sector in sample_sectors:
            # 获取行业历史数据
            history = integrator._get_sector_history(sector)
            
            if history is None or history.empty:
                data_stats.append({
                    "name": sector,
                    "status": "失败",
                    "records": 0,
                    "real_data": False
                })
                continue
            
            # 检查数据字段
            required_fields = ["收盘", "开盘", "最高", "最低", "成交量"]
            missing_fields = [f for f in required_fields if f not in history.columns]
            
            is_real = integrator._is_real_data(sector)
            
            data_stats.append({
                "name": sector,
                "status": "成功" if not missing_fields else f"缺少字段: {', '.join(missing_fields)}",
                "records": len(history),
                "date_range": f"{history.index.min()} 至 {history.index.max()}" if not history.empty else "无数据",
                "real_data": is_real
            })
        
        # 打印数据统计
        print("\n行业数据抽样检查:")
        for stat in data_stats:
            print(f"  {stat['name']}:")
            print(f"    状态: {stat['status']}")
            print(f"    记录数: {stat['records']}")
            if "date_range" in stat:
                print(f"    日期范围: {stat['date_range']}")
            print(f"    真实数据: {'是' if stat['real_data'] else '否'}")
        
        # 检查缓存目录
        cache_dir = "data_cache"
        if os.path.exists(cache_dir) and os.path.isdir(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith(".pkl") or f.endswith(".json")]
            print(f"\n✅ 缓存目录存在，包含 {len(cache_files)} 个缓存文件")
        else:
            print("\n❌ 缓存目录不存在或不是目录")
        
        # 整体评估
        success_count = sum(1 for stat in data_stats if stat["status"] == "成功")
        real_data_count = sum(1 for stat in data_stats if stat["real_data"])
        
        if success_count == len(data_stats):
            print("\n✅ 数据完整性检查通过")
            print(f"  - {real_data_count}/{len(data_stats)} 个抽样行业使用真实数据")
            return True
        else:
            print(f"\n⚠️ 数据完整性检查不完全通过 ({success_count}/{len(data_stats)})")
            return False
    
    except Exception as e:
        import traceback
        print(f"\n❌ 数据完整性验证失败: {str(e)}")
        print(traceback.format_exc())
        return False

def verify_enhanced_features():
    """验证增强特性是否正常工作"""
    print_divider("验证增强特性")
    
    try:
        # 导入增强版分析器
        from enhance_sector_analyzer import EnhancedSectorAnalyzer
        
        # 初始化分析器
        analyzer = EnhancedSectorAnalyzer(top_n=5)
        
        # 验证功能特性列表
        features = [
            "动量指标计算",
            "趋势稳定性分析",
            "相对强度比较",
            "交易信号生成",
            "入场/出场区间",
            "风险评估",
            "多维度预测"
        ]
        
        # 获取热门行业
        hot_sectors = analyzer.analyze_enhanced_hot_sectors()
        
        if hot_sectors['status'] != 'success':
            print(f"❌ 获取增强版热门行业失败: {hot_sectors.get('message', '未知错误')}")
            return False
        
        print(f"✅ 成功获取增强版热门行业，共 {len(hot_sectors['data']['hot_sectors'])} 个")
        
        # 获取第一个行业详细信息
        if hot_sectors['data']['hot_sectors']:
            sector = hot_sectors['data']['hot_sectors'][0]
            print(f"\n行业 '{sector['name']}' 的增强特性:")
            
            feature_status = {}
            
            # 检查动量指标
            if 'rsi' in sector or 'macd' in sector:
                feature_status["动量指标计算"] = "✅ 存在"
                print(f"  - RSI: {sector.get('rsi', '未计算')}")
                print(f"  - MACD: {sector.get('macd', '未计算')}")
            else:
                feature_status["动量指标计算"] = "❌ 缺失"
            
            # 检查趋势稳定性
            if 'trend_stability_score' in sector and 'trend_stability_desc' in sector:
                feature_status["趋势稳定性分析"] = "✅ 存在"
                print(f"  - 趋势稳定性得分: {sector['trend_stability_score']}")
                print(f"  - 趋势描述: {sector['trend_stability_desc']}")
            else:
                feature_status["趋势稳定性分析"] = "❌ 缺失"
            
            # 检查相对强度
            if 'relative_strength_score' in sector and 'relative_strength_desc' in sector:
                feature_status["相对强度比较"] = "✅ 存在"
                print(f"  - 相对强度得分: {sector['relative_strength_score']}")
                print(f"  - 相对强度描述: {sector['relative_strength_desc']}")
            else:
                feature_status["相对强度比较"] = "❌ 缺失"
            
            # 检查交易信号
            if 'trading_signals' in sector:
                signals = sector['trading_signals']
                if signals:
                    feature_status["交易信号生成"] = "✅ 存在"
                    if 'buy_signals' in signals and signals['buy_signals']:
                        print(f"  - 买入信号: {', '.join(signals['buy_signals'][:2])}")
                    if 'sell_signals' in signals and signals['sell_signals']:
                        print(f"  - 卖出信号: {', '.join(signals['sell_signals'][:2])}")
                    
                    # 检查入场/出场区间
                    if 'entry_zones' in signals and 'exit_zones' in signals:
                        feature_status["入场/出场区间"] = "✅ 存在"
                        if signals['entry_zones']:
                            entry = signals['entry_zones'][0]
                            print(f"  - 入场区间: {entry['price']} ({entry['desc']})")
                        if signals['exit_zones']:
                            exit = signals['exit_zones'][0]
                            print(f"  - 出场区间: {exit['price']} ({exit['desc']})")
                    else:
                        feature_status["入场/出场区间"] = "❌ 缺失"
                    
                    # 检查风险评估
                    if 'risk_level' in signals and 'position_advice' in signals:
                        feature_status["风险评估"] = "✅ 存在"
                        print(f"  - 风险级别: {signals['risk_level']}")
                        print(f"  - 仓位建议: {int(signals['position_advice'] * 100)}%")
                    else:
                        feature_status["风险评估"] = "❌ 缺失"
                else:
                    feature_status["交易信号生成"] = "❌ 缺失"
                    feature_status["入场/出场区间"] = "❌ 缺失"
                    feature_status["风险评估"] = "❌ 缺失"
            else:
                feature_status["交易信号生成"] = "❌ 缺失"
                feature_status["入场/出场区间"] = "❌ 缺失"
                feature_status["风险评估"] = "❌ 缺失"
        
        # 获取行业预测
        predictions = analyzer.predict_hot_sectors_enhanced()
        
        if predictions['status'] != 'success':
            print(f"\n❌ 获取增强版行业预测失败: {predictions.get('message', '未知错误')}")
            feature_status["多维度预测"] = "❌ 缺失"
        else:
            print(f"\n✅ 成功获取增强版行业预测，共 {len(predictions['data']['predicted_sectors'])} 个")
            
            # 检查多维度预测
            if predictions['data']['predicted_sectors'] and 'prediction_components' in predictions['data']['predicted_sectors'][0]:
                feature_status["多维度预测"] = "✅ 存在"
                pred = predictions['data']['predicted_sectors'][0]
                components = pred['prediction_components']
                print(f"  - 行业: {pred['name']}")
                print(f"  - 技术评分: {pred['technical_score']}")
                print(f"  - 预测组成: 趋势({components['trend_score']:.2f}) + "
                      f"热度({components['hot_score']:.2f}) + "
                      f"信号({components['signal_score']:.2f})")
                print(f"  - 预测理由: {pred['reason']}")
            else:
                feature_status["多维度预测"] = "❌ 缺失"
        
        # 打印特性总结
        print("\n增强特性验证总结:")
        for feature in features:
            status = feature_status.get(feature, "❓ 未知")
            print(f"  - {feature}: {status}")
        
        # 特性实现率
        implemented_count = sum(1 for status in feature_status.values() if "✅" in status)
        implementation_rate = implemented_count / len(features) * 100
        
        print(f"\n特性实现率: {implementation_rate:.1f}% ({implemented_count}/{len(features)})")
        
        if implementation_rate >= 80:
            print("✅ 增强特性验证通过")
            return True
        elif implementation_rate >= 50:
            print("⚠️ 增强特性部分通过")
            return False
        else:
            print("❌ 增强特性验证失败")
            return False
    
    except Exception as e:
        import traceback
        print(f"\n❌ 增强特性验证失败: {str(e)}")
        print(traceback.format_exc())
        return False

def verify_integration():
    """验证集成是否正常工作"""
    print_divider("验证集成功能")
    
    try:
        # 导入原始分析器
        from sector_analyzer import SectorAnalyzer
        
        # 初始化分析器
        analyzer = SectorAnalyzer(top_n=3)
        
        # 检查是否已集成增强功能
        is_enhanced = hasattr(analyzer.__class__, 'is_enhanced') and analyzer.__class__.is_enhanced
        
        if is_enhanced:
            print(f"✅ 行业分析器已集成增强功能（集成时间: {analyzer.__class__.enhancement_time}）")
        else:
            print("❌ 行业分析器未集成增强功能")
            print("\n正在尝试集成...")
            
            # 尝试进行集成
            import sector_analyzer_integration
            if sector_analyzer_integration.patch_sector_analyzer():
                print("✅ 集成成功")
                is_enhanced = True
            else:
                print("❌ 集成失败")
                return False
        
        # 使用原始接口获取热门行业
        hot_sectors = analyzer.analyze_hot_sectors()
        
        if hot_sectors['status'] != 'success':
            print(f"❌ 获取热门行业失败: {hot_sectors.get('message', '未知错误')}")
            return False
        
        print(f"✅ 成功获取热门行业，共 {len(hot_sectors['data']['hot_sectors'])} 个")
        
        # 检查是否真的使用了增强版
        is_using_enhanced = False
        if hot_sectors['data']['hot_sectors']:
            sector = hot_sectors['data']['hot_sectors'][0]
            is_using_enhanced = ('trend_stability_score' in sector or 
                                'relative_strength_score' in sector or 
                                'trading_signals' in sector or
                                'advanced_analysis' in sector)
        
        # 也检查数据中是否有增强标记
        if hot_sectors.get('is_enhanced', False):
            is_using_enhanced = True
        
        if is_using_enhanced:
            print("✅ 确认使用了增强版行业分析")
        else:
            print("❌ 未使用增强版行业分析")
            return False
        
        # 使用原始接口获取行业预测
        predictions = analyzer.predict_next_hot_sectors()
        
        if predictions['status'] != 'success':
            print(f"❌ 获取行业预测失败: {predictions.get('message', '未知错误')}")
            return False
        
        print(f"✅ 成功获取行业预测，共 {len(predictions['data']['predicted_sectors'])} 个")
        
        # 检查是否真的使用了增强版预测
        is_enhanced_pred = False
        if predictions['data']['predicted_sectors']:
            pred = predictions['data']['predicted_sectors'][0]
            is_enhanced_pred = ('trend_stability' in pred or 
                                'prediction_components' in pred or 
                                'trading_signals' in pred)
        
        # 也检查数据对象是否包含增强标记
        if predictions['data'].get('is_enhanced', False):
            is_enhanced_pred = True
        
        if is_enhanced_pred:
            print("✅ 确认使用了增强版行业预测")
        else:
            print("❌ 未使用增强版行业预测")
            return False
        
        print("\n✅ 集成验证通过，原始接口成功使用增强版功能")
        return True
    
    except Exception as e:
        import traceback
        print(f"\n❌ 集成验证失败: {str(e)}")
        print(traceback.format_exc())
        return False

def generate_report():
    """生成验证报告"""
    print_divider("生成验证报告")
    
    results = {
        "data_completeness": verify_data_completeness(),
        "enhanced_features": verify_enhanced_features(),
        "integration": verify_integration(),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 计算总体通过率
    pass_count = sum(1 for result in results.values() if isinstance(result, bool) and result)
    total_tests = sum(1 for result in results.values() if isinstance(result, bool))
    pass_rate = pass_count / total_tests * 100 if total_tests > 0 else 0
    
    # 生成JSON报告
    report = {
        "title": "增强版行业分析模块验证报告",
        "timestamp": results["timestamp"],
        "results": {
            "data_completeness": {
                "status": "通过" if results["data_completeness"] else "失败",
                "description": "数据完整性和质量检查"
            },
            "enhanced_features": {
                "status": "通过" if results["enhanced_features"] else "失败",
                "description": "增强特性功能验证"
            },
            "integration": {
                "status": "通过" if results["integration"] else "失败",
                "description": "与原有系统集成验证"
            }
        },
        "summary": {
            "pass_rate": f"{pass_rate:.1f}%",
            "pass_count": pass_count,
            "total_tests": total_tests,
            "overall_status": "通过" if pass_rate >= 80 else "部分通过" if pass_rate >= 50 else "失败"
        }
    }
    
    # 保存报告
    with open("enhanced_sector_verification.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"已生成验证报告: enhanced_sector_verification.json")
    
    # 打印总结
    print("\n验证结果总结:")
    print(f"  - 数据完整性: {'通过' if results['data_completeness'] else '失败'}")
    print(f"  - 增强特性: {'通过' if results['enhanced_features'] else '失败'}")
    print(f"  - 集成功能: {'通过' if results['integration'] else '失败'}")
    print(f"\n总体通过率: {pass_rate:.1f}% ({pass_count}/{total_tests})")
    
    overall_status = "通过" if pass_rate >= 80 else "部分通过" if pass_rate >= 50 else "失败"
    print(f"整体评价: {overall_status}")
    
    if overall_status == "通过":
        print("\n🎉 增强版行业分析模块验证成功！该模块功能强大，可以集成到生产环境中。")
    elif overall_status == "部分通过":
        print("\n⚠️ 增强版行业分析模块部分验证通过。请修复失败项后再集成到生产环境。")
    else:
        print("\n❌ 增强版行业分析模块验证失败。需要修复问题后再使用。")
    
    return report

def main():
    """主函数"""
    print_divider("增强版行业分析模块完整性验证")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成验证报告
    report = generate_report()
    
    # 提供使用建议
    print_divider("使用建议")
    
    if report["summary"]["overall_status"] == "通过":
        print("1. 可以放心在生产环境中使用增强版行业分析模块")
        print("2. 启用方式:")
        print("   - 方式一: python sector_analyzer_integration.py")
        print("   - 方式二: 在代码中导入并使用")
        print("     ```python")
        print("     # 导入原始分析器(已增强)")
        print("     from sector_analyzer import SectorAnalyzer")
        print("     analyzer = SectorAnalyzer()")
        print("     ```")
        print("3. 定期更新数据:")
        print("   python fetch_real_sector_data.py")
    elif report["summary"]["overall_status"] == "部分通过":
        print("1. 需要修复验证失败的项目:")
        if not report["results"]["data_completeness"]["status"] == "通过":
            print("   - 修复数据完整性问题: 检查数据源和缓存机制")
        if not report["results"]["enhanced_features"]["status"] == "通过":
            print("   - 完善增强特性: 检查enhance_sector_analyzer.py中缺失的功能")
        if not report["results"]["integration"]["status"] == "通过":
            print("   - 修复集成问题: 检查sector_analyzer_integration.py")
        print("2. 修复后再次运行验证:")
        print("   python verify_enhanced_sectors.py")
    else:
        print("1. 需要大幅修复增强版行业分析模块")
        print("2. 暂时使用原始版本:")
        print("   ```python")
        print("   # 确保使用原始版本")
        print("   from sector_analyzer import SectorAnalyzer")
        print("   # 检查是否已被增强")
        print("   if hasattr(SectorAnalyzer, 'is_enhanced'):")
        print("       print('警告: 分析器已被增强，但增强功能有问题')")
        print("   ```")
        print("3. 修复问题后重新集成")

if __name__ == "__main__":
    main() 