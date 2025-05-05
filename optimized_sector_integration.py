#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化版行业分析集成器
将优化版行业分析器与原系统集成
"""

import os
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

# 导入优化版行业分析器
try:
    from optimized_sector_analyzer import OptimizedSectorAnalyzer
    from tushare_sector_provider import get_sector_provider
except ImportError as e:
    print(f"导入行业分析器失败: {str(e)}")
    raise

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sector_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SectorIntegration")

class SectorIntegrator:
    """行业分析集成器"""
    
    def __init__(self, use_optimized=True, top_n=10, data_days=90):
        """初始化行业分析集成器
        
        Args:
            use_optimized: 是否优先使用优化版行业分析器
            top_n: 返回的热门行业数
            data_days: 历史数据天数
        """
        self.use_optimized = use_optimized
        self.top_n = top_n
        self.data_days = data_days
        
        # 初始化数据提供器与分析器
        self.provider = get_sector_provider()
        
        # 初始化优化版分析器
        try:
            self.optimized_analyzer = OptimizedSectorAnalyzer(
                top_n=self.top_n,
                data_days=self.data_days,
                provider=self.provider
            )
            logger.info("优化版行业分析器初始化成功")
        except Exception as e:
            self.optimized_analyzer = None
            logger.error(f"优化版行业分析器初始化失败: {str(e)}")
        
        # 不再尝试初始化原版分析器
        self.original_analyzer = None
    
    def get_hot_sectors(self) -> Dict:
        """获取热门行业
        
        Returns:
            Dict: 热门行业分析结果
        """
        # 使用优化版分析器
        if self.optimized_analyzer:
            try:
                logger.info("使用优化版行业分析器获取热门行业")
                result = self.optimized_analyzer.analyze_hot_sectors()
                
                if result['status'] == 'success' and result['data']['hot_sectors']:
                    # 标记数据来源
                    result['data']['source'] = 'optimized'
                    logger.info(f"优化版分析成功，找到 {len(result['data']['hot_sectors'])} 个热门行业")
                    return result
                else:
                    logger.warning("优化版分析器返回空结果")
            except Exception as e:
                logger.error(f"优化版分析器出错: {str(e)}")
                logger.debug(traceback.format_exc())
                
        # 所有分析器都失败，返回错误结果
        return {
            'status': 'error',
            'message': '行业分析器失败',
            'data': {
                'hot_sectors': [],
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    def predict_hot_sectors(self) -> Dict:
        """预测未来热门行业
        
        Returns:
            Dict: 行业预测结果
        """
        # 首先获取当前热门行业
        hot_sectors = self.get_hot_sectors()
        
        # 如果获取热门行业失败，直接返回错误
        if hot_sectors['status'] != 'success':
            return {
                'status': 'error',
                'message': '获取当前热门行业失败，无法进行预测',
                'data': {
                    'predicted_sectors': [],
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        
        # 简化预测逻辑：维持热门行业排序，添加预测信息
        predicted_sectors = []
        
        for sector in hot_sectors['data']['hot_sectors']:
            # 提取关键指标
            name = sector['name']
            hot_score = sector['hot_score']
            trend_score = sector.get('trend_score', 50)
            
            # 根据技术指标调整预测得分
            prediction_adjustment = 0
            
            # 考虑MACD指标
            macd = sector.get('macd', 0)
            if macd > 0:
                prediction_adjustment += 5  # MACD为正，上涨概率增加
            else:
                prediction_adjustment -= 5  # MACD为负，下跌概率增加
            
            # 考虑RSI指标
            rsi = sector.get('rsi', 50)
            if rsi > 70:  # 超买
                prediction_adjustment -= 10
            elif rsi < 30:  # 超卖
                prediction_adjustment += 10
            
            # 考虑均线排列
            ma_trend_up = sector.get('ma_trend_up', False)
            if ma_trend_up:
                prediction_adjustment += 5
            
            # 计算最终预测得分
            prediction_score = hot_score + prediction_adjustment
            prediction_score = max(0, min(100, prediction_score))  # 确保在0-100范围内
            
            # 生成预测理由
            if prediction_score > hot_score + 5:
                reason = f"{name}行业有望走强，技术指标向好"
                if macd > 0:
                    reason += "，MACD金叉向上"
                if rsi < 40:
                    reason += "，RSI处于低位有反弹空间"
                if ma_trend_up:
                    reason += "，均线呈多头排列"
            elif prediction_score < hot_score - 5:
                reason = f"{name}行业可能走弱，技术指标转差"
                if macd < 0:
                    reason += "，MACD死叉向下"
                if rsi > 60:
                    reason += "，RSI处于高位面临回调压力"
                if not ma_trend_up:
                    reason += "，均线排列不佳"
            else:
                reason = f"{name}行业预计维持当前走势，无明显转向信号"
            
            # 加入预测结果
            predicted_sectors.append({
                'name': name,
                'code': sector.get('code', ''),
                'type': sector.get('type', 'UNKNOWN'),
                'current_hot_score': hot_score,
                'prediction_score': round(prediction_score, 2),
                'prediction_change': round(prediction_score - hot_score, 2),
                'reason': reason,
                'trading_signals': sector.get('trading_signals', {})
            })
        
        # 按预测得分排序
        predicted_sectors.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        return {
            'status': 'success',
            'data': {
                'predicted_sectors': predicted_sectors[:self.top_n],
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': hot_sectors['data'].get('source', 'unknown')
            }
        }
    
    def get_sector_data(self, sector_name: str) -> Dict:
        """获取特定行业的历史数据
        
        Args:
            sector_name: 行业名称
            
        Returns:
            Dict: 行业历史数据
        """
        # 获取行业列表
        sectors = self.provider.get_sector_list()
        
        # 查找匹配的行业
        sector_code = None
        for sector in sectors:
            if sector['name'] == sector_name:
                sector_code = sector['code']
                break
        
        if not sector_code:
            return {
                'status': 'error',
                'message': f'未找到行业: {sector_name}',
                'data': None
            }
        
        # 获取行业历史数据
        hist_data = self.provider.get_sector_history(sector_code, days=self.data_days)
        
        if hist_data is None or hist_data.empty:
            return {
                'status': 'error',
                'message': f'无法获取行业 {sector_name} 的历史数据',
                'data': None
            }
        
        return {
            'status': 'success',
            'data': hist_data
        }
    
    def get_available_sectors(self) -> List[str]:
        """获取系统支持的所有行业名称
        
        Returns:
            List[str]: 行业名称列表
        """
        sectors = self.provider.get_sector_list()
        return [sector['name'] for sector in sectors]

# 单例模式提供全局访问点
_integrator = None

def get_sector_integrator(use_optimized=True, top_n=10, data_days=90):
    """获取行业分析集成器单例
    
    Args:
        use_optimized: 是否优先使用优化版分析器
        top_n: 热门行业数量
        data_days: 历史数据天数
        
    Returns:
        SectorIntegrator: 行业分析集成器实例
    """
    global _integrator
    if _integrator is None:
        _integrator = SectorIntegrator(use_optimized, top_n, data_days)
    return _integrator

if __name__ == "__main__":
    # 运行测试
    print("\n====== 行业分析集成器测试 ======\n")
    
    # 创建集成器
    integrator = get_sector_integrator(use_optimized=True, top_n=5)
    
    # 获取热门行业
    print("获取热门行业:")
    hot_result = integrator.get_hot_sectors()
    
    if hot_result['status'] == 'success':
        print(f"分析成功 (来源: {hot_result['data'].get('source', 'unknown')})")
        print("热门行业排名:")
        
        for i, sector in enumerate(hot_result['data']['hot_sectors']):
            print(f"{i+1}. {sector['name']} (热度: {sector.get('hot_score', 'N/A')})")
            print(f"   - 分析: {sector.get('analysis_reason', 'N/A')}")
            
            # 打印交易信号
            signals = sector.get('trading_signals', {})
            if signals and 'buy_signals' in signals and signals['buy_signals']:
                print(f"   - 买入信号: {', '.join(signals['buy_signals'])}")
            if signals and 'sell_signals' in signals and signals['sell_signals']:
                print(f"   - 卖出信号: {', '.join(signals['sell_signals'])}")
    else:
        print(f"分析失败: {hot_result.get('message', '未知错误')}")
    
    # 测试行业预测
    print("\n预测热门行业:")
    predict_result = integrator.predict_hot_sectors()
    
    if predict_result['status'] == 'success':
        print(f"预测成功 (来源: {predict_result['data'].get('source', 'unknown')})")
        print("预测行业排名:")
        
        for i, sector in enumerate(predict_result['data']['predicted_sectors']):
            print(f"{i+1}. {sector['name']} (预测得分: {sector['prediction_score']})")
            print(f"   - 变化: {sector['prediction_change']:+.2f}")
            print(f"   - 理由: {sector['reason']}")
    else:
        print(f"预测失败: {predict_result.get('message', '未知错误')}")
    
    # 测试获取可用行业
    print("\n获取所有可用行业:")
    available_sectors = integrator.get_available_sectors()
    print(f"共有 {len(available_sectors)} 个可用行业")
    print(f"前10个行业: {', '.join(available_sectors[:10])}")
    
    print("\n====== 测试完成 ======\n") 