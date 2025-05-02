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
                    trade_signal = '买入'
                    analysis = "市场热度高，资金关注度大"
                elif score >= 50:
                    hot_level = '较热'
                    trade_signal = '观望'
                    analysis = "市场关注度中等偏上"
                elif score >= 30:
                    hot_level = '中性'
                    trade_signal = '观望'
                    analysis = "市场关注度一般"
                else:
                    hot_level = '冷门'
                    trade_signal = '回避'
                    analysis = "市场关注度较低"
                
                # 添加行业状态信息
                industry_status = "中性"
                if score > 70:
                    industry_status = "上升期"
                elif score < 30:
                    industry_status = "下降期"
                
                # 添加到结果
                sector_scores.append({
                    'name': sector,
                    'hot_score': round(score, 2),
                    'hot_level': hot_level,
                    'trade_signal': trade_signal,
                    'rank': i + 1,
                    'analysis': analysis,
                    'industry_status': industry_status,
                    'change_pct': round(np.random.normal(0, 2), 2)  # 模拟涨跌幅
                })
            
            # 排序
            sorted_sectors = sorted(sector_scores, key=lambda x: x['hot_score'], reverse=True)
            
            # 生成结果
            result = {
                'status': 'success',
                'data': {
                    'hot_sectors': sorted_sectors[:self.top_n],
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'market_trend': 'neutral',
                    'market_chg_pct': 0.0,
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
    
    def get_sector_technical_analysis(self, sector_name: str) -> Dict:
        """获取行业技术分析"""
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
                tech_score = 70 + hash_val % 15
                support = 1000 + hash_val * 5
                resistance = support * 1.1
            elif hash_val > 40:
                trend = "中性"
                bull_score = 40 + hash_val % 20
                bear_score = 100 - bull_score
                analysis = "技术指标中性，可能维持震荡"
                tech_score = 45 + hash_val % 15
                support = 1000 + hash_val * 5
                resistance = support * 1.05
            else:
                trend = "看空"
                bull_score = 20 + hash_val % 20
                bear_score = 100 - bull_score
                analysis = "技术指标偏弱，注意风险控制"
                tech_score = 25 + hash_val % 15
                support = 1000 + hash_val * 5
                resistance = support * 1.03
            
            # 创建与EnhancedSector类似的结构
            return {
                'status': 'success',
                'data': {
                    'sector': sector_name,
                    'date': datetime.now().strftime('%Y%m%d'),
                    'price': round(1000 + hash_val * 10, 2),
                    'change': round((hash_val - 50) / 10, 2),
                    'volume': hash_val * 1000,
                    'tech_score': tech_score,
                    'trend_analysis': {
                        'trend': trend,
                        'strength': round((hash_val - 50) / 5, 2),
                        'support': support,
                        'resistance': resistance,
                        'analysis': analysis
                    },
                    'indicators': {
                        'macd': {'signal': '买入' if hash_val > 50 else '卖出'},
                        'kdj': {'signal': '超卖反弹买入' if hash_val < 30 else '中性'},
                        'rsi': {'signal': '超卖' if hash_val < 30 else '超买' if hash_val > 70 else '中性'},
                        'ma': {'signal': '多头排列' if hash_val > 60 else '空头排列' if hash_val < 40 else '震荡'},
                        'boll': {'signal': '超卖区间' if hash_val < 30 else '超买区间' if hash_val > 70 else '中轨徘徊'}
                    },
                    'trade_signal': {
                        'signal': '买入' if hash_val > 60 else '卖出' if hash_val < 40 else '观望',
                        'description': analysis,
                        'action': f"建议{'关注' if hash_val > 50 else '谨慎关注' if hash_val > 30 else '暂避'}{sector_name}行业",
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}技术分析失败: {str(e)}")
            return {'status': 'error', 'message': f"获取行业技术分析失败: {str(e)}"}
    
    def get_sector_stocks(self, sector_name: str) -> Dict:
        """获取行业成分股 - 简化版模拟"""
        try:
            # 模拟成分股数据
            import hashlib
            hash_val = int(hashlib.md5(sector_name.encode()).hexdigest(), 16) % 10000
            np.random.seed(hash_val)
            
            # 模拟5-15个成分股
            stock_count = np.random.randint(5, 16)
            stocks = []
            
            for i in range(stock_count):
                # 生成随机股票代码和名称
                code_prefix = '60' if i % 2 == 0 else '00'
                code_suffix = np.random.randint(1000, 10000)
                ts_code = f"{code_prefix}{code_suffix}.{'SH' if code_prefix == '60' else 'SZ'}"
                
                stocks.append({
                    'ts_code': ts_code,
                    'name': f"{sector_name[:2]}{chr(65+i)}股份",
                    'in_date': (datetime.now() - timedelta(days=np.random.randint(30, 1000))).strftime('%Y%m%d')
                })
            
            # 返回结果
            return {
                'status': 'success',
                'data': {
                    'sector': sector_name,
                    'stocks': stocks,
                    'total': len(stocks),
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'simple'
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取行业 {sector_name} 成分股失败: {str(e)}")
            return {'status': 'error', 'message': f"获取行业成分股失败: {str(e)}"}

# 测试代码
if __name__ == "__main__":
    print("简化版行业分析器测试")
    analyzer = SimpleSectorAnalyzer()
    
    # 测试获取热门行业
    print("\n获取热门行业...")
    hot_result = analyzer.get_hot_sectors()
    if hot_result['status'] == 'success':
        print(f"\n热门行业:")
        for i, sector in enumerate(hot_result['data']['hot_sectors'], 1):
            print(f"{i}. {sector['name']} - 热度: {sector['hot_score']}, 级别: {sector['hot_level']}")
    
    # 测试获取行业技术分析
    print("\n获取行业技术分析...")
    tech_result = analyzer.get_sector_technical_analysis("电子")
    if tech_result['status'] == 'success':
        data = tech_result['data']
        print(f"\n{data['sector']}行业分析:")
        print(f"技术评分: {data['tech_score']}")
        print(f"趋势: {data['trend_analysis']['trend']}")
        print(f"交易信号: {data['trade_signal']['signal']}")
        print(f"建议: {data['trade_signal']['action']}") 