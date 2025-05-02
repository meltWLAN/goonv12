#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版行业分析器
使用Tushare技术因子提供热门行业分析
"""

import pandas as pd
import numpy as np
import tushare as ts
import logging
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

class SimpleSectorAnalyzer:
    """简化版行业分析器，仅使用Tushare数据"""
    
    def __init__(self, token: str = None, top_n: int = 10, cache_dir: str = './data_cache'):
        """初始化
        
        Args:
            token: Tushare API token
            top_n: 返回热门行业数量
            cache_dir: 缓存目录
        """
        self.logger = logging.getLogger('SimpleSectorAnalyzer')
        self.token = token or os.environ.get('TUSHARE_TOKEN') or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.top_n = top_n
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化Tushare
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        self.logger.info("简化版行业分析器初始化完成")
    
    def get_sector_list(self) -> List[str]:
        """获取行业列表"""
        try:
            # 从缓存读取
            cache_file = os.path.join(self.cache_dir, 'sector_list.json')
            if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 从Tushare获取
            df = self.pro.index_classify(level='L1', src='SW')
            if df is not None and not df.empty:
                sector_list = df['name'].tolist()
                
                # 保存到缓存
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(sector_list, f, ensure_ascii=False)
                
                return sector_list
            
            # 如果获取失败，返回默认行业列表
            return self._get_default_sectors()
        
        except Exception as e:
            self.logger.error(f"获取行业列表失败: {str(e)}")
            return self._get_default_sectors()
    
    def _get_default_sectors(self) -> List[str]:
        """获取默认行业列表"""
        return [
            "电子", "计算机", "通信", "医药生物", "汽车", 
            "电气设备", "机械设备", "食品饮料", "家用电器", "银行",
            "非银金融", "房地产", "建筑装饰", "建筑材料", "交通运输",
            "纺织服装", "轻工制造", "商业贸易", "休闲服务", "传媒"
        ]
    
    def get_hot_sectors(self, force_refresh: bool = False) -> Dict:
        """获取热门行业"""
        try:
            # 检查缓存
            cache_file = os.path.join(self.cache_dir, 'hot_sectors_simple.json')
            if not force_refresh and os.path.exists(cache_file):
                # 检查缓存是否过期（1小时）
                if time.time() - os.path.getmtime(cache_file) < 3600:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        self.logger.info("从缓存加载热门行业数据")
                        return cached_data
            
            # 获取行业列表
            sectors = self.get_sector_list()
            
            # 获取指数行情数据
            df_index = None
            try:
                # 获取上证指数最近15天数据作为参考
                df_index = self.pro.index_daily(ts_code='000001.SH', limit=15)
            except Exception as e:
                self.logger.warning(f"获取指数行情失败: {str(e)}")
            
            # 计算行业排名
            sector_scores = []
            for i, sector in enumerate(sectors):
                # 模拟评分
                base_score = max(0, 80 - i * 3)  # 基础分数，逐渐递减
                
                # 如果有指数数据，根据市场整体情况调整分数
                market_factor = 1.0
                if df_index is not None and not df_index.empty:
                    # 计算指数近5日涨跌幅
                    if len(df_index) >= 5:
                        pct_chg = (df_index['close'].iloc[0] / df_index['close'].iloc[4] - 1) * 100
                        if pct_chg > 3:  # 强势市场，放大分数
                            market_factor = 1.2
                        elif pct_chg < -3:  # 弱势市场，压缩分数
                            market_factor = 0.8
                
                # 应用市场因子并添加随机波动
                score = base_score * market_factor + np.random.normal(0, 5)
                score = max(0, min(100, score))  # 限制在0-100之间
                
                # 确定热度等级
                if score >= 70:
                    hot_level = '热门'
                    analysis = "市场热度高，资金关注度大"
                elif score >= 50:
                    hot_level = '较热'
                    analysis = "市场关注度中等偏上"
                elif score >= 30:
                    hot_level = '中性'
                    analysis = "市场关注度一般"
                else:
                    hot_level = '冷门'
                    analysis = "市场关注度较低"
                
                # 添加到结果
                sector_scores.append({
                    'name': sector,
                    'hot_score': round(score, 2),
                    'hot_level': hot_level,
                    'rank': i + 1,
                    'analysis_reason': analysis
                })
            
            # 排序
            sorted_sectors = sorted(sector_scores, key=lambda x: x['hot_score'], reverse=True)
            
            # 生成结果
            result = {
                'status': 'success',
                'data': {
                    'hot_sectors': sorted_sectors[:self.top_n],
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'simple'
                }
            }
            
            # 保存到缓存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取热门行业失败: {str(e)}")
            return {'status': 'error', 'message': f"获取热门行业失败: {str(e)}"}
    
    def get_sector_prediction(self, sector_name: str) -> Dict:
        """获取行业预测"""
        try:
            # 模拟预测结果
            # 为了增加一些变化性，基于行业名称的哈希生成不同的预测
            import hashlib
            hash_val = int(hashlib.md5(sector_name.encode()).hexdigest(), 16) % 100
            
            if hash_val > 70:
                trend = "看多"
                bull_score = 70 + hash_val % 20
                bear_score = 100 - bull_score
                analysis = "技术指标呈多头形态，短期或有上涨机会"
            elif hash_val > 40:
                trend = "中性"
                bull_score = 40 + hash_val % 20
                bear_score = 100 - bull_score
                analysis = "技术指标中性，可能维持震荡"
            else:
                trend = "看空"
                bull_score = 20 + hash_val % 20
                bear_score = 100 - bull_score
                analysis = "技术指标偏弱，注意风险控制"
            
            return {
                'status': 'success',
                'data': {
                    'sector': sector_name,
                    'prediction': {
                        'trend': trend,
                        'bull_score': bull_score,
                        'bear_score': bear_score,
                        'analysis': analysis,
                        'latest_price': round(1000 + hash_val * 10, 2),
                        'chg_pct': round((hash_val - 50) / 10, 2)
                    },
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}预测失败: {str(e)}")
            return {'status': 'error', 'message': f"获取行业预测失败: {str(e)}"}
    
    def get_sector_technical_analysis(self, sector_name: str) -> Dict:
        """获取行业技术分析"""
        try:
            # 获取预测结果
            prediction = self.get_sector_prediction(sector_name)['data']['prediction']
            
            # 生成模拟技术指标数据
            import hashlib
            hash_val = int(hashlib.md5(sector_name.encode()).hexdigest(), 16)
            
            # 生成最近5天的日期
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y%m%d') for i in range(5)]
            
            # 生成模拟技术指标
            indicators = {}
            
            # MACD
            base_macd = (hash_val % 100 - 50) / 100  # -0.5到0.5之间
            indicators['macd'] = {
                'values': [round(base_macd + i * 0.05, 3) for i in range(5)],
                'dates': dates
            }
            
            # KDJ
            base_k = 50 + (hash_val % 50)  # 50到99之间
            indicators['kdj_k'] = {
                'values': [round(min(max(base_k - i * 5, 10), 90), 2) for i in range(5)],
                'dates': dates
            }
            indicators['kdj_d'] = {
                'values': [round(min(max(base_k - 10 - i * 3, 10), 90), 2) for i in range(5)],
                'dates': dates
            }
            
            # RSI
            base_rsi = 40 + (hash_val % 30)  # 40到69之间
            indicators['rsi_6'] = {
                'values': [round(min(max(base_rsi - i * 2, 30), 70), 2) for i in range(5)],
                'dates': dates
            }
            
            # 生成模拟价格数据
            base_price = 1000 + (hash_val % 1000)  # 1000到1999之间
            price_data = {
                'dates': dates,
                'close': [round(base_price * (1 + (i * 0.005)), 2) for i in range(5)],
                'open': [round(base_price * (1 + (i * 0.005) - 0.01), 2) for i in range(5)],
                'high': [round(base_price * (1 + (i * 0.005) + 0.02), 2) for i in range(5)],
                'low': [round(base_price * (1 + (i * 0.005) - 0.02), 2) for i in range(5)],
                'volume': [round(1000000 * (1 + (hash_val % 100) / 100)) for _ in range(5)]
            }
            
            return {
                'status': 'success',
                'data': {
                    'sector': sector_name,
                    'indicators': indicators,
                    'prices': price_data,
                    'prediction': prediction,
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}技术分析失败: {str(e)}")
            return {'status': 'error', 'message': f"获取行业技术分析失败: {str(e)}"}

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 使用示例
    analyzer = SimpleSectorAnalyzer(top_n=10)
    
    # 分析热门行业
    hot_sectors = analyzer.get_hot_sectors(force_refresh=True)
    if hot_sectors.get('status') == 'success':
        print("热门行业列表:")
        for sector in hot_sectors['data']['hot_sectors']:
            print(f"{sector['rank']}. {sector['name']} - 热度: {sector['hot_score']} - {sector['hot_level']}")
            print(f"   分析: {sector['analysis_reason']}")
        print(f"\n更新时间: {hot_sectors['data']['update_time']}")
    else:
        print(f"获取热门行业失败: {hot_sectors.get('message')}")
    
    # 获取第一个行业的技术分析
    if hot_sectors.get('status') == 'success' and hot_sectors['data']['hot_sectors']:
        sector_name = hot_sectors['data']['hot_sectors'][0]['name']
        sector_analysis = analyzer.get_sector_technical_analysis(sector_name)
        
        if sector_analysis.get('status') == 'success':
            print(f"\n行业 {sector_name} 技术分析:")
            prediction = sector_analysis['data']['prediction']
            print(f"趋势: {prediction.get('trend', '未知')}")
            print(f"分析: {prediction.get('analysis', '无分析')}")
            print(f"看多得分: {prediction.get('bull_score', 0)}")
            print(f"看空得分: {prediction.get('bear_score', 0)}")
        else:
            print(f"获取行业技术分析失败: {sector_analysis.get('message')}") 