"""
数据源健康监控模块
负责监控数据源的健康状态、性能指标和自动恢复
"""

import time
import logging
import asyncio
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from collections import deque

class DataSourceMetrics:
    """数据源指标收集类"""
    def __init__(self, retention_period: int = 86400):
        self.response_times = deque(maxlen=1000)
        self.error_counts = deque(maxlen=1000)
        self.success_counts = deque(maxlen=1000)
        self.last_error = None
        self.last_success = None
        self.retention_period = retention_period
        self.timestamps = deque(maxlen=1000)

    def record_response_time(self, response_time: float):
        """记录响应时间"""
        self.response_times.append(response_time)
        self.timestamps.append(time.time())
        self._cleanup_old_data()

    def record_error(self, error: Exception):
        """记录错误"""
        self.error_counts.append(1)
        self.success_counts.append(0)
        self.last_error = error
        self.timestamps.append(time.time())
        self._cleanup_old_data()

    def record_success(self):
        """记录成功"""
        self.error_counts.append(0)
        self.success_counts.append(1)
        self.last_success = time.time()
        self.timestamps.append(time.time())
        self._cleanup_old_data()

    def get_error_rate(self) -> float:
        """计算错误率"""
        if not self.error_counts:
            return 0.0
        total = sum(self.error_counts) + sum(self.success_counts)
        return sum(self.error_counts) / total if total > 0 else 0.0

    def get_avg_response_time(self) -> float:
        """计算平均响应时间"""
        return np.mean(self.response_times) if self.response_times else 0.0

    def _cleanup_old_data(self):
        """清理过期数据"""
        current_time = time.time()
        while self.timestamps and (current_time - self.timestamps[0]) > self.retention_period:
            self.timestamps.popleft()
            if self.response_times:
                self.response_times.popleft()
            if self.error_counts:
                self.error_counts.popleft()
            if self.success_counts:
                self.success_counts.popleft()

class DataSourceMonitor:
    """数据源监控类"""
    def __init__(self, config_path: str):
        self.logger = logging.getLogger("DataSourceMonitor")
        self.config = self._load_config(config_path)
        self.metrics: Dict[str, DataSourceMetrics] = {}
        self.health_check_tasks = {}
        self.is_running = False

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return {}

    async def start_monitoring(self):
        """启动监控"""
        self.is_running = True
        for source_name, source_config in self.config['data_sources'].items():
            self.metrics[source_name] = DataSourceMetrics(
                self.config['health_monitor']['metrics_retention']
            )
            self.health_check_tasks[source_name] = asyncio.create_task(
                self._health_check_loop(source_name, source_config)
            )

    async def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        for task in self.health_check_tasks.values():
            task.cancel()
        await asyncio.gather(*self.health_check_tasks.values(), return_exceptions=True)

    async def _health_check_loop(self, source_name: str, source_config: dict):
        """健康检查循环"""
        while self.is_running:
            try:
                await self._perform_health_check(source_name, source_config)
                await asyncio.sleep(source_config['health_check_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查失败 {source_name}: {str(e)}")
                await asyncio.sleep(10)  # 错误后等待10秒再重试

    async def _perform_health_check(self, source_name: str, source_config: dict):
        """执行健康检查"""
        metrics = self.metrics[source_name]
        error_rate = metrics.get_error_rate()
        avg_response_time = metrics.get_avg_response_time()

        # 检查错误率
        if error_rate > self.config['health_monitor']['alert_threshold']:
            self.logger.warning(
                f"数据源 {source_name} 错误率过高: {error_rate:.2%}"
            )
            if source_config['auto_reconnect']:
                await self._attempt_reconnect(source_name)

        # 检查响应时间
        if avg_response_time > self.config['health_monitor']['performance_threshold']:
            self.logger.warning(
                f"数据源 {source_name} 响应时间过长: {avg_response_time:.2f}ms"
            )

        # 记录健康状态
        self.logger.info(
            f"数据源 {source_name} 健康状态: "
            f"错误率={error_rate:.2%}, "
            f"平均响应时间={avg_response_time:.2f}ms"
        )

    async def _attempt_reconnect(self, source_name: str):
        """尝试重新连接数据源"""
        source_config = self.config['data_sources'][source_name]
        retry_config = self.config['retry_strategy']

        for attempt in range(retry_config['max_attempts']):
            try:
                # 这里应该实现实际的重连逻辑
                self.logger.info(f"尝试重新连接数据源 {source_name} (第{attempt + 1}次)")
                
                # 模拟重连操作
                await asyncio.sleep(1)
                
                # 如果重连成功，重置指标
                self.metrics[source_name] = DataSourceMetrics(
                    self.config['health_monitor']['metrics_retention']
                )
                self.logger.info(f"数据源 {source_name} 重连成功")
                return True
            except Exception as e:
                delay = min(
                    retry_config['initial_delay'] * (2 ** attempt),
                    retry_config['max_delay']
                )
                self.logger.error(
                    f"重连数据源 {source_name} 失败: {str(e)}, "
                    f"{delay}秒后重试"
                )
                await asyncio.sleep(delay)

        self.logger.error(f"数据源 {source_name} 重连失败，已达到最大重试次数")
        return False

    def record_request(self, source_name: str, success: bool, 
                      response_time: Optional[float] = None, 
                      error: Optional[Exception] = None):
        """记录请求结果"""
        if source_name not in self.metrics:
            self.metrics[source_name] = DataSourceMetrics(
                self.config['health_monitor']['metrics_retention']
            )

        metrics = self.metrics[source_name]
        if success:
            metrics.record_success()
            if response_time is not None:
                metrics.record_response_time(response_time)
        else:
            metrics.record_error(error)

    def get_source_status(self, source_name: str) -> dict:
        """获取数据源状态"""
        if source_name not in self.metrics:
            return {
                'status': 'unknown',
                'error_rate': 0.0,
                'avg_response_time': 0.0,
                'last_error': None,
                'last_success': None
            }

        metrics = self.metrics[source_name]
        return {
            'status': 'healthy' if metrics.get_error_rate() < self.config['health_monitor']['alert_threshold'] else 'unhealthy',
            'error_rate': metrics.get_error_rate(),
            'avg_response_time': metrics.get_avg_response_time(),
            'last_error': metrics.last_error,
            'last_success': metrics.last_success
        }

    def get_all_source_status(self) -> Dict[str, dict]:
        """获取所有数据源状态"""
        return {
            source_name: self.get_source_status(source_name)
            for source_name in self.config['data_sources'].keys()
        } 