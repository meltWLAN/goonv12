from enhanced_data_provider import EnhancedDataProvider
import pandas as pd
import logging

def test_basic_functionality():
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化数据提供者
        logger.info("初始化数据提供者...")
        provider = EnhancedDataProvider()
        
        # 初始化内存缓存
        provider.memory_cache = {}
        
        # 测试获取股票日线数据
        logger.info("测试获取股票日线数据...")
        stock_data = provider.get_stock_daily('000001.SZ', start_date='20250401', end_date='20250429')
        if not stock_data.empty:
            logger.info(f"成功获取股票数据，共 {len(stock_data)} 条记录")
            logger.info("\n" + str(stock_data.head()))
        else:
            logger.error("获取股票数据失败")
            
        # 测试获取行业列表
        logger.info("\n测试获取行业列表...")
        sectors = provider.get_sector_list()
        if sectors:
            logger.info(f"成功获取行业列表，共 {len(sectors)} 个行业")
            logger.info("前5个行业：")
            for sector in sectors[:5]:
                logger.info(f"行业名称: {sector['name']}, 涨跌幅: {sector['change_pct']}%")
        else:
            logger.error("获取行业列表失败")
            
        # 测试获取市场概览
        logger.info("\n测试获取市场概览...")
        overview = provider.get_market_overview()
        if overview:
            logger.info("市场概览数据：")
            logger.info(f"日期: {overview.get('date')}")
            logger.info(f"上证指数: {overview.get('indices', {}).get('sh')}")
            logger.info(f"深证成指: {overview.get('indices', {}).get('sz')}")
            logger.info(f"创业板指: {overview.get('indices', {}).get('cyb')}")
        else:
            logger.error("获取市场概览失败")
            
        # 测试数据源健康状态
        logger.info("\n测试数据源健康状态...")
        health_status = provider.check_data_source_health()
        for source, status in health_status.items():
            logger.info(f"{source} 状态: {'健康' if status['is_healthy'] else '异常'}")
            
        logger.info("\n系统验证完成!")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise  # 抛出异常以便查看完整的错误信息

if __name__ == "__main__":
    test_basic_functionality() 