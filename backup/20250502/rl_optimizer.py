import numpy as np
from typing import Dict, Any
from collections import deque
from jf_trading_system import JFTradingSystem
from enhanced_backtesting import EnhancedBacktesting

class RLOptimizer:
    def __init__(self, trading_system: JFTradingSystem, backtester: EnhancedBacktesting):
        self.trading_system = trading_system
        self.backtester = backtester
        self.state_size = 10  # 包含：收益率、波动率、夏普比率、最大回撤等
        self.action_size = 6   # 可调整参数：仓位比例、止损比例等
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        # 初始化神经网络模型
        self.model = self._build_model()
        
    def _build_model(self):
        from tensorflow.keras import Sequential
        from tensorflow.keras.layers import Dense
        from tensorflow.keras.optimizers import Adam
        
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def get_current_state(self) -> np.ndarray:
        """获取当前策略状态"""
        metrics = self.backtester.get_performance_metrics()
        return np.array([
            metrics['total_return'],
            metrics['annualized_volatility'],
            metrics['sharpe_ratio'],
            metrics['max_drawdown'],
            metrics['win_rate'],
            self.trading_system.risk_threshold,
            self.trading_system.min_profit_ratio,
            self.backtester.market_volatility_percentile,
            metrics['profit_factor'],
            metrics['consecutive_losses']
        ])

    def adapt_parameters(self, episode: int):
        """动态调整策略参数"""
        state = self.get_current_state()
        state = np.reshape(state, [1, self.state_size])
        
        # 使用ε-贪婪策略选择动作
        if np.random.rand() <= self.epsilon:
            action = np.random.randint(self.action_size)
        else:
            q_values = self.model.predict(state, verbose=0)
            action = np.argmax(q_values[0])
        
        # 执行参数调整动作
        self._apply_action(action)
        
        # 衰减探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def _apply_action(self, action: int):
        """将RL决策转化为实际参数调整"""
        # 参数调整逻辑
        param_adjustments = {
            0: ('risk_threshold', 0.005),
            1: ('min_profit_ratio', 0.1),
            2: ('max_position_ratio', 0.01),
            3: ('trailing_stop_pct', 0.005),
            4: ('market_condition_weight', 0.05),
            5: ('volatility_adjustment', True)
        }
        
        param, delta = param_adjustments[action]
        current_value = getattr(self.trading_system, param, None) or \
                       getattr(self.backtester, param, None)
        
        if isinstance(current_value, bool):
            new_value = not current_value
        else:
            new_value = current_value + delta
            
        # 应用参数限制
        if param == 'risk_threshold':
            new_value = max(0.1, min(new_value, 0.3))
        elif param == 'min_profit_ratio':
            new_value = max(2.0, min(new_value, 5.0))
            
        setattr(self.trading_system, param, new_value)
        
    def remember(self, state, action, reward, next_state, done):
        """存储经验到记忆库"""
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, batch_size=32):
        """经验回放训练"""
        if len(self.memory) < batch_size:
            return
        
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

    def update_performance_metrics(self, metrics: Dict[str, float]):
        """更新绩效指标用于强化学习"""
        # 实现具体指标更新逻辑
        pass