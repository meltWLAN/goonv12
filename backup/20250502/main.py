"""
系统主入口
整合数据源监控、缓存管理和并行处理功能
"""

import asyncio
import logging
import os
import yaml
import signal
from typing import Dict, Optional
from data_source_monitor import DataSourceMonitor
from cache_manager import CacheManager
from parallel_processor import ParallelProcessor
from enhanced_data_provider import EnhancedDataProvider

class SystemManager:
    """系统管理器"""
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger("SystemManager")
        self.config = self._load_config()
        self.is_running = False
        self.components: Dict[str, Optional[object]] = {
            'monitor': None,
            'cache': None,
            'processor': None,
            'data_provider': None
        }

    def _setup_logging(self):
        """配置日志系统"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "system.log")),
                logging.StreamHandler()
            ]
        )

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open("data_source_config.yaml", 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            raise

    async def _initialize_components(self):
        """初始化所有组件"""
        try:
            # 初始化数据源监控
            self.components['monitor'] = DataSourceMonitor("data_source_config.yaml")
            await self.components['monitor'].start_monitoring()
            self.logger.info("数据源监控已启动")

            # 初始化缓存管理器
            self.components['cache'] = CacheManager(self.config)
            await self.components['cache'].start()
            self.logger.info("缓存管理器已启动")

            # 初始化并行处理器
            self.components['processor'] = ParallelProcessor(self.config)
            self.logger.info("并行处理器已启动")

            # 初始化数据提供者
            self.components['data_provider'] = EnhancedDataProvider(
                token=os.getenv("TUSHARE_TOKEN"),
                cache_dir=self.config['cache']['disk_path']
            )
            self.logger.info("数据提供者已启动")

        except Exception as e:
            self.logger.error(f"初始化组件失败: {str(e)}")
            await self.shutdown()
            raise

    async def _health_check(self):
        """系统健康检查"""
        while self.is_running:
            try:
                # 检查数据源状态
                if self.components['monitor']:
                    status = self.components['monitor'].get_all_source_status()
                    for source, stats in status.items():
                        if stats['status'] != 'healthy':
                            self.logger.warning(f"数据源 {source} 状态异常: {stats}")

                # 检查缓存状态
                if self.components['cache']:
                    stats = self.components['cache'].get_cache_stats()
                    if stats['memory_cache']['utilization'] > 0.9:
                        self.logger.warning("内存缓存使用率过高")

                # 检查处理器状态
                if self.components['processor']:
                    stats = self.components['processor'].get_stats()
                    if stats['active_tasks'] > self.config['parallel_processing']['max_workers'] * 2:
                        self.logger.warning("活动任务数量过多")

                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"健康检查失败: {str(e)}")
                await asyncio.sleep(10)

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown())
            )

    async def start(self):
        """启动系统"""
        self.logger.info("正在启动系统...")
        self.is_running = True
        
        try:
            # 设置信号处理
            self._setup_signal_handlers()
            
            # 初始化组件
            await self._initialize_components()
            
            # 启动健康检查
            health_check_task = asyncio.create_task(self._health_check())
            
            # 预加载常用数据
            if self.components['cache'] and self.components['data_provider']:
                preload_symbols = self.config['data_sources']['tushare']['preload_symbols']
                preload_tasks = []
                for symbol in preload_symbols:
                    task = self.components['cache'].preload_data(
                        f"daily_{symbol}",
                        lambda: self.components['data_provider'].get_stock_daily(symbol),
                        self.config['data_sources']['tushare']['cache_ttl']
                    )
                    preload_tasks.append(task)
                await asyncio.gather(*preload_tasks)
                self.logger.info("数据预加载完成")
            
            self.logger.info("系统启动完成")
            
            # 保持系统运行
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"系统启动失败: {str(e)}")
            await self.shutdown()
            raise
        finally:
            if health_check_task:
                health_check_task.cancel()
                try:
                    await health_check_task
                except asyncio.CancelledError:
                    pass

    async def shutdown(self):
        """关闭系统"""
        if not self.is_running:
            return
            
        self.logger.info("正在关闭系统...")
        self.is_running = False
        
        # 关闭所有组件
        if self.components['monitor']:
            await self.components['monitor'].stop_monitoring()
            
        if self.components['cache']:
            await self.components['cache'].stop()
            
        if self.components['processor']:
            await self.components['processor'].shutdown()
            
        self.logger.info("系统已关闭")

async def main():
    """主函数"""
    system = SystemManager()
    try:
        await system.start()
    except KeyboardInterrupt:
        await system.shutdown()
    except Exception as e:
        logging.error(f"系统运行错误: {str(e)}")
        await system.shutdown()
        raise

if __name__ == "__main__":
    asyncio.run(main())