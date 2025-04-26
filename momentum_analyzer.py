import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

class SectorAnalyzer:
    """板块分析器"""
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
        
    def rank_sectors(self, sector_data: pd.DataFrame) -> List[Tuple[str, float]]:
        """对板块进行强度排名
        
        Args:
            sector_data: 包含板块指数数据的DataFrame
            
        Returns:
            按强度排序的板块列表，每个元素为(板块名称, 强度得分)元组
        """
        sector_scores = {}
        
        for sector in sector_data.columns:
            # 计算动量得分
            momentum = self._calculate_momentum(sector_data[sector])
            # 计算趋势强度
            trend_strength = self._calculate_trend_strength(sector_data[sector])
            # 计算相对强度
            relative_strength = self._calculate_relative_strength(sector_data[sector], sector_data)
            
            # 综合评分
            sector_scores[sector] = (
                momentum * 0.4 +
                trend_strength * 0.3 +
                relative_strength * 0.3
            )
        
        # 按强度降序排序
        ranked_sectors = sorted(
            sector_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return ranked_sectors
    
    def _calculate_momentum(self, prices: pd.Series) -> float:
        """计算动量得分"""
        returns = prices.pct_change(self.lookback_period)
        momentum_score = returns.mean()
        return momentum_score
    
    def _calculate_trend_strength(self, prices: pd.Series) -> float:
        """计算趋势强度
        使用价格与移动平均线的关系评估趋势强度
        """
        ma20 = prices.rolling(20).mean()
        ma60 = prices.rolling(60).mean()
        
        # 计算价格与均线关系
        above_ma20 = (prices > ma20).mean()
        above_ma60 = (prices > ma60).mean()
        ma_trend = (ma20 > ma60).mean()
        
        trend_score = (above_ma20 * 0.4 + above_ma60 * 0.3 + ma_trend * 0.3)
        return trend_score
    
    def _calculate_relative_strength(self, prices: pd.Series, sector_data: pd.DataFrame) -> float:
        """计算相对强度
        对比个别板块与整体市场的表现
        """
        market_return = sector_data.mean(axis=1).pct_change(self.lookback_period)
        sector_return = prices.pct_change(self.lookback_period)
        
        relative_strength = (sector_return - market_return).mean()
        return relative_strength

class StockAnalyzer:
    """个股分析器"""
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
        
    def find_leading_stocks(self, stock_data: pd.DataFrame, sector: str) -> List[Tuple[str, float]]:
        """识别板块内的领头羊股票
        
        Args:
            stock_data: 包含个股数据的DataFrame
            sector: 板块名称
            
        Returns:
            按强度排序的股票列表，每个元素为(股票代码, 强度得分)元组
        """
        stock_scores = {}
        
        for stock in stock_data.columns:
            # 计算个股动量
            momentum = self._calculate_momentum(stock_data[stock])
            # 计算成交量特征
            volume_factor = self._analyze_volume(stock_data[stock])
            # 计算波动率特征
            volatility_factor = self._analyze_volatility(stock_data[stock])
            
            # 综合评分
            stock_scores[stock] = (
                momentum * 0.5 +
                volume_factor * 0.3 +
                volatility_factor * 0.2
            )
        
        # 按强度降序排序
        ranked_stocks = sorted(
            stock_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return ranked_stocks
    
    def _calculate_momentum(self, data: pd.Series) -> float:
        """计算个股动量得分"""
        # 计算多个周期的收益率
        returns_5d = data.pct_change(5).mean()
        returns_10d = data.pct_change(10).mean()
        returns_20d = data.pct_change(20).mean()
        
        # 加权平均
        momentum_score = (
            returns_5d * 0.5 +
            returns_10d * 0.3 +
            returns_20d * 0.2
        )
        
        return momentum_score
    
    def _analyze_volume(self, data: pd.Series) -> float:
        """分析成交量特征"""
        # 计算近期成交量变化
        volume = data['volume'] if isinstance(data, pd.DataFrame) else data
        volume_ma5 = volume.rolling(5).mean()
        volume_ma20 = volume.rolling(20).mean()
        
        # 计算量能放大程度
        volume_ratio = (volume_ma5 / volume_ma20).mean()
        return volume_ratio
    
    def _analyze_volatility(self, data: pd.Series) -> float:
        """分析波动率特征"""
        # 计算历史波动率
        returns = data.pct_change()
        volatility = returns.std()
        
        # 将波动率转换为评分（较低波动率得分更高）
        volatility_score = 1 / (1 + volatility)
        return volatility_score