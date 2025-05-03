#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能股票推荐管理系统
用于自动收录和管理强烈推荐的股票，提供智能买入卖出建议
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='smart_recommendation.log'
)
logger = logging.getLogger('SmartRecommendation')

class StockRecommendation:
    """单个股票推荐信息"""
    
    def __init__(self, 
                 stock_code: str,
                 stock_name: str,
                 recommendation_date: datetime,
                 entry_price: float,
                 target_price: float,
                 stop_loss: float,
                 reason: str,
                 source: str,
                 score: float = 0,
                 tags: List[str] = None,
                 status: str = "active",
                 actual_entry: Optional[Dict] = None,
                 actual_exit: Optional[Dict] = None,
                 technical_indicators: Optional[Dict] = None,
                 performance_metrics: Optional[Dict] = None):
        """初始化股票推荐
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            recommendation_date: 推荐日期
            entry_price: 建议买入价格
            target_price: 目标价格
            stop_loss: 止损价格
            reason: 推荐理由
            source: 推荐来源（技术分析/基本面/AI预测等）
            score: 推荐强度评分(0-100)
            tags: 相关标签(行业、主题等)
            status: 状态(active/completed/canceled)
            actual_entry: 实际买入信息
            actual_exit: 实际卖出信息
            technical_indicators: 相关技术指标
            performance_metrics: 业绩指标
        """
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.recommendation_date = recommendation_date
        self.entry_price = entry_price
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.reason = reason
        self.source = source
        self.score = score
        self.tags = tags or []
        self.status = status
        self.actual_entry = actual_entry or {}
        self.actual_exit = actual_exit or {}
        self.technical_indicators = technical_indicators or {}
        self.performance_metrics = performance_metrics or {}
        self.last_update = datetime.now()
        
        # 计算收益比(Risk Reward Ratio)
        if entry_price > 0 and stop_loss > 0:
            self.risk = abs(entry_price - stop_loss) / entry_price * 100
            self.reward = abs(target_price - entry_price) / entry_price * 100
            self.risk_reward_ratio = self.reward / self.risk if self.risk > 0 else 0
        else:
            self.risk = 0
            self.reward = 0
            self.risk_reward_ratio = 0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'recommendation_date': self.recommendation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'reason': self.reason,
            'source': self.source,
            'score': self.score,
            'tags': self.tags,
            'status': self.status,
            'actual_entry': self.actual_entry,
            'actual_exit': self.actual_exit,
            'technical_indicators': self.technical_indicators,
            'performance_metrics': self.performance_metrics,
            'risk': self.risk,
            'reward': self.reward,
            'risk_reward_ratio': self.risk_reward_ratio,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StockRecommendation':
        """从字典创建推荐对象"""
        recommendation_date = datetime.strptime(data['recommendation_date'], '%Y-%m-%d %H:%M:%S')
        
        return cls(
            stock_code=data['stock_code'],
            stock_name=data['stock_name'],
            recommendation_date=recommendation_date,
            entry_price=data['entry_price'],
            target_price=data['target_price'],
            stop_loss=data['stop_loss'],
            reason=data['reason'],
            source=data['source'],
            score=data.get('score', 0),
            tags=data.get('tags', []),
            status=data.get('status', 'active'),
            actual_entry=data.get('actual_entry', {}),
            actual_exit=data.get('actual_exit', {}),
            technical_indicators=data.get('technical_indicators', {}),
            performance_metrics=data.get('performance_metrics', {})
        )
    
    def update_price(self, current_price: float) -> None:
        """更新当前价格，更新状态和表现"""
        # 如果已经结束，不再更新
        if self.status == 'completed' or self.status == 'canceled':
            return
        
        # 计算距离推荐的天数
        days_since_recommendation = (datetime.now() - self.recommendation_date).days
        
        # 计算当前收益率
        if self.actual_entry and self.actual_entry.get('price', 0) > 0:
            entry_price = self.actual_entry.get('price')
            current_return = (current_price - entry_price) / entry_price * 100
        else:
            entry_price = self.entry_price
            current_return = (current_price - entry_price) / entry_price * 100
        
        # 更新表现指标
        self.performance_metrics['current_price'] = current_price
        self.performance_metrics['current_return'] = current_return
        self.performance_metrics['days_held'] = days_since_recommendation
        
        # 检查是否达到目标价格
        if current_price >= self.target_price:
            self.performance_metrics['target_reached'] = True
            self.performance_metrics['target_reached_date'] = datetime.now().strftime('%Y-%m-%d')
            
        # 检查是否触发止损
        if current_price <= self.stop_loss:
            self.performance_metrics['stop_loss_triggered'] = True
            self.performance_metrics['stop_loss_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # 更新最后更新时间
        self.last_update = datetime.now()

class SmartRecommendationSystem:
    """智能股票推荐管理系统"""
    
    def __init__(self, data_path: str = "smart_recommendation_data"):
        """初始化推荐系统
        
        Args:
            data_path: 数据存储路径
        """
        self.data_path = data_path
        self.recommendations = {}  # 股票代码 -> StockRecommendation
        self.recommendation_history = []  # 历史推荐记录
        
        # 确保数据目录存在
        os.makedirs(data_path, exist_ok=True)
        
        # 加载保存的推荐
        self._load_recommendations()
        
        logger.info(f"智能推荐系统初始化完成，加载了 {len(self.recommendations)} 个推荐")
    
    def _load_recommendations(self) -> None:
        """从文件加载推荐"""
        recommendations_file = os.path.join(self.data_path, "recommendations.json")
        
        if os.path.exists(recommendations_file):
            try:
                with open(recommendations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载当前推荐
                for stock_code, rec_data in data.get('current', {}).items():
                    self.recommendations[stock_code] = StockRecommendation.from_dict(rec_data)
                
                # 加载历史推荐
                self.recommendation_history = data.get('history', [])
                
                logger.info(f"成功加载 {len(self.recommendations)} 个推荐和 {len(self.recommendation_history)} 条历史记录")
            
            except Exception as e:
                logger.error(f"加载推荐时出错: {str(e)}")
    
    def _save_recommendations(self) -> None:
        """保存推荐到文件"""
        recommendations_file = os.path.join(self.data_path, "recommendations.json")
        
        try:
            # 准备保存的数据
            data = {
                'current': {code: rec.to_dict() for code, rec in self.recommendations.items()},
                'history': self.recommendation_history,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 保存到文件
            with open(recommendations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"成功保存 {len(self.recommendations)} 个推荐和 {len(self.recommendation_history)} 条历史记录")
        
        except Exception as e:
            logger.error(f"保存推荐时出错: {str(e)}")
    
    def add_recommendation(self, recommendation: StockRecommendation) -> bool:
        """添加新的推荐
        
        Args:
            recommendation: 推荐对象
            
        Returns:
            添加是否成功
        """
        stock_code = recommendation.stock_code
        
        # 检查是否已存在
        if stock_code in self.recommendations:
            existing_rec = self.recommendations[stock_code]
            
            # 如果新推荐评分更高，则更新
            if recommendation.score > existing_rec.score:
                logger.info(f"更新推荐: {stock_code} - {recommendation.stock_name}, 新评分: {recommendation.score}")
                self.recommendations[stock_code] = recommendation
                self._save_recommendations()
                return True
            else:
                logger.info(f"保留现有推荐: {stock_code}, 现有评分 {existing_rec.score} > 新评分 {recommendation.score}")
                return False
        
        # 添加新推荐
        logger.info(f"添加新推荐: {stock_code} - {recommendation.stock_name}, 评分: {recommendation.score}")
        self.recommendations[stock_code] = recommendation
        self._save_recommendations()
        return True
    
    def update_recommendation(self, stock_code: str, updates: Dict) -> bool:
        """更新现有推荐
        
        Args:
            stock_code: 股票代码
            updates: 要更新的字段
            
        Returns:
            更新是否成功
        """
        if stock_code not in self.recommendations:
            logger.warning(f"找不到推荐: {stock_code}")
            return False
        
        recommendation = self.recommendations[stock_code]
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(recommendation, key):
                setattr(recommendation, key, value)
        
        # 更新最后更新时间
        recommendation.last_update = datetime.now()
        
        logger.info(f"更新推荐: {stock_code} - {recommendation.stock_name}")
        self._save_recommendations()
        return True
    
    def remove_recommendation(self, stock_code: str, reason: str = "手动删除") -> bool:
        """删除推荐
        
        Args:
            stock_code: 股票代码
            reason: 删除原因
            
        Returns:
            删除是否成功
        """
        if stock_code not in self.recommendations:
            logger.warning(f"找不到推荐: {stock_code}")
            return False
        
        # 获取推荐信息
        recommendation = self.recommendations[stock_code]
        
        # 添加到历史记录
        history_entry = recommendation.to_dict()
        history_entry['removal_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        history_entry['removal_reason'] = reason
        self.recommendation_history.append(history_entry)
        
        # 删除推荐
        del self.recommendations[stock_code]
        
        logger.info(f"删除推荐: {stock_code} - {recommendation.stock_name}, 原因: {reason}")
        self._save_recommendations()
        return True
    
    def get_recommendation(self, stock_code: str) -> Optional[StockRecommendation]:
        """获取指定股票的推荐
        
        Args:
            stock_code: 股票代码
            
        Returns:
            推荐对象，如果不存在则返回None
        """
        return self.recommendations.get(stock_code)
    
    def get_all_recommendations(self) -> Dict[str, StockRecommendation]:
        """获取所有推荐
        
        Returns:
            所有推荐的字典
        """
        return self.recommendations
    
    def get_top_recommendations(self, limit: int = 10) -> List[StockRecommendation]:
        """获取评分最高的推荐
        
        Args:
            limit: 返回的推荐数量
            
        Returns:
            评分最高的推荐列表
        """
        # 按评分降序排序
        sorted_recommendations = sorted(
            self.recommendations.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_recommendations[:limit]
    
    def get_recommendations_by_tag(self, tag: str) -> List[StockRecommendation]:
        """获取包含指定标签的推荐
        
        Args:
            tag: 标签
            
        Returns:
            包含指定标签的推荐列表
        """
        return [
            rec for rec in self.recommendations.values()
            if tag in rec.tags
        ]
    
    def update_prices(self, price_data: Dict[str, float]) -> None:
        """批量更新当前价格
        
        Args:
            price_data: 股票代码 -> 价格 的字典
        """
        updated_count = 0
        
        for stock_code, price in price_data.items():
            if stock_code in self.recommendations:
                self.recommendations[stock_code].update_price(price)
                updated_count += 1
        
        if updated_count > 0:
            logger.info(f"更新了 {updated_count} 个推荐的价格")
            self._save_recommendations()
    
    def clean_recommendations(self, days_threshold: int = 30) -> int:
        """清理过期的推荐
        
        Args:
            days_threshold: 天数阈值，超过这个天数的推荐将被清理
            
        Returns:
            清理的推荐数量
        """
        now = datetime.now()
        to_remove = []
        
        for stock_code, recommendation in self.recommendations.items():
            # 计算推荐的天数
            days_since_recommendation = (now - recommendation.recommendation_date).days
            
            # 如果超过阈值，标记为删除
            if days_since_recommendation > days_threshold:
                to_remove.append(stock_code)
        
        # 删除过期推荐
        for stock_code in to_remove:
            self.remove_recommendation(stock_code, reason=f"超过{days_threshold}天未达目标")
        
        logger.info(f"清理了 {len(to_remove)} 个过期推荐")
        return len(to_remove)
    
    def get_performance_stats(self) -> Dict:
        """获取推荐系统的表现统计
        
        Returns:
            表现统计字典
        """
        if not self.recommendations:
            return {
                'total_active_recommendations': 0,
                'total_historical_recommendations': 0,
                'avg_score': 0,
                'avg_return': 0,
                'success_rate': 0
            }
        
        # 统计当前推荐
        total_recs = len(self.recommendations)
        avg_score = sum(rec.score for rec in self.recommendations.values()) / total_recs
        
        # 计算平均收益率
        returns = []
        for rec in self.recommendations.values():
            if 'current_return' in rec.performance_metrics:
                returns.append(rec.performance_metrics['current_return'])
        
        avg_return = sum(returns) / len(returns) if returns else 0
        
        # 计算历史成功率
        if self.recommendation_history:
            successful_recs = sum(
                1 for rec in self.recommendation_history
                if rec.get('performance_metrics', {}).get('current_return', 0) > 0
            )
            success_rate = successful_recs / len(self.recommendation_history) * 100
        else:
            success_rate = 0
        
        return {
            'total_active_recommendations': total_recs,
            'total_historical_recommendations': len(self.recommendation_history),
            'avg_score': avg_score,
            'avg_return': avg_return,
            'success_rate': success_rate
        }
    
    def generate_recommendation_report(self) -> str:
        """生成推荐报告
        
        Returns:
            HTML格式的推荐报告
        """
        # 获取性能统计
        stats = self.get_performance_stats()
        
        # 获取排名靠前的推荐
        top_recommendations = self.get_top_recommendations(10)
        
        # 生成HTML报告
        html = f"""
        <html>
        <head>
            <title>智能股票推荐报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>智能股票推荐报告</h1>
            <div class="summary">
                <h2>系统概况</h2>
                <p>当前活跃推荐: {stats['total_active_recommendations']}</p>
                <p>历史推荐总数: {stats['total_historical_recommendations']}</p>
                <p>平均推荐评分: {stats['avg_score']:.2f}</p>
                <p>平均当前收益率: <span class="{'positive' if stats['avg_return'] >= 0 else 'negative'}">{stats['avg_return']:.2f}%</span></p>
                <p>历史成功率: {stats['success_rate']:.2f}%</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>排名靠前的推荐</h2>
            <table>
                <tr>
                    <th>股票代码</th>
                    <th>股票名称</th>
                    <th>推荐日期</th>
                    <th>推荐评分</th>
                    <th>建议买入价</th>
                    <th>目标价格</th>
                    <th>止损价格</th>
                    <th>当前收益率</th>
                    <th>收益比</th>
                </tr>
        """
        
        # 添加推荐行
        for rec in top_recommendations:
            current_return = rec.performance_metrics.get('current_return', 0)
            
            html += f"""
                <tr>
                    <td>{rec.stock_code}</td>
                    <td>{rec.stock_name}</td>
                    <td>{rec.recommendation_date.strftime('%Y-%m-%d')}</td>
                    <td>{rec.score:.2f}</td>
                    <td>{rec.entry_price:.2f}</td>
                    <td>{rec.target_price:.2f}</td>
                    <td>{rec.stop_loss:.2f}</td>
                    <td class="{'positive' if current_return >= 0 else 'negative'}">{current_return:.2f}%</td>
                    <td>{rec.risk_reward_ratio:.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        # 保存HTML报告
        report_path = os.path.join(self.data_path, f"recommendation_report_{datetime.now().strftime('%Y%m%d')}.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"生成推荐报告: {report_path}")
        return report_path

def create_recommendation(
    stock_code: str,
    stock_name: str,
    entry_price: float,
    target_price: float,
    stop_loss: float,
    reason: str,
    source: str,
    score: float = 75.0,
    tags: List[str] = None
) -> StockRecommendation:
    """创建新的推荐
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        entry_price: 建议买入价格
        target_price: 目标价格
        stop_loss: 止损价格
        reason: 推荐理由
        source: 推荐来源
        score: 推荐评分
        tags: 标签
        
    Returns:
        新的推荐对象
    """
    recommendation = StockRecommendation(
        stock_code=stock_code,
        stock_name=stock_name,
        recommendation_date=datetime.now(),
        entry_price=entry_price,
        target_price=target_price,
        stop_loss=stop_loss,
        reason=reason,
        source=source,
        score=score,
        tags=tags or []
    )
    
    return recommendation

# 全局实例
recommendation_system = None

def get_recommendation_system() -> SmartRecommendationSystem:
    """获取全局推荐系统实例"""
    global recommendation_system
    
    if recommendation_system is None:
        recommendation_system = SmartRecommendationSystem()
    
    return recommendation_system

if __name__ == "__main__":
    # 测试代码
    system = SmartRecommendationSystem()
    
    # 创建测试推荐
    recommendation = create_recommendation(
        stock_code="000001",
        stock_name="平安银行",
        entry_price=10.5,
        target_price=12.0,
        stop_loss=9.8,
        reason="技术面突破，量能放大，短期看涨",
        source="技术分析",
        score=85.0,
        tags=["银行", "金融", "短线"]
    )
    
    # 添加到系统
    system.add_recommendation(recommendation)
    
    # 更新价格
    system.update_prices({"000001": 11.2})
    
    # 输出报告
    report_path = system.generate_recommendation_report()
    print(f"生成报告: {report_path}") 