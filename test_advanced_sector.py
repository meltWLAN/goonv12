#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级行业分析测试脚本
用于测试高级行业分析模块的功能
"""

import sys
import logging
import pandas as pd
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestAdvancedSector')

def test_analyzer():
    """测试高级行业分析器功能"""
    print("\n====== 测试高级行业分析器 ======")
    
    try:
        from advanced_sector_analyzer import AdvancedSectorAnalyzer
        
        # 创建分析器实例
        print("创建分析器实例...")
        analyzer = AdvancedSectorAnalyzer(top_n=5)
        
        # 获取行业列表
        print("\n1. 获取行业列表")
        sectors = analyzer.get_sector_list()
        print(f"获取到 {len(sectors)} 个行业")
        
        if sectors:
            print("行业列表示例:")
            for i, sector in enumerate(sectors[:3], 1):
                print(f"  {i}. {sector.get('name', '未知')} ({sector.get('code', '未知')})")
        
        # 获取热门行业
        print("\n2. 获取热门行业")
        hot_sectors = analyzer.analyze_hot_sectors()
        
        if hot_sectors['status'] == 'success':
            sectors_data = hot_sectors['data'].get('hot_sectors', [])
            print(f"成功获取 {len(sectors_data)} 个热门行业")
            
            if sectors_data:
                print("\n热门行业排名:")
                for i, sector in enumerate(sectors_data[:5], 1):
                    print(f"  {i}. {sector.get('name', '未知')} - 热度: {sector.get('hot_score', 0):.2f}")
                    print(f"     涨跌幅: {sector.get('change_pct', 0):.2f}% | 分析: {sector.get('analysis_reason', '无')}")
        else:
            print(f"获取热门行业失败: {hot_sectors.get('message', '未知错误')}")
        
        # 测试行业历史数据
        if sectors:
            print("\n3. 测试获取行业历史数据")
            test_sector = sectors[0]
            sector_code = test_sector.get('code', '')
            sector_name = test_sector.get('name', '')
            
            print(f"获取行业 {sector_name} 的历史数据...")
            hist_data = analyzer.get_sector_history(sector_code, sector_name)
            
            if isinstance(hist_data, pd.DataFrame) and not hist_data.empty:
                print(f"成功获取历史数据，共 {len(hist_data)} 条记录")
                print("\n历史数据示例:")
                
                if '日期' in hist_data.columns:
                    print(hist_data.sort_values('日期', ascending=False).head(3))
                else:
                    print(hist_data.head(3))
            else:
                print("获取历史数据失败")
        
        # 生成行业报告
        print("\n4. 生成行业分析报告")
        report = analyzer.generate_sector_report()
        
        if report['status'] == 'success':
            print("成功生成行业分析报告")
            
            if 'market_summary' in report['data']:
                summary = report['data']['market_summary']
                print("\n市场概况:")
                print(f"  市场趋势: {summary.get('market_trend', '未知')}")
                print(f"  平均涨跌幅: {summary.get('avg_change', 0):.2f}%")
                print(f"  上涨行业: {summary.get('up_sectors', 0)}个")
                print(f"  下跌行业: {summary.get('down_sectors', 0)}个")
                print(f"  北向资金: {summary.get('north_flow', 0):.2f}亿元")
            
            if 'analysis_conclusion' in report['data']:
                print(f"\n分析结论:\n  {report['data']['analysis_conclusion']}")
        else:
            print(f"生成行业分析报告失败: {report.get('message', '未知错误')}")
            
        print("\n====== 高级行业分析器测试完成 ======")
        return True
        
    except ImportError as e:
        print(f"无法导入高级行业分析模块: {str(e)}")
        print("请确认已正确安装高级行业分析模块")
        return False
    except Exception as e:
        print(f"测试过程出错: {str(e)}")
        logger.error(f"测试过程出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_integration():
    """测试集成器功能"""
    print("\n====== 测试高级行业分析集成器 ======")
    
    try:
        from advanced_sector_integration import AdvancedSectorIntegrator
        
        # 创建集成器实例
        print("创建集成器实例...")
        integrator = AdvancedSectorIntegrator()
        
        # 获取热门行业
        print("\n1. 通过集成器获取热门行业")
        result = integrator.get_hot_sectors()
        
        if result['status'] == 'success':
            hot_sectors = result['data'].get('hot_sectors', [])
            print(f"成功获取 {len(hot_sectors)} 个热门行业")
            
            if hot_sectors:
                print("\n热门行业排名:")
                for i, sector in enumerate(hot_sectors[:5], 1):
                    print(f"  {i}. {sector.get('name', '未知')} - 热度: {sector.get('hot_score', 0):.2f}")
            
            # 确认数据源
            source = result['data'].get('source', '未知')
            print(f"\n数据来源: {source}")
        else:
            print(f"获取热门行业失败: {result.get('message', '未知错误')}")
        
        # 获取行业报告
        print("\n2. 通过集成器获取行业报告")
        report = integrator.get_sector_report()
        
        if report['status'] == 'success':
            print("成功获取行业报告")
            
            # 打印报告来源
            source = report['data'].get('report_source', '未知')
            print(f"报告来源: {source}")
            
            if 'analysis_conclusion' in report['data']:
                print(f"\n分析结论:\n  {report['data']['analysis_conclusion']}")
        else:
            print(f"获取行业报告失败: {report.get('message', '未知错误')}")
        
        # 获取单个行业详细数据
        print("\n3. 获取单个行业详细数据")
        # 先获取行业列表
        sectors = integrator.get_sector_list()
        
        if sectors:
            test_sector = sectors[0]
            sector_code = test_sector.get('code', '')
            sector_name = test_sector.get('name', '')
            
            print(f"获取行业 {sector_name} 的详细数据...")
            sector_data = integrator.get_sector_data(sector_code, sector_name)
            
            if sector_data['status'] == 'success':
                print("获取详细数据成功")
                data = sector_data['data']
                print(f"  行业: {data.get('name', '')} ({data.get('code', '')})")
                print(f"  历史记录数: {data.get('records', 0)}")
                print(f"  是否为真实数据: {'是' if data.get('is_real_data', False) else '否'}")
                print(f"  最近收盘价: {data.get('latest_close', 0):.2f}")
            else:
                print(f"获取详细数据失败: {sector_data.get('message', '未知错误')}")
        else:
            print("无法获取行业列表进行测试")
        
        print("\n====== 高级行业分析集成器测试完成 ======")
        return True
        
    except ImportError as e:
        print(f"无法导入高级行业分析集成模块: {str(e)}")
        print("请确认已正确安装高级行业分析模块")
        return False
    except Exception as e:
        print(f"测试过程出错: {str(e)}")
        logger.error(f"测试过程出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    print(f"====== 高级行业分析模块测试 [时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ======\n")
    
    print("请选择测试类型:")
    print("1. 测试高级行业分析器功能")
    print("2. 测试高级行业分析集成器功能")
    print("3. 运行全部测试")
    
    choice = input("请输入选项 [1/2/3]: ").strip()
    
    if choice == '1':
        test_analyzer()
    elif choice == '2':
        test_integration()
    else:
        print("\n运行全部测试...\n")
        test_analyzer()
        print("\n" + "-" * 50 + "\n")
        test_integration()
    
    print("\n====== 测试完成 ======")

if __name__ == "__main__":
    main() 