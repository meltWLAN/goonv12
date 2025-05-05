#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级行业分析模块集成工具
将高级行业分析模块与现有股票系统集成
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("advanced_sector_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AdvancedSectorIntegration")

class AdvancedSectorIntegrator:
    """高级行业分析集成器
    
    将高级行业分析模块与现有系统集成，提供兼容接口
    """
    
    def __init__(self, token=None, top_n=10):
        """初始化集成器
        
        Args:
            token: Tushare API token
            top_n: 热门行业返回数量
        """
        logger.info("初始化高级行业分析集成器")
        
        # 导入高级行业分析模块
        try:
            from advanced_sector_analyzer import AdvancedSectorAnalyzer
            self.advanced_analyzer = AdvancedSectorAnalyzer(token=token, top_n=top_n)
            self.has_advanced = True
            logger.info("成功创建高级行业分析器")
        except ImportError:
            logger.error("无法导入高级行业分析模块")
            self.advanced_analyzer = None
            self.has_advanced = False
        except Exception as e:
            logger.error(f"创建高级行业分析器失败: {str(e)}")
            self.advanced_analyzer = None
            self.has_advanced = False
        
        # 导入原始行业分析模块
        try:
            from sector_analyzer import SectorAnalyzer
            self.legacy_analyzer = SectorAnalyzer(top_n=top_n)
            self.has_legacy = True
            logger.info("成功创建原始行业分析器")
        except ImportError:
            logger.warning("无法导入原始行业分析模块")
            self.legacy_analyzer = None
            self.has_legacy = False
        except Exception as e:
            logger.warning(f"创建原始行业分析器失败: {str(e)}")
            self.legacy_analyzer = None
            self.has_legacy = False
        
        # 检查是否至少有一个分析器可用
        if not self.has_advanced and not self.has_legacy:
            logger.critical("没有可用的行业分析器，系统将无法工作")
            raise RuntimeError("没有可用的行业分析器，请检查依赖")
        
        # 记录初始化状态
        if token:
            logger.info(f"集成器初始化完成，使用token: {token[:4]}...{token[-4:]}")
        else:
            logger.info("集成器初始化完成，使用默认token")
    
    def get_hot_sectors(self) -> Dict:
        """获取热门行业
        
        兼容原始接口，优先使用高级行业分析器
        
        Returns:
            Dict: 热门行业分析结果
        """
        logger.info("获取热门行业分析")
        
        try:
            # 优先使用高级分析器
            if self.has_advanced:
                logger.info("尝试使用高级分析器获取热门行业")
                result = self.advanced_analyzer.analyze_hot_sectors()
                
                if result['status'] == 'success':
                    logger.info("使用高级分析器成功获取热门行业")
                    result['data']['source'] = '高级分析器'
                    return result
                
                logger.warning(f"高级分析器获取失败: {result.get('message', '未知错误')}")
            
            # 如果高级分析器不可用或失败，使用原始分析器
            if self.has_legacy:
                logger.info("尝试使用原始分析器获取热门行业")
                legacy_result = self.legacy_analyzer.analyze_hot_sectors()
                
                if legacy_result['status'] == 'success':
                    logger.info("使用原始分析器成功获取热门行业")
                    legacy_result['data']['source'] = '原始分析器'
                    return legacy_result
                
                logger.error("原始分析器也获取失败")
                return legacy_result
            
            # 如果两者都失败
            logger.error("所有可用分析器都获取失败")
            return {
                'status': 'error',
                'message': "所有可用的行业分析器都获取失败",
                'data': {}
            }
            
        except Exception as e:
            logger.error(f"获取热门行业时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                'status': 'error',
                'message': f"系统错误: {str(e)}",
                'data': {}
            }
    
    def get_sector_report(self) -> Dict:
        """获取行业分析报告
        
        优先使用高级行业分析器生成完整报告
        
        Returns:
            Dict: 行业分析报告
        """
        logger.info("获取行业分析报告")
        
        try:
            # 使用高级分析器生成报告
            report = self.advanced_analyzer.generate_sector_report()
            
            if report['status'] == 'success':
                logger.info("成功生成行业分析报告")
                report['data']['report_source'] = '高级行业分析器'
                return report
            
            logger.warning(f"高级分析器生成报告失败: {report.get('message', '未知错误')}")
            
            # 如果高级分析器失败，尝试使用原始分析器
            if self.has_legacy:
                logger.info("尝试使用原始分析器生成报告")
                try:
                    legacy_report = self.legacy_analyzer.generate_sector_report()
                    if legacy_report['status'] == 'success':
                        logger.info("使用原始分析器成功生成报告")
                        legacy_report['data']['report_source'] = '原始分析器'
                        return legacy_report
                except:
                    logger.error("原始分析器生成报告失败")
            
            return report  # 返回高级分析器的错误结果
            
        except Exception as e:
            logger.error(f"生成行业分析报告时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                'status': 'error',
                'message': f"系统错误: {str(e)}",
                'data': {}
            }
    
    def get_sector_data(self, sector_code: str, sector_name: str = None) -> Dict:
        """获取单个行业的详细数据
        
        Args:
            sector_code: 行业代码
            sector_name: 行业名称
            
        Returns:
            Dict: 行业详细数据
        """
        logger.info(f"获取行业 {sector_name or sector_code} 详细数据")
        
        try:
            # 获取行业历史数据
            hist_data = self.advanced_analyzer.get_sector_history(sector_code, sector_name)
            
            if hist_data is None or hist_data.empty:
                logger.warning(f"无法获取行业 {sector_name or sector_code} 历史数据")
                
                # 尝试使用原始分析器
                if self.has_legacy and hasattr(self.legacy_analyzer, '_get_sector_history'):
                    logger.info("尝试使用原始分析器获取行业历史数据")
                    legacy_data = self.legacy_analyzer._get_sector_history(sector_name, sector_code)
                    if legacy_data is not None and not legacy_data.empty:
                        hist_data = legacy_data
            
            # 如果还是获取不到数据
            if hist_data is None or hist_data.empty:
                return {
                    'status': 'error',
                    'message': f"无法获取行业 {sector_name or sector_code} 历史数据",
                    'data': {}
                }
            
            # 确保列名标准化
            if '收盘' in hist_data.columns:
                close_column = '收盘'
            elif 'close' in hist_data.columns:
                close_column = 'close'
            else:
                close_column = hist_data.columns[3] if len(hist_data.columns) > 3 else None
            
            # 准备返回数据
            is_real_data = True
            if '是真实数据' in hist_data.columns:
                is_real_data = hist_data['是真实数据'].all()
            
            # 将DataFrame转换为字典列表
            history_records = []
            for _, row in hist_data.iterrows():
                record = {}
                for col in hist_data.columns:
                    if col != '是真实数据' and col != '是合成数据':
                        record[col] = row[col]
                history_records.append(record)
            
            return {
                'status': 'success',
                'data': {
                    'code': sector_code,
                    'name': sector_name,
                    'records': len(history_records),
                    'is_real_data': is_real_data,
                    'history': history_records,
                    'latest_close': float(hist_data[close_column].iloc[-1]) if close_column else 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取行业详细数据时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                'status': 'error',
                'message': f"系统错误: {str(e)}",
                'data': {}
            }
    
    def get_sector_list(self) -> List[Dict]:
        """获取行业列表
        
        Returns:
            List[Dict]: 行业列表
        """
        logger.info("获取行业列表")
        
        try:
            # 优先使用高级分析器
            if self.has_advanced:
                logger.info("尝试使用高级分析器获取行业列表")
                sectors = self.advanced_analyzer.get_sector_list()
                
                if sectors:
                    logger.info(f"高级分析器成功获取行业列表，共 {len(sectors)} 个行业")
                    return sectors
                
                logger.warning("高级分析器获取行业列表失败")
            
            # 如果高级分析器不可用或失败，使用原始分析器
            if self.has_legacy:
                logger.info("尝试使用原始分析器获取行业列表")
                legacy_sectors = self.legacy_analyzer.get_sector_list()
                
                if legacy_sectors:
                    logger.info(f"原始分析器成功获取行业列表，共 {len(legacy_sectors)} 个行业")
                    return legacy_sectors
                
                logger.warning("原始分析器获取行业列表失败")
            
            # 如果两者都失败
            logger.error("所有可用分析器都获取行业列表失败")
            return []
            
        except Exception as e:
            logger.error(f"获取行业列表时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return []

# 测试函数
def test_integration():
    """测试高级行业分析集成器"""
    print("====== 测试高级行业分析集成器 ======")
    
    # 初始化集成器
    try:
        integrator = AdvancedSectorIntegrator()
        
        # 测试获取行业列表
        print("\n1. 测试获取行业列表")
        sectors = integrator.get_sector_list()
        print(f"获取到 {len(sectors)} 个行业")
        if sectors:
            print("前5个行业:")
            for i, sector in enumerate(sectors[:5], 1):
                print(f"{i}. {sector['name']} ({sector['code']}) - 涨跌幅: {sector.get('change_pct', 0):.2f}%")
        
        # 测试获取热门行业
        print("\n2. 测试获取热门行业")
        hot_result = integrator.get_hot_sectors()
        if hot_result['status'] == 'success':
            hot_sectors = hot_result['data']['hot_sectors']
            print(f"成功获取热门行业，共 {len(hot_sectors)} 个")
            print("热门行业排名:")
            for i, sector in enumerate(hot_sectors[:5], 1):
                print(f"{i}. {sector['name']} (热度: {sector.get('hot_score', 0):.2f}) - {sector.get('analysis_reason', '')}")
        else:
            print(f"获取热门行业失败: {hot_result.get('message', '未知错误')}")
        
        # 测试获取行业报告
        print("\n3. 测试获取行业分析报告")
        report = integrator.get_sector_report()
        if report['status'] == 'success':
            print("成功生成行业分析报告")
            if 'market_summary' in report['data']:
                summary = report['data']['market_summary']
                print(f"市场趋势: {summary.get('market_trend', '未知')}")
                print(f"平均涨跌幅: {summary.get('avg_change', 0):.2f}%")
                print(f"北向资金: {summary.get('north_flow', 0):.2f}亿元")
            
            if 'analysis_conclusion' in report['data']:
                print(f"\n分析结论: {report['data']['analysis_conclusion']}")
        else:
            print(f"生成行业分析报告失败: {report.get('message', '未知错误')}")
        
        # 测试获取单个行业数据
        if sectors:
            test_sector = sectors[0]
            print(f"\n4. 测试获取单个行业详细数据: {test_sector['name']}")
            sector_data = integrator.get_sector_data(test_sector['code'], test_sector['name'])
            
            if sector_data['status'] == 'success':
                print(f"成功获取行业 {test_sector['name']} 的详细数据")
                print(f"共 {sector_data['data']['records']} 条历史记录")
                print(f"是否为真实数据: {'是' if sector_data['data']['is_real_data'] else '否'}")
                print(f"最新收盘价: {sector_data['data']['latest_close']}")
            else:
                print(f"获取行业详细数据失败: {sector_data.get('message', '未知错误')}")
        
        print("\n====== 测试完成 ======")
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_integration() 