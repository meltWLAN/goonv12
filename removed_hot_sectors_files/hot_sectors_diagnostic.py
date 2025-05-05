#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
热门行业功能诊断脚本
全面测试热门行业分析和可视化功能，验证修复是否完全成功
"""

import os
import sys
import json
import logging
from datetime import datetime
import matplotlib.pyplot as plt

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='hot_sectors_diagnostic.log',
    filemode='w'
)
logger = logging.getLogger('HotSectorsDiagnostic')

def test_enhanced_sector_analyzer():
    """测试增强版行业分析器"""
    logger.info("测试增强版行业分析器...")
    
    try:
        from enhanced_sector_analyzer import EnhancedSectorAnalyzer
        
        # 实例化分析器
        analyzer = EnhancedSectorAnalyzer()
        
        # 1. 测试方法存在性
        methods_to_check = [
            'analyze_hot_sectors',
            'get_hot_sectors',
            '_calculate_market_sentiment',
            '_get_sector_index_data',
            '_get_sector_fund_flow'
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if not hasattr(analyzer, method) or not callable(getattr(analyzer, method)):
                missing_methods.append(method)
        
        if missing_methods:
            logger.error(f"缺少关键方法: {', '.join(missing_methods)}")
            return False
        
        # 2. 测试 analyze_hot_sectors 方法
        logger.info("测试 analyze_hot_sectors 方法...")
        result = analyzer.analyze_hot_sectors(top_n=5)
        
        if result['status'] != 'success':
            logger.error(f"分析失败: {result.get('message', '未知错误')}")
            return False
        
        # 3. 测试数据结构
        required_fields = [
            'hot_sectors',
            'total_sectors',
            'market_sentiment',
            'update_time',
            'prediction_data'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in result['data']:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"结果数据缺少字段: {', '.join(missing_fields)}")
            return False
        
        # 4. 验证 prediction_data 字段
        if not result['data']['prediction_data']:
            logger.error("prediction_data 字段为空")
            return False
        
        # 打印诊断信息
        logger.info(f"行业分析成功! 找到 {len(result['data']['hot_sectors'])} 个热门行业")
        logger.info(f"预测数据中包含 {len(result['data']['prediction_data'])} 项预测")
        
        # 保存分析结果
        with open('hot_sectors_diagnostic_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        logger.info("分析结果已保存到 hot_sectors_diagnostic_result.json")
        return True
    
    except Exception as e:
        import traceback
        logger.error(f"测试增强版行业分析器时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_visualization():
    """测试可视化功能"""
    logger.info("测试可视化功能...")
    
    try:
        from enhanced_sector_analyzer import EnhancedSectorAnalyzer
        from sector_visualization import SectorVisualizationDialog
        from PyQt5.QtWidgets import QApplication
        
        # 初始化QApplication
        app = QApplication(sys.argv)
        
        # 获取行业数据
        analyzer = EnhancedSectorAnalyzer()
        result = analyzer.analyze_hot_sectors(top_n=10)
        
        if result['status'] != 'success':
            logger.error(f"获取行业数据失败: {result.get('message', '未知错误')}")
            return False
        
        # 创建可视化对话框
        dialog = SectorVisualizationDialog(viz_data=result)
        
        # 检查所有标签页
        if dialog.tab_widget.count() < 5:
            logger.error(f"标签页数量不足，当前只有 {dialog.tab_widget.count()} 个")
            return False
        
        # 检查标签页名称
        expected_tabs = ["热度趋势", "热度分布", "行业轮动", "产业链关系", "预测结果"]
        for i, tab_name in enumerate(expected_tabs):
            if i < dialog.tab_widget.count():
                actual_name = dialog.tab_widget.tabText(i)
                if tab_name not in actual_name:
                    logger.warning(f"标签页名称不匹配: 期望 '{tab_name}'，实际 '{actual_name}'")
        
        logger.info("可视化功能测试通过")
        return True
    
    except Exception as e:
        import traceback
        logger.error(f"测试可视化功能时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_data_flow():
    """测试数据流"""
    logger.info("测试数据流...")
    
    try:
        # 1. 从增强版行业分析器获取数据
        from enhanced_sector_analyzer import EnhancedSectorAnalyzer
        analyzer = EnhancedSectorAnalyzer()
        result = analyzer.analyze_hot_sectors(top_n=5)
        
        if result['status'] != 'success':
            logger.error(f"获取行业数据失败: {result.get('message', '未知错误')}")
            return False
        
        # 2. 检查数据流向可视化模块
        prediction_data = result['data'].get('prediction_data', [])
        if not prediction_data:
            logger.error("prediction_data 字段为空，无法流向可视化模块")
            return False
        
        # 3. 验证预测数据格式
        for item in prediction_data:
            if not isinstance(item, dict):
                logger.error(f"预测数据项不是字典: {item}")
                return False
            
            if 'name' not in item or 'technical_score' not in item:
                logger.error(f"预测数据项缺少必要字段: {item}")
                return False
        
        logger.info("数据流测试通过")
        return True
    
    except Exception as e:
        import traceback
        logger.error(f"测试数据流时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def generate_report(results):
    """生成诊断报告"""
    logger.info("生成诊断报告...")
    
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'results': results,
        'summary': {
            'total_tests': len(results),
            'passed': sum(1 for r in results.values() if r),
            'failed': sum(1 for r in results.values() if not r)
        }
    }
    
    # 计算总体状态
    report['status'] = 'PASS' if report['summary']['failed'] == 0 else 'FAIL'
    
    # 保存报告
    with open('hot_sectors_diagnostic_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    # 打印摘要
    print("\n热门行业功能诊断报告:")
    print(f"测试时间: {report['timestamp']}")
    print(f"总体状态: {'✅ 通过' if report['status'] == 'PASS' else '❌ 失败'}")
    print(f"测试总数: {report['summary']['total_tests']}")
    print(f"通过测试: {report['summary']['passed']}")
    print(f"失败测试: {report['summary']['failed']}")
    
    # 打印各测试结果
    print("\n详细测试结果:")
    for test_name, result in results.items():
        status = '✅ 通过' if result else '❌ 失败'
        print(f"  {test_name}: {status}")
    
    print("\n详细日志已保存到 hot_sectors_diagnostic.log")
    print("诊断报告已保存到 hot_sectors_diagnostic_report.json")
    
    return report

def main():
    """主函数"""
    print("开始热门行业功能全面诊断...")
    
    # 运行测试
    results = {
        '增强版行业分析器': test_enhanced_sector_analyzer(),
        '可视化功能': test_visualization(),
        '数据流': test_data_flow()
    }
    
    # 生成报告
    report = generate_report(results)
    
    return 0 if report['status'] == 'PASS' else 1

if __name__ == "__main__":
    sys.exit(main()) 