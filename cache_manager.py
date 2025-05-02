"""
缓存管理器模块
实现高效的缓存策略和预加载机制
"""

import os
import time
import pickle
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
import asyncio
from concurrent.futures import ThreadPoolExecutor

class CacheEntry:
    """缓存条目"""
    def __init__(self, key: str, value: Any, ttl: int):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl

    def access(self):
        """记录访问"""
        self.last_accessed = time.time()
        self.access_count += 1

class CacheManager:
    """缓存管理器"""
    def __init__(self, config: dict):
        self.logger = logging.getLogger("CacheManager")
        self.config = config
        self.memory_cache: OrderedDict = OrderedDict()
        self.disk_cache_path = config['cache']['disk_path']
        self.max_memory_size = config['cache']['memory_cache_size'] * 1024 * 1024  # 转换为字节
        self.current_memory_size = 0
        self.lock = threading.Lock()
        self.preload_queue: List[Tuple[str, dict]] = []
        self.thread_pool = ThreadPoolExecutor(
            max_workers=config['parallel_processing']['max_workers']
        )
        self.cleanup_task = None
        
        # 确保缓存目录存在
        os.makedirs(self.disk_cache_path, exist_ok=True)

    async def start(self):
        """启动缓存管理器"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """停止缓存管理器"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        self.thread_pool.shutdown(wait=True)

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        # 首先检查内存缓存
        with self.lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired():
                    entry.access()
                    self.memory_cache.move_to_end(key)
                    return entry.value
                else:
                    del self.memory_cache[key]

        # 如果内存中没有，检查磁盘缓存
        try:
            disk_path = os.path.join(self.disk_cache_path, f"{key}.cache")
            if os.path.exists(disk_path):
                with open(disk_path, 'rb') as f:
                    entry = pickle.load(f)
                if not entry.is_expired():
                    # 将磁盘缓存加载到内存
                    await self._add_to_memory_cache(key, entry.value, entry.ttl)
                    return entry.value
                else:
                    os.remove(disk_path)
        except Exception as e:
            self.logger.error(f"读取磁盘缓存失败 {key}: {str(e)}")

        return None

    async def set(self, key: str, value: Any, ttl: int):
        """设置缓存数据"""
        # 添加到内存缓存
        await self._add_to_memory_cache(key, value, ttl)

        # 异步保存到磁盘
        asyncio.create_task(self._save_to_disk(key, value, ttl))

    async def _add_to_memory_cache(self, key: str, value: Any, ttl: int):
        """添加到内存缓存"""
        entry = CacheEntry(key, value, ttl)
        entry_size = self._estimate_size(value)

        with self.lock:
            # 如果需要，清理空间
            while self.current_memory_size + entry_size > self.max_memory_size:
                if not self.memory_cache:
                    break
                # 根据缓存策略选择要删除的项
                removed_key = self._select_entry_to_remove()
                removed_entry = self.memory_cache.pop(removed_key)
                self.current_memory_size -= self._estimate_size(removed_entry.value)

            self.memory_cache[key] = entry
            self.current_memory_size += entry_size

    def _select_entry_to_remove(self) -> str:
        """根据缓存策略选择要删除的条目"""
        if self.config['cache']['strategy'] == 'lru':
            # 最近最少使用
            return next(iter(self.memory_cache))
        elif self.config['cache']['strategy'] == 'fifo':
            # 先进先出
            return next(iter(self.memory_cache))
        else:  # adaptive
            # 基于访问频率和时间的混合策略
            current_time = time.time()
            min_score = float('inf')
            min_key = None
            
            for key, entry in self.memory_cache.items():
                # 计算得分：访问频率 * 时间衰减
                time_factor = 1.0 / (current_time - entry.last_accessed + 1)
                score = entry.access_count * time_factor
                if score < min_score:
                    min_score = score
                    min_key = key
            
            return min_key

    async def _save_to_disk(self, key: str, value: Any, ttl: int):
        """保存到磁盘缓存"""
        try:
            entry = CacheEntry(key, value, ttl)
            disk_path = os.path.join(self.disk_cache_path, f"{key}.cache")
            
            # 使用线程池执行IO操作
            await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self._write_to_disk,
                disk_path,
                entry
            )
        except Exception as e:
            self.logger.error(f"保存到磁盘缓存失败 {key}: {str(e)}")

    def _write_to_disk(self, path: str, entry: CacheEntry):
        """写入磁盘"""
        with open(path, 'wb') as f:
            pickle.dump(entry, f)

    async def _cleanup_loop(self):
        """定期清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(self.config['cache']['cleanup_interval'])
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理缓存时发生错误: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待较长时间

    async def _cleanup_expired(self):
        """清理过期的缓存条目"""
        # 清理内存缓存
        with self.lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                entry = self.memory_cache.pop(key)
                self.current_memory_size -= self._estimate_size(entry.value)

        # 清理磁盘缓存
        try:
            for filename in os.listdir(self.disk_cache_path):
                if filename.endswith('.cache'):
                    file_path = os.path.join(self.disk_cache_path, filename)
                    try:
                        with open(file_path, 'rb') as f:
                            entry = pickle.load(f)
                        if entry.is_expired():
                            os.remove(file_path)
                    except Exception as e:
                        self.logger.error(f"清理磁盘缓存失败 {filename}: {str(e)}")
                        # 如果文件损坏，直接删除
                        try:
                            os.remove(file_path)
                        except:
                            pass
        except Exception as e:
            self.logger.error(f"清理磁盘缓存时发生错误: {str(e)}")

    def _estimate_size(self, obj: Any) -> int:
        """估算对象大小"""
        try:
            return len(pickle.dumps(obj))
        except:
            return 1024  # 默认大小1KB

    async def preload_data(self, key: str, fetch_func, ttl: int):
        """预加载数据"""
        try:
            # 检查是否已经在缓存中
            if await self.get(key) is not None:
                return

            # 异步获取数据
            data = await fetch_func()
            if data is not None:
                await self.set(key, data, ttl)
        except Exception as e:
            self.logger.error(f"预加载数据失败 {key}: {str(e)}")

    async def batch_preload(self, items: List[Tuple[str, Any, int]]):
        """批量预加载数据"""
        tasks = []
        for key, fetch_func, ttl in items:
            task = asyncio.create_task(self.preload_data(key, fetch_func, ttl))
            tasks.append(task)
        
        # 使用gather并发执行所有预加载任务
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        with self.lock:
            memory_cache_size = self.current_memory_size
            memory_cache_count = len(self.memory_cache)
            
            # 计算命中率
            total_entries = sum(entry.access_count for entry in self.memory_cache.values())
            expired_entries = len([1 for entry in self.memory_cache.values() if entry.is_expired()])
            
            # 获取磁盘缓存统计
            disk_cache_size = 0
            disk_cache_count = 0
            try:
                for filename in os.listdir(self.disk_cache_path):
                    if filename.endswith('.cache'):
                        file_path = os.path.join(self.disk_cache_path, filename)
                        disk_cache_size += os.path.getsize(file_path)
                        disk_cache_count += 1
            except Exception as e:
                self.logger.error(f"获取磁盘缓存统计失败: {str(e)}")

        return {
            'memory_cache': {
                'size': memory_cache_size,
                'count': memory_cache_count,
                'utilization': memory_cache_size / self.max_memory_size,
                'expired_count': expired_entries
            },
            'disk_cache': {
                'size': disk_cache_size,
                'count': disk_cache_count
            },
            'total_entries': total_entries
        } 