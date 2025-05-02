"""
测试增强特性
验证数据源监控、缓存管理和并行处理功能
"""

import asyncio
import logging
import os
import time
import pandas as pd
from datetime import datetime, timedelta
from data_source_monitor import DataSourceMonitor
from cache_manager import CacheManager
from parallel_processor import ParallelProcessor
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_features_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedFeaturesTest")

async def test_data_source_monitor():
    """测试数据源监控"""
    logger.info("\n=== 测试数据源监控 ===")
    
    monitor = DataSourceMonitor("data_source_config.yaml")
    await monitor.start_monitoring()
    
    # 模拟数据源操作
    monitor.record_request("tushare", True, 0.5)
    monitor.record_request("tushare", True, 0.8)
    monitor.record_request("tushare", False, error=Exception("API错误"))
    
    monitor.record_request("akshare", True, 0.3)
    monitor.record_request("akshare", True, 0.4)
    
    # 获取状态
    status = monitor.get_all_source_status()
    logger.info("数据源状态:")
    for source, stats in status.items():
        logger.info(f"\n{source}:")
        for key, value in stats.items():
            logger.info(f"- {key}: {value}")
    
    await monitor.stop_monitoring()

async def test_cache_manager():
    """测试缓存管理"""
    logger.info("\n=== 测试缓存管理 ===")
    
    with open("data_source_config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    cache_manager = CacheManager(config)
    await cache_manager.start()
    
    # 测试缓存操作
    test_data = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=100),
        'value': range(100)
    })
    
    # 设置缓存
    await cache_manager.set('test_key', test_data, ttl=3600)
    
    # 获取缓存
    cached_data = await cache_manager.get('test_key')
    if cached_data is not None:
        logger.info("成功从缓存获取数据")
        logger.info(f"数据大小: {len(cached_data)}")
    
    # 获取缓存统计
    stats = cache_manager.get_cache_stats()
    logger.info("\n缓存统计:")
    for key, value in stats.items():
        logger.info(f"{key}:")
        if isinstance(value, dict):
            for k, v in value.items():
                logger.info(f"  - {k}: {v}")
        else:
            logger.info(f"  {value}")
    
    await cache_manager.stop()

async def test_parallel_processor():
    """测试并行处理"""
    logger.info("\n=== 测试并行处理 ===")
    
    with open("data_source_config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    processor = ParallelProcessor(config)
    
    # 测试数据
    test_items = list(range(100))
    
    # 测试函数
    def process_item(x):
        # 模拟处理时间
        time.sleep(0.1)
        if x % 10 == 0:
            raise ValueError(f"处理项 {x} 失败")
        return x * 2
    
    # 测试批量处理
    logger.info("测试批量处理:")
    results = await processor.process_batch(
        test_items[:10],
        process_item,
        chunk_size=3
    )
    
    success_count = sum(1 for r in results if r.success)
    error_count = sum(1 for r in results if not r.success)
    logger.info(f"成功: {success_count}, 失败: {error_count}")
    
    # 测试重试机制
    logger.info("\n测试重试机制:")
    retry_result = await processor.process_with_retry(
        5,
        process_item,
        max_retries=3
    )
    logger.info(f"重试结果: {'成功' if retry_result.success else '失败'}")
    
    # 测试故障转移
    logger.info("\n测试故障转移:")
    def fallback_process(x):
        return x + 1
    
    fallback_result = await processor.process_with_fallback(
        10,  # 会触发主处理函数的错误
        process_item,
        fallback_process
    )
    logger.info(f"故障转移结果: {'成功' if fallback_result.success else '失败'}")
    
    # 获取处理器统计
    stats = processor.get_stats()
    logger.info("\n处理器统计:")
    for key, value in stats.items():
        logger.info(f"- {key}: {value}")
    
    await processor.shutdown()

async def main():
    """主测试函数"""
    logger.info("开始测试增强特性...")
    
    try:
        # 运行所有测试
        await test_data_source_monitor()
        await test_cache_manager()
        await test_parallel_processor()
        
        logger.info("\n所有测试完成!")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 