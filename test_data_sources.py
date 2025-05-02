"""
数据源验证测试脚本
用于测试各个数据源的可用性和数据质量
"""

import pandas as pd
import logging
import asyncio
from datetime import datetime, timedelta
from enhanced_data_provider import EnhancedDataProvider
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_source_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataSourceTest")

def test_stock_daily_data(provider):
    """测试股票日线数据获取"""
    logger.info("=== 测试股票日线数据获取 ===")
    
    # 测试样本
    test_cases = [
        {'code': '000001.SZ', 'name': '平安银行'},
        {'code': '600519.SH', 'name': '贵州茅台'},
        {'code': '300750.SZ', 'name': '宁德时代'}
    ]
    
    for case in test_cases:
        logger.info(f"\n测试 {case['name']} ({case['code']}) 的日线数据:")
        df = provider.get_stock_daily(
            code=case['code'],
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d')
        )
        
        if df is not None and not df.empty:
            logger.info(f"成功获取数据: {len(df)} 条记录")
            logger.info(f"数据字段: {', '.join(df.columns)}")
            logger.info(f"数据日期范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")
        else:
            logger.error(f"获取 {case['name']} 数据失败")

def test_sector_data(provider):
    """测试行业数据获取"""
    logger.info("\n=== 测试行业数据获取 ===")
    
    # 获取行业列表
    sectors = provider.get_sector_list()
    if sectors:
        logger.info(f"成功获取行业列表: {len(sectors)} 个行业")
        logger.info("示例行业:")
        for sector in sectors[:3]:
            logger.info(f"- {sector['name']}: 涨跌幅 {sector['change_pct']}%, 来源: {sector['source']}")
            
        # 测试获取行业成分股
        test_sector = sectors[0]
        logger.info(f"\n测试获取行业成分股: {test_sector['name']}")
        stocks = provider.get_sector_stocks(test_sector['name'])
        if stocks:
            logger.info(f"成功获取成分股: {len(stocks)} 只股票")
            logger.info(f"示例成分股: {', '.join(stocks[:5])}")
        else:
            logger.error("获取行业成分股失败")
    else:
        logger.error("获取行业列表失败")

def test_market_sentiment(provider):
    """测试市场情绪数据获取"""
    logger.info("\n=== 测试市场情绪数据获取 ===")
    
    sentiment = provider.get_market_sentiment()
    if sentiment:
        logger.info("市场情绪数据:")
        for key, value in sentiment.items():
            logger.info(f"- {key}: {value}")
    else:
        logger.error("获取市场情绪数据失败")

async def test_north_flow_data(provider):
    """测试北向资金数据获取"""
    logger.info("\n=== 测试北向资金数据获取 ===")
    
    north_flow = await provider.get_north_flow_data()
    if north_flow:
        logger.info("北向资金数据:")
        for key, value in north_flow.items():
            logger.info(f"- {key}: {value}")
            
        # 检查数据源健康状态
        logger.info("\n数据源健康状态:")
        health_status = provider.check_data_source_health()
        for source, status in health_status.items():
            logger.info(f"\n{source}数据源状态:")
            for metric, value in status.items():
                logger.info(f"- {metric}: {value}")
    else:
        logger.error("获取北向资金数据失败")

def test_data_source_fallback(provider):
    """测试数据源自动切换"""
    logger.info("\n=== 测试数据源自动切换 ===")
    
    # 模拟Tushare失败场景
    original_tushare_enabled = provider.data_sources['tushare']['enabled']
    provider.data_sources['tushare']['enabled'] = False
    
    logger.info("模拟Tushare不可用的情况:")
    df = provider.get_stock_daily('000001.SZ')
    if df is not None and not df.empty:
        logger.info("成功切换到备用数据源获取数据")
    else:
        logger.error("数据源切换失败")
    
    # 恢复Tushare状态
    provider.data_sources['tushare']['enabled'] = original_tushare_enabled

async def main():
    """主测试函数"""
    logger.info("开始数据源测试...")
    
    # 初始化数据提供者
    provider = EnhancedDataProvider(
        token=os.environ.get('TUSHARE_TOKEN', '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'),
        cache_dir="./test_cache",
        cache_expire_days=1
    )
    
    try:
        # 运行所有测试
        test_stock_daily_data(provider)
        test_sector_data(provider)
        test_market_sentiment(provider)
        await test_north_flow_data(provider)
        test_data_source_fallback(provider)
        
        logger.info("\n所有测试完成!")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise
    finally:
        # 关闭异步会话
        if provider.aiohttp_session:
            await provider.aiohttp_session.close()

if __name__ == "__main__":
    asyncio.run(main()) 