#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析器集成工具
支持简化版和增强版行业分析器

该模块可以:
1. 提供统一的接口函数
2. 缓存和管理行业数据
3. 自动检测并使用可用的行业分析器
"""

import os
import sys
import json
import logging
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='sector_integration.log'
)
logger = logging.getLogger('SectorIntegration')

class SectorAnalyzerIntegrator:
    """行业分析器集成工具"""
    
    def __init__(self, cache_dir='./data_cache', prefer_enhanced=True):
        """初始化集成器
        
        Args:
            cache_dir: 缓存目录
            prefer_enhanced: 是否优先使用增强版分析器
        """
        self.cache_dir = cache_dir
        self.prefer_enhanced = prefer_enhanced
        self.simple_available = False
        self.enhanced_available = False
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 状态文件
        self.status_file = os.path.join(self.cache_dir, 'sector_analyzer_status.json')
        
        # 加载或创建状态文件
        self.status = self._load_status()
        
        # 测试增强版分析器的可用性
        if prefer_enhanced:
            self._test_enhanced_analyzer()
        
        # 测试简化版分析器的可用性
        if not self.enhanced_available or not prefer_enhanced:
            self._test_simple_analyzer()
        
        # 更新状态
        self._update_status()
        
        # 初始化适当的分析器
        self._init_analyzer()
    
    def _load_status(self) -> Dict:
        """加载状态文件"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载状态文件失败: {e}")
        
        # 默认状态
        return {
            "simple_available": False,
            "enhanced_available": False,
            "last_simple_test": None,
            "last_enhanced_test": None,
            "simple_error": None,
            "enhanced_error": None
        }
    
    def _update_status(self):
        """更新状态文件"""
        self.status["simple_available"] = self.simple_available
        self.status["enhanced_available"] = self.enhanced_available
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"更新状态文件失败: {e}")
    
    def _test_simple_analyzer(self):
        """测试简化版分析器"""
        try:
            # 导入简化版分析器
            from fix_sector_analyzer import SimpleSectorAnalyzer
            analyzer = SimpleSectorAnalyzer()
            
            # 测试获取热门行业
            start_time = time.time()
            result = analyzer.get_hot_sectors()
            elapsed = time.time() - start_time
            
            if result['status'] == 'success':
                self.simple_available = True
                self.status["last_simple_test"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.status["simple_error"] = None
                logger.info(f"简化版分析器测试成功，耗时: {elapsed:.2f}秒")
            else:
                self.simple_available = False
                self.status["simple_error"] = result.get('message', '未知错误')
                logger.warning(f"简化版分析器测试失败: {self.status['simple_error']}")
        except Exception as e:
            self.simple_available = False
            self.status["simple_error"] = str(e)
            logger.error(f"简化版分析器测试异常: {e}")
    
    def _test_enhanced_analyzer(self):
        """测试增强版分析器"""
        try:
            # 导入增强版分析器
            from enhanced_sector_analyzer import EnhancedSectorAnalyzer
            analyzer = EnhancedSectorAnalyzer(cache_dir=self.cache_dir)
            
            # 测试获取热门行业
            start_time = time.time()
            result = analyzer.get_hot_sectors()
            elapsed = time.time() - start_time
            
            if result['status'] == 'success':
                self.enhanced_available = True
                self.status["last_enhanced_test"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.status["enhanced_error"] = None
                logger.info(f"增强版分析器测试成功，耗时: {elapsed:.2f}秒")
            else:
                self.enhanced_available = False
                self.status["enhanced_error"] = result.get('message', '未知错误')
                logger.warning(f"增强版分析器测试失败: {self.status['enhanced_error']}")
                
            # 导入技术分析模块
            from sector_technical_analysis import SectorTechnicalAnalyzer
            tech_analyzer = SectorTechnicalAnalyzer(cache_dir=self.cache_dir)
            
        except Exception as e:
            self.enhanced_available = False
            self.status["enhanced_error"] = str(e)
            logger.error(f"增强版分析器测试异常: {e}")
    
    def _init_analyzer(self):
        """初始化适当的分析器"""
        if self.enhanced_available and self.prefer_enhanced:
            try:
                from enhanced_sector_analyzer import EnhancedSectorAnalyzer
                self.analyzer = EnhancedSectorAnalyzer(cache_dir=self.cache_dir)
                
                from sector_technical_analysis import SectorTechnicalAnalyzer
                self.tech_analyzer = SectorTechnicalAnalyzer(cache_dir=self.cache_dir)
                
                from integrate_enhanced_sector import EnhancedSectorIntegrator
                self.enhanced_integrator = EnhancedSectorIntegrator(cache_dir=self.cache_dir)
                
                logger.info("使用增强版行业分析器")
            except Exception as e:
                logger.error(f"初始化增强版分析器失败: {e}")
                self.enhanced_available = False
                
        if not self.enhanced_available or not self.prefer_enhanced:
            try:
                from fix_sector_analyzer import SimpleSectorAnalyzer
                self.analyzer = SimpleSectorAnalyzer()
                logger.info("使用简化版行业分析器")
            except Exception as e:
                logger.error(f"初始化简化版分析器失败: {e}")
                self.simple_available = False
    
    def get_hot_sectors(self) -> Dict:
        """获取热门行业"""
        try:
            if self.enhanced_available and self.prefer_enhanced:
                return self.enhanced_integrator.get_hot_sectors()
            elif self.simple_available:
                return self.analyzer.get_hot_sectors()
            else:
                return {"status": "error", "message": "没有可用的行业分析器"}
        except Exception as e:
            logger.error(f"获取热门行业失败: {e}")
            return {"status": "error", "message": f"获取热门行业失败: {str(e)}"}
    
    def get_sector_technical_analysis(self, sector_name: str) -> Dict:
        """获取行业技术分析
        
        Args:
            sector_name: 行业名称
        """
        try:
            if self.enhanced_available and self.prefer_enhanced:
                return self.enhanced_integrator.get_sector_technical(sector_name)
            elif self.simple_available:
                return self.analyzer.get_sector_technical_analysis(sector_name)
            else:
                return {"status": "error", "message": "没有可用的行业分析器"}
        except Exception as e:
            logger.error(f"获取行业技术分析失败: {e}")
            return {"status": "error", "message": f"获取行业技术分析失败: {str(e)}"}
    
    def get_sector_stocks(self, sector_name: str) -> Dict:
        """获取行业成分股
        
        Args:
            sector_name: 行业名称
        """
        try:
            if self.enhanced_available and self.prefer_enhanced:
                return self.enhanced_integrator.get_sector_stocks(sector_name)
            elif self.simple_available:
                return self.analyzer.get_sector_stocks(sector_name)
            else:
                return {"status": "error", "message": "没有可用的行业分析器"}
        except Exception as e:
            logger.error(f"获取行业成分股失败: {e}")
            return {"status": "error", "message": f"获取行业成分股失败: {str(e)}"}
    
    def get_unified_analysis(self) -> Dict:
        """获取统一格式的行业分析结果
        
        返回一个标准化格式的行业分析结果
        """
        try:
            if self.enhanced_available and self.prefer_enhanced:
                return self.enhanced_integrator.get_unified_analysis()
            
            # 如果没有增强版或不优先使用增强版，则使用简化版
            result = self.get_hot_sectors()
            
            if result['status'] != 'success':
                return result
            
            hot_sectors = result['data']['hot_sectors']
            
            # 如果有热门行业，获取第一个的技术分析
            if hot_sectors and len(hot_sectors) > 0:
                top_sector = hot_sectors[0]
                tech_result = self.get_sector_technical_analysis(top_sector['name'])
                
                if tech_result['status'] == 'success':
                    # 合并技术分析结果
                    result['data']['technical_analysis'] = tech_result['data']
            
            # 添加一些其他分析信息
            result['data']['market_sentiment'] = '中性'
            result['data']['north_flow'] = 0.0
            result['data']['analyzer_version'] = 'enhanced' if self.enhanced_available and self.prefer_enhanced else 'simple'
                
            return result
        except Exception as e:
            logger.error(f"获取统一分析失败: {e}")
            return {"status": "error", "message": f"获取统一分析失败: {str(e)}"}
    
    def generate_investment_report(self) -> Dict:
        """生成行业投资报告
        
        返回全面的行业分析和投资建议报告
        """
        try:
            if self.enhanced_available and self.prefer_enhanced:
                return self.enhanced_integrator.generate_investment_report()
            else:
                return {
                    'status': 'error',
                    'message': '增强版行业分析器不可用，无法生成投资报告'
                }
        except Exception as e:
            logger.error(f"生成投资报告失败: {e}")
            return {"status": "error", "message": f"生成投资报告失败: {str(e)}"}

# 测试代码
if __name__ == "__main__":
    print("行业分析器集成工具测试")
    integrator = SectorAnalyzerIntegrator(prefer_enhanced=True)
    
    print(f"简化版分析器可用: {integrator.simple_available}")
    print(f"增强版分析器可用: {integrator.enhanced_available}")
    
    print("\n正在获取热门行业...")
    hot_sectors = integrator.get_hot_sectors()
    
    if hot_sectors['status'] == 'success':
        print(f"热门行业数据源: {hot_sectors['data'].get('source', '未知')}")
        print("\n热门行业列表:")
        for i, sector in enumerate(hot_sectors['data']['hot_sectors'], 1):
            print(f"{i}. {sector['name']} - 热度: {sector.get('hot_score', 0)}")
    else:
        print(f"获取热门行业失败: {hot_sectors.get('message')}")
    
    # 测试统一分析
    print("\n正在获取统一分析结果...")
    unified = integrator.get_unified_analysis()
    
    if unified['status'] == 'success':
        print(f"统一分析数据源: {unified['data'].get('source', '未知')}")
        
        # 检查是否有技术分析
        if 'technical_analysis' in unified['data']:
            tech = unified['data']['technical_analysis']
            print(f"\n行业 {tech['sector']} 技术分析:")
            print(f"技术评分: {tech.get('tech_score', 0)}")
            print(f"趋势: {tech.get('trend_analysis', {}).get('trend', '未知')}")
            print(f"交易建议: {tech.get('trade_signal', {}).get('signal', '未知')}")
    else:
        print(f"获取统一分析失败: {unified.get('message')}")
        
    # 测试生成投资报告
    if integrator.enhanced_available and integrator.prefer_enhanced:
        print("\n生成投资报告...")
        report = integrator.generate_investment_report()
        if report['status'] == 'success':
            print(f"\n{report['data']['title']} ({report['data']['date']})")
            print(f"市场概况: {report['data']['market_overview']['comment']}")
            print("\n投资建议:")
            for rec in report['data']['recommendations']:
                print(f"{rec['rating']} {rec['sector']}: {rec['investment_advice']}") 