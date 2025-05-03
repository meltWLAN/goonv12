#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复版增强型行业分析器
增加了市场趋势信息和行业评分
"""

import os
import sys
import time
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 获取原始版本
from enhanced_sector_analyzer import EnhancedSectorAnalyzer as OriginalEnhancedSectorAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='enhanced_sector_fixed.log',
    filemode='a'
)
logger = logging.getLogger('EnhancedSectorFixed')

class EnhancedSectorAnalyzer(OriginalEnhancedSectorAnalyzer):
    """修复版增强型行业分析器"""
    
    def __init__(self, token: str = None, cache_dir: str = './data_cache'):
        """初始化修复版增强型行业分析器"""
        super().__init__(token, cache_dir)
        self.logger = logger
        self.logger.info("修复版增强型行业分析器已初始化")
    
    def get_hot_sectors(self, top_n: int = 10, force_refresh: bool = False) -> Dict:
        """获取热门行业分析
        
        Args:
            top_n: 返回的热门行业数量
            force_refresh: 是否强制刷新缓存
            
        Returns:
            包含热门行业的字典
        """
        # 调用原始方法
        original_result = super().get_hot_sectors(top_n, force_refresh)
        
        # 如果原始结果不成功，直接返回
        if original_result.get('status') != 'success':
            return original_result
        
        # 确保原始结果中有'data'字段
        if 'data' not in original_result:
            original_result['data'] = {}
        
        # 添加市场趋势信息
        try:
            market_trend_data = self._get_market_trend()
            
            # 更新结果
            original_result['data'].update({
                'market_trend': market_trend_data.get('trend', 'neutral'),
                'market_chg_pct': market_trend_data.get('change_percent', 0.0),
                'market_status': market_trend_data.get('status', '正常'),
                'market_update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # 为每个行业添加技术评分
            self._add_sector_tech_scores(original_result['data'])
            
        except Exception as e:
            self.logger.error(f"添加市场趋势信息失败: {e}")
        
        return original_result
    
    def _get_market_trend(self) -> Dict:
        """获取市场趋势
        
        Returns:
            市场趋势数据
        """
        try:
            # 从缓存加载
            cache_path = os.path.join(self.cache_dir, 'market_trend.json')
            if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < 3600):  # 1小时缓存
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
            
            # 从tushare获取上证指数数据
            index_data = self.pro.index_daily(ts_code='000001.SH', start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
            
            if index_data is None or index_data.empty:
                return {'trend': 'neutral', 'change_percent': 0.0, 'status': '数据不足'}
            
            # 计算大盘趋势
            latest = index_data.iloc[0]
            prev = index_data.iloc[min(5, len(index_data)-1)]
            change_percent = (latest['close'] - prev['close']) / prev['close'] * 100
            
            # 确定趋势
            if change_percent > 5:
                trend = 'strong_bull'
                status = '强势上涨'
            elif change_percent > 2:
                trend = 'bull'
                status = '上涨'
            elif change_percent < -5:
                trend = 'strong_bear'
                status = '强势下跌'
            elif change_percent < -2:
                trend = 'bear'
                status = '下跌'
            else:
                trend = 'neutral'
                status = '震荡'
            
            # 构建结果
            result = {
                'trend': trend,
                'change_percent': float(change_percent),
                'status': status,
                'latest_close': float(latest['close']),
                'prev_close': float(prev['close']),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 保存到缓存
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False)
            except Exception as e:
                self.logger.warning(f"保存市场趋势缓存失败: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取市场趋势失败: {e}")
            return {'trend': 'neutral', 'change_percent': 0.0, 'status': '获取失败'}
    
    def _add_sector_tech_scores(self, data: Dict) -> None:
        """为热门行业添加技术评分
        
        Args:
            data: 包含热门行业的数据字典
        """
        if 'hot_sectors' not in data:
            return
        
        # 遍历热门行业
        for sector in data['hot_sectors']:
            try:
                sector_name = sector['name']
                sector_code = sector.get('code', '') or self.get_sector_code(sector_name)
                
                # 获取行业技术分析
                from sector_technical_analysis import SectorTechnicalAnalyzer
                tech_analyzer = SectorTechnicalAnalyzer(cache_dir=self.cache_dir)
                tech_result = tech_analyzer.analyze_sector(sector_code, sector_name)
                
                # 如果获取成功，添加技术评分
                if tech_result['status'] == 'success':
                    sector['tech_score'] = tech_result['data'].get('tech_score', 50)
                    
                    # 添加交易信号
                    if 'trade_signal' in tech_result['data']:
                        sector['trade_signal'] = tech_result['data']['trade_signal'].get('action', '观望')
                
            except Exception as e:
                self.logger.warning(f"为行业 {sector.get('name', '')} 添加技术评分失败: {e}")
                # 添加默认评分
                sector['tech_score'] = 50

# 测试代码
if __name__ == "__main__":
    analyzer = EnhancedSectorAnalyzer()
    result = analyzer.get_hot_sectors()
    print(f"热门行业分析结果: {result['status']}")
    if result['status'] == 'success':
        print(f"市场趋势: {result['data'].get('market_trend', '未知')}")
        print(f"市场变化: {result['data'].get('market_chg_pct', 0.0):.2f}%")
        print("\n热门行业:")
        for i, sector in enumerate(result['data']['hot_sectors'][:5], 1):
            print(f"{i}. {sector['name']} - 热度: {sector.get('hot_score', 0):.2f}, 技术评分: {sector.get('tech_score', 0)}") 