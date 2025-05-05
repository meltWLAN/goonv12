#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版行业分析器测试脚本
用于测试增强版行业分析器的功能
"""

import sys
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_sector_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('EnhancedSectorTest')

def format_json(data):
    """格式化JSON数据"""
    return json.dumps(data, ensure_ascii=False, indent=2)

def print_separator(title):
    """打印分隔线"""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def main():
    print_separator("增强版行业分析器测试")
    logger.info("开始测试增强版行业分析器")
    
    try:
        # 导入集成模块
        from integrate_sector_analyzer import SectorAnalyzerIntegrator
        
        # 创建集成器，优先使用增强版
        integrator = SectorAnalyzerIntegrator(prefer_enhanced=True)
        
        # 检查分析器状态
        print(f"简化版分析器可用: {integrator.simple_available}")
        print(f"增强版分析器可用: {integrator.enhanced_available}")
        
        if not integrator.enhanced_available and not integrator.simple_available:
            logger.error("没有可用的行业分析器")
            return 1
        
        # 测试热门行业功能
        print_separator("热门行业分析")
        logger.info("测试获取热门行业")
        hot_sectors = integrator.get_hot_sectors()
        
        if hot_sectors['status'] == 'success':
            data_source = hot_sectors['data'].get('source', '未知')
            analyzer_version = hot_sectors['data'].get('analyzer_version', '未知')
            print(f"数据来源: {data_source}")
            print(f"分析器版本: {analyzer_version}")
            
            sectors = hot_sectors['data']['hot_sectors']
            print(f"\n共找到 {len(sectors)} 个热门行业:")
            
            for i, sector in enumerate(sectors, 1):
                print(f"{i}. {sector['name']} - 热度: {sector.get('hot_score', 0)}")
                print(f"   行业状态: {sector.get('industry_status', '未知')}")
                print(f"   交易信号: {sector.get('trade_signal', '未知')}")
                print(f"   分析: {sector.get('analysis', '无')}")
        else:
            logger.error(f"获取热门行业失败: {hot_sectors.get('message')}")
            print(f"错误: {hot_sectors.get('message')}")
        
        # 如果有热门行业，测试技术分析功能
        if hot_sectors['status'] == 'success' and hot_sectors['data']['hot_sectors']:
            # 选择第一个热门行业进行技术分析
            top_sector = hot_sectors['data']['hot_sectors'][0]
            sector_name = top_sector['name']
            sector_code = top_sector.get('code', '')
            
            print_separator(f"行业技术分析 - {sector_name}")
            logger.info(f"测试获取行业 {sector_name} 技术分析")
            
            tech_analysis = integrator.get_sector_technical_analysis(sector_name)
            
            if tech_analysis['status'] == 'success':
                data = tech_analysis['data']
                print(f"技术评分: {data.get('tech_score', 0)}/100")
                print(f"当前价格: {data.get('price', 0)}")
                print(f"涨跌幅: {data.get('change', 0)}%")
                
                # 显示趋势分析
                trend = data.get('trend_analysis', {})
                print(f"\n趋势分析:")
                print(f"趋势方向: {trend.get('trend', '未知')}")
                print(f"趋势强度: {trend.get('strength', 0)}")
                print(f"支撑位: {trend.get('support', 0)}")
                print(f"阻力位: {trend.get('resistance', 0)}")
                print(f"分析: {trend.get('analysis', '无')}")
                
                # 显示指标信号
                indicators = data.get('indicators', {})
                print(f"\n技术指标信号:")
                for name, indicator in indicators.items():
                    print(f"{name.upper()}: {indicator.get('signal', '未知')}")
                
                # 显示交易信号
                signal = data.get('trade_signal', {})
                print(f"\n交易建议:")
                print(f"信号: {signal.get('signal', '未知')}")
                print(f"建议: {signal.get('action', '无')}")
                print(f"说明: {signal.get('description', '无')}")
            else:
                logger.error(f"获取行业技术分析失败: {tech_analysis.get('message')}")
                print(f"错误: {tech_analysis.get('message')}")
        
        # 测试成分股功能
        if hot_sectors['status'] == 'success' and hot_sectors['data']['hot_sectors']:
            sector_name = hot_sectors['data']['hot_sectors'][0]['name']
            
            print_separator(f"行业成分股 - {sector_name}")
            logger.info(f"测试获取行业 {sector_name} 成分股")
            
            stocks_result = integrator.get_sector_stocks(sector_name)
            
            if stocks_result['status'] == 'success':
                stocks = stocks_result['data']['stocks']
                print(f"共找到 {len(stocks)} 支成分股:")
                
                # 只显示前10支
                for i, stock in enumerate(stocks[:10], 1):
                    print(f"{i}. {stock['ts_code']} - {stock['name']}")
                
                if len(stocks) > 10:
                    print(f"... 还有 {len(stocks) - 10} 支股票")
            else:
                logger.error(f"获取行业成分股失败: {stocks_result.get('message')}")
                print(f"错误: {stocks_result.get('message')}")
        
        # 如果增强版可用，测试投资报告功能
        if integrator.enhanced_available:
            print_separator("行业投资报告")
            logger.info("测试生成行业投资报告")
            
            report = integrator.generate_investment_report()
            
            if report['status'] == 'success':
                report_data = report['data']
                print(f"{report_data['title']} ({report_data['date']})")
                
                # 显示市场概况
                market = report_data.get('market_overview', {})
                print(f"\n市场概况:")
                print(f"趋势: {market.get('trend', '未知')}")
                print(f"变化: {market.get('change', 0)}%")
                print(f"评论: {market.get('comment', '无')}")
                
                # 显示投资建议
                recommendations = report_data.get('recommendations', [])
                print(f"\n投资建议:")
                for rec in recommendations:
                    print(f"{rec['rating']} {rec['sector']}: {rec['investment_advice']}")
                    print(f"   要点: {', '.join(rec['key_points'])}")
                    print(f"   风险因素: {', '.join(rec['risk_factors'])}")
            else:
                logger.error(f"生成投资报告失败: {report.get('message')}")
                print(f"错误: {report.get('message')}")
        
        logger.info("增强版行业分析器测试完成")
        return 0
        
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        print(f"错误: 导入模块失败 - {e}")
        return 1
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 