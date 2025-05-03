from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import os

# 导入模型管理器
from evolving_backtester import ModelManager

# 配置日志
logger = logging.getLogger('EvolvingBacktester')

def calculate_position_size(self, features: Dict, signal_strength: float, price: float, stop_loss: float) -> float:
    """计算最优仓位大小
    
    Args:
        features: 特征字典
        signal_strength: 信号强度 (0-1)
        price: 当前价格
        stop_loss: 止损价格
        
    Returns:
        仓位比例 (0-1)，表示应该使用的总资金比例
    """
    try:
        # 如果特征不完整，使用基本方法计算
        if not features or len(features) < 10 or self.model_manager.models['position'] is None:
            # 计算风险（价格到止损的距离）
            risk_per_share = price - stop_loss
            
            # 基础风险金额（账户的1%）
            base_risk_amount = self.current_capital * 0.01
            
            # 调整风险金额
            adjusted_risk = base_risk_amount * signal_strength
            
            # 计算可承受的仓位比例
            if risk_per_share > 0:
                position_ratio = adjusted_risk / (self.current_capital * risk_per_share / price)
            else:
                # 如果止损价格不合理，使用基础仓位
                position_ratio = self.max_position_ratio * signal_strength
            
            # 确保不超过最大仓位限制
            position_ratio = min(position_ratio, self.max_position_ratio)
            
            return float(max(0.0, position_ratio))
        
        # 获取模型预测的仓位比例
        position_ratio = self.model_manager.predict_position_size(list(features.values()))
        
        # 应用信号强度调整
        adjusted_ratio = position_ratio * signal_strength * self.adaptive_params['position_size_factor']
        
        # 确保不超过最大仓位限制
        adjusted_ratio = min(adjusted_ratio, self.max_position_ratio)
        
        logger.info(f"计算仓位: 模型建议比例={position_ratio:.4f}, 调整后比例={adjusted_ratio:.4f}, 资金比例={adjusted_ratio:.2%}")
        
        return float(max(0.0, adjusted_ratio))
        
    except Exception as e:
        logger.error(f"计算仓位大小出错: {str(e)}")
        
        # 基本仓位计算作为后备
        position_ratio = self.max_position_ratio * 0.5 * signal_strength
        return float(max(0.0, position_ratio))
