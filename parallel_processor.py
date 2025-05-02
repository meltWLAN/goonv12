"""
并行处理管理器
实现高效的并行数据获取和处理
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from dataclasses import dataclass
from functools import partial

@dataclass
class TaskResult:
    """任务结果"""
    success: bool
    data: Any
    error: Optional[Exception] = None
    execution_time: float = 0.0

class ParallelProcessor:
    """并行处理器"""
    def __init__(self, config: dict):
        self.logger = logging.getLogger("ParallelProcessor")
        self.config = config
        self.thread_pool = ThreadPoolExecutor(
            max_workers=config['parallel_processing']['max_workers']
        )
        self.process_pool = ProcessPoolExecutor(
            max_workers=max(1, config['parallel_processing']['max_workers'] // 2)
        )
        self.active_tasks: Dict[str, asyncio.Task] = {}

    async def process_batch(self, 
                          items: List[Any],
                          process_func: Callable,
                          chunk_size: Optional[int] = None,
                          timeout: Optional[float] = None) -> List[TaskResult]:
        """批量处理数据"""
        chunk_size = chunk_size or self.config['parallel_processing']['chunk_size']
        timeout = timeout or self.config['parallel_processing']['timeout']
        
        # 将数据分块
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        results = []
        
        # 创建处理任务
        tasks = []
        for chunk in chunks:
            task = asyncio.create_task(
                self._process_chunk(chunk, process_func, timeout)
            )
            tasks.append(task)
        
        # 等待所有任务完成
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        for chunk_result in chunk_results:
            if isinstance(chunk_result, Exception):
                self.logger.error(f"处理数据块时发生错误: {str(chunk_result)}")
                continue
            results.extend(chunk_result)
        
        return results

    async def _process_chunk(self,
                           chunk: List[Any],
                           process_func: Callable,
                           timeout: float) -> List[TaskResult]:
        """处理数据块"""
        results = []
        
        # 创建处理任务
        tasks = []
        for item in chunk:
            task = asyncio.create_task(
                self._process_item(item, process_func, timeout)
            )
            tasks.append(task)
        
        # 等待所有任务完成或超时
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED
        )
        
        # 处理完成的任务
        for task in done:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                self.logger.error(f"处理数据项时发生错误: {str(e)}")
                results.append(TaskResult(
                    success=False,
                    data=None,
                    error=e,
                    execution_time=0.0
                ))
        
        # 取消未完成的任务
        for task in pending:
            task.cancel()
            results.append(TaskResult(
                success=False,
                data=None,
                error=TimeoutError("处理超时"),
                execution_time=timeout
            ))
        
        return results

    async def _process_item(self,
                          item: Any,
                          process_func: Callable,
                          timeout: float) -> TaskResult:
        """处理单个数据项"""
        start_time = time.time()
        try:
            # 使用线程池执行处理函数
            result = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                process_func,
                item
            )
            execution_time = time.time() - start_time
            return TaskResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                data=None,
                error=e,
                execution_time=execution_time
            )

    async def process_with_retry(self,
                               item: Any,
                               process_func: Callable,
                               max_retries: int = 3,
                               retry_delay: float = 1.0) -> TaskResult:
        """带重试的数据处理"""
        last_error = None
        total_time = 0.0
        
        for attempt in range(max_retries):
            if attempt > 0:
                # 计算重试延迟
                delay = retry_delay * (2 ** (attempt - 1))  # 指数退避
                await asyncio.sleep(delay)
            
            result = await self._process_item(
                item,
                process_func,
                self.config['parallel_processing']['timeout']
            )
            total_time += result.execution_time
            
            if result.success:
                return result
            
            last_error = result.error
            self.logger.warning(
                f"处理失败 (尝试 {attempt + 1}/{max_retries}): {str(last_error)}"
            )
        
        return TaskResult(
            success=False,
            data=None,
            error=last_error,
            execution_time=total_time
        )

    async def process_with_fallback(self,
                                  item: Any,
                                  primary_func: Callable,
                                  fallback_func: Callable) -> TaskResult:
        """带故障转移的数据处理"""
        # 尝试使用主处理函数
        result = await self._process_item(
            item,
            primary_func,
            self.config['parallel_processing']['timeout']
        )
        
        if result.success:
            return result
        
        # 如果主处理失败，使用备用处理函数
        self.logger.warning(f"主处理失败，使用备用处理: {str(result.error)}")
        fallback_result = await self._process_item(
            item,
            fallback_func,
            self.config['parallel_processing']['timeout']
        )
        
        # 合并执行时间
        fallback_result.execution_time += result.execution_time
        return fallback_result

    def get_active_tasks(self) -> Dict[str, Dict]:
        """获取活动任务状态"""
        return {
            task_id: {
                'running': not task.done(),
                'cancelled': task.cancelled(),
                'exception': task.exception() if task.done() else None,
                'start_time': task.get_name()  # 使用任务名称存储开始时间
            }
            for task_id, task in self.active_tasks.items()
        }

    async def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.active_tasks[task_id]
                return True
        return False

    async def shutdown(self):
        """关闭处理器"""
        # 取消所有活动任务
        for task_id in list(self.active_tasks.keys()):
            await self.cancel_task(task_id)
        
        # 关闭线程池和进程池
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

    def get_stats(self) -> dict:
        """获取处理器统计信息"""
        return {
            'active_tasks': len(self.active_tasks),
            'thread_pool_workers': self.thread_pool._max_workers,
            'process_pool_workers': self.process_pool._max_workers,
            'tasks': self.get_active_tasks()
        } 