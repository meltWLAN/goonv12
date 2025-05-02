#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析器集成工具
只使用简化版行业分析器的版本

该模块可以:
1. 提供统一的接口函数
2. 缓存和管理行业数据
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
    """行业分析器集成工具 - 简化版"""
    
    def __init__(self, cache_dir='./data_cache'):
        """初始化集成器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.simple_available = False
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 状态文件
        self.status_file = os.path.join(self.cache_dir, 'sector_analyzer_status.json')
        
        # 加载或创建状态文件
        self.status = self._load_status()
        
        # 测试简化版分析器的可用性
        self._test_simple_analyzer()
        
        # 更新状态
        self._update_status()
    
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
            "last_simple_test": None,
            "simple_error": None
        }
    
    def _update_status(self):
        """更新状态文件"""
        self.status["simple_available"] = self.simple_available
        
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
    
    def get_hot_sectors(self) -> Dict:
        """获取热门行业"""
        try:
            from fix_sector_analyzer import SimpleSectorAnalyzer
            analyzer = SimpleSectorAnalyzer()
            result = analyzer.get_hot_sectors()
            
            # 标记数据来源
            if result['status'] == 'success':
                result['data']['source'] = 'simple'
            
            return result
        except Exception as e:
            logger.error(f"简化版分析器获取热门行业失败: {e}")
            return {"status": "error", "message": f"简化版分析器获取热门行业失败: {str(e)}"}
    
    def get_sector_technical_analysis(self, sector_name: str) -> Dict:
        """获取行业技术分析
        
        Args:
            sector_name: 行业名称
        """
        try:
            from fix_sector_analyzer import SimpleSectorAnalyzer
            analyzer = SimpleSectorAnalyzer()
            result = analyzer.get_sector_technical_analysis(sector_name)
            
            # 标记数据来源
            if result['status'] == 'success':
                result['data']['source'] = 'simple'
            
            return result
        except Exception as e:
            logger.error(f"简化版分析器获取行业技术分析失败: {e}")
            return {"status": "error", "message": f"简化版分析器获取行业技术分析失败: {str(e)}"}
    
    def get_unified_analysis(self) -> Dict:
        """获取统一格式的行业分析结果
        
        返回一个标准化格式的行业分析结果
        """
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
            
        return result

# 测试代码
if __name__ == "__main__":
    print("行业分析器集成工具测试 - 简化版")
    integrator = SectorAnalyzerIntegrator()
    
    print(f"简化版分析器可用: {integrator.simple_available}")
    
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
            print(f"趋势: {tech['prediction'].get('trend', '未知')}")
            print(f"分析: {tech['prediction'].get('analysis', '无')}")
    else:
        print(f"获取统一分析失败: {unified.get('message')}") 