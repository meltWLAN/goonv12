#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化版行业分析器
支持多数据源（Tushare, AKShare等）
"""

import os
import sys
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import threading
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sector_analyzer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("OptimizedSectorAnalyzer")

class OptimizedSectorAnalyzer:
    """优化版行业分析器，支持多数据源"""
    
    def __init__(self, top_n=10, provider=None, provider_type='auto', tushare_token=None):
        """初始化优化版行业分析器
        
        Args:
            top_n: 返回的热门行业数量
            provider: 行业数据提供器实例，如果为None则自动创建
            provider_type: 提供器类型 ('tushare', 'akshare', 'auto')
            tushare_token: Tushare API Token
        """
        self.top_n = top_n
        self._last_update = 0
        self.is_analyzing = False
        self.analysis_lock = threading.Lock()
        
        # 初始化数据提供器
        if provider is not None:
            self.provider = provider
            logger.info(f"使用外部提供的行业数据提供器: {provider.__class__.__name__}")
        else:
            # 使用行业数据提供器工厂获取提供器
            try:
                from sector_provider_factory import get_provider
                self.provider = get_provider(provider_type, tushare_token)
                
                if self.provider is None:
                    logger.error("无法初始化行业数据提供器")
                    raise ValueError("无法初始化行业数据提供器")
                    
                logger.info(f"使用行业数据提供器: {self.provider.__class__.__name__}")
            except ImportError:
                logger.error("无法导入sector_provider_factory模块")
                raise ImportError("无法导入sector_provider_factory模块")
    
    def analyze_hot_sectors(self, days=90, min_days=30) -> Dict:
        """分析热门行业
        
        Args:
            days: 分析的历史天数
            min_days: 最小有效数据天数
            
        Returns:
            分析结果 {'timestamp': 时间戳, 'data': {'sectors': 行业列表, 'market_info': 市场信息}}
        """
        start_time = time.time()
        
        # 使用锁防止并发分析
        if self.analysis_lock.acquire(False):
            try:
                self.is_analyzing = True
                logger.info(f"开始分析热门行业，历史天数: {days}")
                
                # 检查缓存是否过期
                if time.time() - self._last_update < 3600:  # 缓存1小时
                    logger.info("使用缓存的热门行业分析结果")
                    self.is_analyzing = False
                    self.analysis_lock.release()
                    return self._cached_result
                
                # 获取行业列表
                sectors = self.provider.get_sector_list()
                if not sectors:
                    logger.error("获取行业列表失败")
                    self.is_analyzing = False
                    self.analysis_lock.release()
                    return {'error': '获取行业列表失败'}
                
                logger.info(f"获取到 {len(sectors)} 个行业")
                
                # 分析各行业
                sectors_analyzed = []
                
                # 申万行业板块，使用优先级更高
                sw_sectors = [s for s in sectors if s['type'] == 'SW']
                cn_sectors = [s for s in sectors if s['type'] == 'CN']
                
                # 合并处理，优先处理申万行业
                all_sectors = sw_sectors + cn_sectors
                
                for sector in all_sectors:
                    try:
                        logger.debug(f"分析行业: {sector['name']} ({sector['code']})")
                        
                        # 获取行业历史数据
                        hist_data = self.provider.get_sector_history(sector['code'], days=days)
                        
                        if hist_data is None or hist_data.empty:
                            logger.warning(f"行业 {sector['name']} 无历史数据，跳过")
                            continue
                            
                        # 检查数据量是否足够
                        if len(hist_data) < min_days:
                            logger.warning(f"行业 {sector['name']} 历史数据不足 {min_days} 天，跳过")
                            continue
                        
                        # 计算行业指标
                        sector_metrics = self._calculate_sector_metrics(hist_data, sector)
                        
                        if sector_metrics:
                            sectors_analyzed.append(sector_metrics)
                    except Exception as e:
                        logger.error(f"分析行业 {sector['name']} 出错: {str(e)}")
                        logger.debug(traceback.format_exc())
                
                # 排序并选出热门行业
                if not sectors_analyzed:
                    logger.error("没有行业满足分析条件")
                    self.is_analyzing = False
                    self.analysis_lock.release()
                    return {'error': '没有行业满足分析条件'}
                
                # 按热度排序（综合评分）
                sectors_analyzed.sort(key=lambda x: x['score'], reverse=True)
                
                # 构造结果
                hot_sectors = sectors_analyzed[:self.top_n]
                
                # 计算市场整体情况
                market_info = self._calculate_market_info(sectors_analyzed)
                
                result = {
                    'timestamp': time.time(),
                    'data': {
                        'sectors': hot_sectors,
                        'market_info': market_info
                    }
                }
                
                # 缓存结果
                self._cached_result = result
                self._last_update = time.time()
                
                end_time = time.time()
                logger.info(f"热门行业分析完成，耗时: {end_time - start_time:.2f}秒，共 {len(hot_sectors)} 个热门行业")
                
                self.is_analyzing = False
                self.analysis_lock.release()
                return result
            except Exception as e:
                logger.error(f"分析热门行业出错: {str(e)}")
                logger.debug(traceback.format_exc())
                self.is_analyzing = False
                self.analysis_lock.release()
                return {'error': f'分析出错: {str(e)}'}
        else:
            logger.warning("已有分析任务正在运行，请稍后再试")
            return {'error': '已有分析任务正在运行，请稍后再试'}
    
    def _calculate_sector_metrics(self, hist_data: pd.DataFrame, sector_info: Dict) -> Dict:
        """计算行业指标
        
        Args:
            hist_data: 行业历史数据
            sector_info: 行业基本信息
            
        Returns:
            行业指标 Dict
        """
        try:
            # 检查必要的列是否存在
            required_cols = ['开盘', '收盘', '最高', '最低']
            if not all(col in hist_data.columns for col in required_cols):
                logger.warning(f"行业 {sector_info['name']} 历史数据缺少必要列")
                available_cols = hist_data.columns.tolist()
                logger.debug(f"可用列: {available_cols}")
                return None
            
            # 数据按日期降序排序（最近的数据在前面）
            data = hist_data.sort_index(ascending=False)
            
            # 计算基本指标
            last_close = data['收盘'].iloc[0]
            last_date = data.index[0].strftime('%Y-%m-%d')
            
            # 计算N日涨幅
            days_back = min(90, len(data) - 1)
            if days_back > 0:
                prev_close = data['收盘'].iloc[days_back]
                change_rate_90d = (last_close / prev_close - 1) * 100
            else:
                change_rate_90d = 0
            
            # 计算20日涨幅
            days_back = min(20, len(data) - 1)
            if days_back > 0:
                prev_close = data['收盘'].iloc[days_back]
                change_rate_20d = (last_close / prev_close - 1) * 100
            else:
                change_rate_20d = 0
            
            # 计算5日涨幅
            days_back = min(5, len(data) - 1)
            if days_back > 0:
                prev_close = data['收盘'].iloc[days_back]
                change_rate_5d = (last_close / prev_close - 1) * 100
            else:
                change_rate_5d = 0
            
            # 计算1日涨幅
            days_back = min(1, len(data) - 1)
            if days_back > 0:
                prev_close = data['收盘'].iloc[days_back]
                change_rate_1d = (last_close / prev_close - 1) * 100
            else:
                change_rate_1d = 0
            
            # 计算波动率
            if len(data) > 5:
                returns = np.log(data['收盘'] / data['收盘'].shift(1))
                volatility = returns.std() * np.sqrt(250) * 100  # 年化波动率
            else:
                volatility = 0
            
            # 计算趋势强度（使用10日和30日均线差值的比例）
            trend_strength = 0
            try:
                if len(data) >= 30:
                    ma10 = data['收盘'].rolling(10).mean()
                    ma30 = data['收盘'].rolling(30).mean()
                    
                    # 确保数据不是NaN
                    if not np.isnan(ma10.iloc[0]) and not np.isnan(ma30.iloc[0]) and ma30.iloc[0] != 0:
                        trend_strength = (ma10.iloc[0] / ma30.iloc[0] - 1) * 100
                    else:
                        logger.warning(f"行业 {sector_info['name']} 计算趋势强度时出现NaN，使用默认值0")
                else:
                    logger.debug(f"行业 {sector_info['name']} 数据不足30天，无法计算趋势强度")
            except Exception as e:
                logger.warning(f"计算行业 {sector_info['name']} 趋势强度出错: {str(e)}")
            
            # 计算综合评分
            # 权重：短期涨幅40%，中期涨幅30%，长期涨幅20%，趋势强度10%
            try:
                score = (
                    change_rate_5d * 0.2 +
                    change_rate_20d * 0.3 +
                    change_rate_90d * 0.2 +
                    trend_strength * 0.3
                )
                # 检查是否为NaN
                if np.isnan(score):
                    logger.warning(f"行业 {sector_info['name']} 评分计算结果为NaN，使用涨幅作为替代")
                    # 如果评分为NaN，使用涨幅作为替代
                    score = change_rate_5d * 0.3 + change_rate_20d * 0.7
                    
                    # 如果仍然为NaN，使用固定值
                    if np.isnan(score):
                        score = 0
            except Exception as e:
                logger.warning(f"计算行业 {sector_info['name']} 综合评分出错: {str(e)}")
                score = 0
            
            # 添加行业基本信息
            result = {
                'code': sector_info['code'],
                'name': sector_info['name'],
                'type': sector_info['type'],
                'description': sector_info.get('description', f"{sector_info['type']}-{sector_info['name']}"),
                'last_close': last_close,
                'last_date': last_date,
                'change_rate_1d': round(change_rate_1d, 2),
                'change_rate_5d': round(change_rate_5d, 2),
                'change_rate_20d': round(change_rate_20d, 2),
                'change_rate_90d': round(change_rate_90d, 2),
                'volatility': round(volatility, 2),
                'trend_strength': round(trend_strength, 2),
                'score': round(score, 2),
                'data_source': data.get('数据来源', ['unknown']).iloc[0] if '数据来源' in data.columns else 'unknown',
                'is_real_data': data.get('是真实数据', [True]).iloc[0] if '是真实数据' in data.columns else True
            }
            
            return result
        except Exception as e:
            logger.error(f"计算行业 {sector_info['name']} 指标出错: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def _calculate_market_info(self, sectors):
        """计算市场整体情况
        
        Args:
            sectors: 行业列表（已计算指标）
            
        Returns:
            市场整体情况
        """
        try:
            if not sectors:
                return {
                    'market_sentiment': 0,
                    'north_flow': 0,
                    'volatility': 0,
                    'shanghai_change_pct': 0,
                    'shenzhen_change_pct': 0,
                    'market_avg_change': 0
                }
            
            # 计算平均值
            avg_1d_change = sum(s['change_rate_1d'] for s in sectors) / len(sectors)
            avg_5d_change = sum(s['change_rate_5d'] for s in sectors) / len(sectors)
            avg_20d_change = sum(s['change_rate_20d'] for s in sectors) / len(sectors)
            avg_volatility = sum(s['volatility'] for s in sectors) / len(sectors)
            
            # 计算市场情绪（基于短期和中期涨幅的加权平均）
            market_sentiment = avg_1d_change * 0.3 + avg_5d_change * 0.4 + avg_20d_change * 0.3
            
            # 获取沪深指数数据
            try:
                shanghai_idx = None
                shenzhen_idx = None
                
                # 尝试从行业数据提供器获取上证指数数据
                try:
                    shanghai_idx = self.provider.get_sector_history('000001.SH', days=5)
                except:
                    logger.warning("无法从行业数据提供器获取上证指数数据")
                
                # 尝试从行业数据提供器获取深证成指数据
                try:
                    shenzhen_idx = self.provider.get_sector_history('399001.SZ', days=5)
                except:
                    logger.warning("无法从行业数据提供器获取深证成指数据")
                
                # 计算上证指数涨跌幅
                shanghai_change_pct = 0
                if shanghai_idx is not None and not shanghai_idx.empty and '收盘' in shanghai_idx.columns:
                    shanghai_idx = shanghai_idx.sort_index(ascending=False)
                    last_close = shanghai_idx['收盘'].iloc[0]
                    prev_close = shanghai_idx['收盘'].iloc[min(1, len(shanghai_idx)-1)]
                    shanghai_change_pct = (last_close / prev_close - 1) * 100
                
                # 计算深证成指涨跌幅
                shenzhen_change_pct = 0
                if shenzhen_idx is not None and not shenzhen_idx.empty and '收盘' in shenzhen_idx.columns:
                    shenzhen_idx = shenzhen_idx.sort_index(ascending=False)
                    last_close = shenzhen_idx['收盘'].iloc[0]
                    prev_close = shenzhen_idx['收盘'].iloc[min(1, len(shenzhen_idx)-1)]
                    shenzhen_change_pct = (last_close / prev_close - 1) * 100
            except Exception as e:
                logger.error(f"获取沪深指数数据出错: {str(e)}")
                shanghai_change_pct = 0
                shenzhen_change_pct = 0
            
            # 构造市场信息
            market_info = {
                'market_sentiment': round(market_sentiment, 2),
                'north_flow': 0,  # 这个数据无法从行业分析获得，需要额外的数据源
                'volatility': round(avg_volatility, 2),
                'shanghai_change_pct': round(shanghai_change_pct, 2),
                'shenzhen_change_pct': round(shenzhen_change_pct, 2),
                'market_avg_change': round(avg_1d_change, 2)
            }
            
            return market_info
        except Exception as e:
            logger.error(f"计算市场整体情况出错: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # 返回默认值
            return {
                'market_sentiment': 0,
                'north_flow': 0,
                'volatility': 0,
                'shanghai_change_pct': 0,
                'shenzhen_change_pct': 0,
                'market_avg_change': 0
            }
    
    def predict_hot_sectors(self) -> Dict:
        """预测未来热门行业
        
        Returns:
            预测结果 {'timestamp': 时间戳, 'data': {'predicted_sectors': 预测行业列表}}
        """
        try:
            logger.info("开始预测未来热门行业")
            
            # 先分析当前热门行业
            result = self.analyze_hot_sectors()
            
            if 'error' in result:
                logger.error(f"分析热门行业失败: {result['error']}")
                return {'error': f"分析热门行业失败: {result['error']}"}
            
            # 获取当前热门行业
            current_hot_sectors = result['data']['sectors']
            
            # 基于当前热门行业和趋势强度预测
            predicted_sectors = []
            
            for sector in current_hot_sectors:
                # 复制当前行业数据
                predicted = sector.copy()
                
                # 基于趋势强度和近期涨幅预测
                trend_factor = predicted['trend_strength'] * 0.1
                
                # 预测未来5日涨跌幅
                predicted_5d_change = predicted['change_rate_5d'] * 0.3 + trend_factor
                
                # 预测未来20日涨跌幅
                predicted_20d_change = predicted['change_rate_20d'] * 0.2 + trend_factor
                
                # 增加预测数据
                predicted['predicted_5d_change'] = round(predicted_5d_change, 2)
                predicted['predicted_20d_change'] = round(predicted_20d_change, 2)
                predicted['prediction_confidence'] = round(50 + min(50, abs(predicted['trend_strength'])), 2)
                
                predicted_sectors.append(predicted)
            
            # 按预测20日涨幅排序
            predicted_sectors.sort(key=lambda x: x['predicted_20d_change'], reverse=True)
            
            # 构造结果
            prediction_result = {
                'timestamp': time.time(),
                'data': {
                    'predicted_sectors': predicted_sectors[:self.top_n]
                }
            }
            
            logger.info(f"热门行业预测完成，共 {len(predicted_sectors[:self.top_n])} 个预测行业")
            return prediction_result
        except Exception as e:
            logger.error(f"预测热门行业出错: {str(e)}")
            logger.debug(traceback.format_exc())
            return {'error': f'预测出错: {str(e)}'}
    
    def clear_cache(self):
        """清除缓存"""
        self._last_update = 0
        if hasattr(self, '_cached_result'):
            delattr(self, '_cached_result')
        
        # 清除提供器缓存
        if hasattr(self.provider, 'clear_cache'):
            self.provider.clear_cache()
        
        logger.info("已清除所有缓存")

if __name__ == "__main__":
    # 简单测试
    analyzer = OptimizedSectorAnalyzer(top_n=10, provider_type='auto')
    
    # 分析热门行业
    print("\n分析热门行业:")
    result = analyzer.analyze_hot_sectors()
    
    if 'error' in result:
        print(f"分析出错: {result['error']}")
    else:
        hot_sectors = result['data']['sectors']
        print(f"热门行业 TOP {len(hot_sectors)}:")
        for i, sector in enumerate(hot_sectors):
            print(f"{i+1}. {sector['name']} ({sector['code']}) - 得分:{sector['score']} - 5日涨幅:{sector['change_rate_5d']}% - 20日涨幅:{sector['change_rate_20d']}% - 趋势强度:{sector['trend_strength']}")
        
        # 输出市场信息
        market_info = result['data']['market_info']
        print("\n市场整体情况:")
        print(f"市场情绪: {market_info['market_sentiment']}")
        print(f"平均波动率: {market_info['volatility']}%")
        print(f"上证指数涨跌幅: {market_info['shanghai_change_pct']}%")
        print(f"深证成指涨跌幅: {market_info['shenzhen_change_pct']}%")
    
    # 预测未来热门行业
    print("\n预测未来热门行业:")
    prediction = analyzer.predict_hot_sectors()
    
    if 'error' in prediction:
        print(f"预测出错: {prediction['error']}")
    else:
        predicted_sectors = prediction['data']['predicted_sectors']
        print(f"预测热门行业 TOP {len(predicted_sectors)}:")
        for i, sector in enumerate(predicted_sectors):
            print(f"{i+1}. {sector['name']} ({sector['code']}) - 预测5日涨幅:{sector['predicted_5d_change']}% - 预测20日涨幅:{sector['predicted_20d_change']}% - 置信度:{sector['prediction_confidence']}%") 