import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error
import os
import logging
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='evolving_backtester.log')
logger = logging.getLogger('EvolvingBacktester')

class ModelManager:
    """管理机器学习模型的训练和使用"""
    
    def __init__(self, models_dir="./ml_models"):
        """初始化模型管理器
        
        Args:
            models_dir: 模型保存目录
        """
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        
        # 初始化模型字典
        self.models = {
            'entry': None,  # 入场信号预测
            'exit': None,   # 出场信号预测
            'risk': None,   # 风险评估
            'position': None, # 仓位大小预测
            'trend': None,  # 趋势预测
            'volatility': None, # 波动率预测
        }
        
        # 特征缩放器
        self.scalers = {}
        
        # 尝试加载现有模型
        self._load_models()
        
    def _load_models(self):
        """加载现有训练好的模型"""
        try:
            for model_name in self.models.keys():
                model_path = os.path.join(self.models_dir, f"{model_name}_model.pkl")
                scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
                
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.models[model_name] = joblib.load(model_path)
                    self.scalers[model_name] = joblib.load(scaler_path)
                    logger.info(f"已加载模型: {model_name}")
        except Exception as e:
            logger.error(f"加载模型出错: {str(e)}")
    
    def save_models(self):
        """保存所有训练好的模型"""
        try:
            for model_name, model in self.models.items():
                if model is not None:
                    model_path = os.path.join(self.models_dir, f"{model_name}_model.pkl")
                    joblib.dump(model, model_path)
                    
                    if model_name in self.scalers:
                        scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
                        joblib.dump(self.scalers[model_name], scaler_path)
                        
            logger.info("所有模型已保存")
        except Exception as e:
            logger.error(f"保存模型出错: {str(e)}")
    
    def train_entry_model(self, X, y):
        """训练入场信号预测模型
        
        Args:
            X: 特征数据
            y: 标签（1为入场信号，0为非入场信号）
        """
        try:
            # 数据标准化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['entry'] = scaler
            
            # 分割训练和测试数据
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
            
            # 创建并训练模型
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # 评估模型
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            logger.info(f"入场模型训练完成 - 准确率: {accuracy:.4f}, 精确度: {precision:.4f}, 召回率: {recall:.4f}, F1: {f1:.4f}")
            
            # 保存模型
            self.models['entry'] = model
            
            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
            
        except Exception as e:
            logger.error(f"训练入场模型出错: {str(e)}")
            return None
    
    def train_exit_model(self, X, y):
        """训练出场信号预测模型
        
        Args:
            X: 特征数据
            y: 标签（1为出场信号，0为非出场信号）
        """
        try:
            # 数据标准化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['exit'] = scaler
            
            # 分割训练和测试数据
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
            
            # 创建并训练模型
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # 评估模型
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            logger.info(f"出场模型训练完成 - 准确率: {accuracy:.4f}, 精确度: {precision:.4f}, 召回率: {recall:.4f}, F1: {f1:.4f}")
            
            # 保存模型
            self.models['exit'] = model
            
            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
            
        except Exception as e:
            logger.error(f"训练出场模型出错: {str(e)}")
            return None
    
    def train_position_model(self, X, y):
        """训练仓位大小预测模型
        
        Args:
            X: 特征数据
            y: 仓位大小百分比 (0-1)
        """
        try:
            # 数据标准化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['position'] = scaler
            
            # 分割训练和测试数据
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
            
            # 创建并训练模型
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # 评估模型
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            logger.info(f"仓位模型训练完成 - RMSE: {rmse:.4f}")
            
            # 保存模型
            self.models['position'] = model
            
            return {
                'rmse': rmse
            }
            
        except Exception as e:
            logger.error(f"训练仓位模型出错: {str(e)}")
            return None
    
    def predict_entry_signal(self, features):
        """预测入场信号
        
        Args:
            features: 特征数据
            
        Returns:
            入场概率 (0-1)
        """
        if self.models['entry'] is None or 'entry' not in self.scalers:
            return 0.5  # 默认概率
        
        try:
            # 标准化特征
            features_scaled = self.scalers['entry'].transform([features])
            
            # 预测概率
            proba = self.models['entry'].predict_proba(features_scaled)[0][1]
            
            return proba
            
        except Exception as e:
            logger.error(f"预测入场信号出错: {str(e)}")
            return 0.5
    
    def predict_exit_signal(self, features):
        """预测出场信号
        
        Args:
            features: 特征数据
            
        Returns:
            出场概率 (0-1)
        """
        if self.models['exit'] is None or 'exit' not in self.scalers:
            return 0.5  # 默认概率
        
        try:
            # 标准化特征
            features_scaled = self.scalers['exit'].transform([features])
            
            # 预测概率
            proba = self.models['exit'].predict_proba(features_scaled)[0][1]
            
            return proba
            
        except Exception as e:
            logger.error(f"预测出场信号出错: {str(e)}")
            return 0.5
    
    def predict_position_size(self, features):
        """预测仓位大小
        
        Args:
            features: 特征数据
            
        Returns:
            建议仓位大小比例 (0-1)
        """
        if self.models['position'] is None or 'position' not in self.scalers:
            return 0.1  # 默认仓位
        
        try:
            # 标准化特征
            features_scaled = self.scalers['position'].transform([features])
            
            # 预测值
            position = self.models['position'].predict(features_scaled)[0]
            
            # 确保在合理范围内
            position = max(0.01, min(0.5, position))
            
            return position
            
        except Exception as e:
            logger.error(f"预测仓位大小出错: {str(e)}")
            return 0.1 