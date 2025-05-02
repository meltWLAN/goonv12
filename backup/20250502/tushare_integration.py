import sys
import os
import logging
import argparse
import pandas as pd
from datetime import datetime, timedelta
from tushare_data_center import TushareDataCenter
from enhanced_data_provider import EnhancedDataProvider

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tushare_integration')

def test_data_center(token, ts_code='000001.SZ'):
    """测试数据中心功能"""
    logger.info("测试数据中心...")
    
    # 初始化数据中心
    data_center = TushareDataCenter(token=token)
    
    # 测试基础数据
    stock_list = data_center.get_stock_list()
    logger.info(f"股票列表: {len(stock_list)} 条数据")
    
    # 测试行情数据
    daily_data = data_center.get_daily_data(ts_code, start_date='20230101')
    logger.info(f"日线数据: {len(daily_data)} 条数据")
    
    # 测试财务数据
    income = data_center.get_income(ts_code)
    logger.info(f"利润表: {len(income)} 条数据")
    
    # 测试股票画像
    profile = data_center.get_stock_profile(ts_code)
    logger.info(f"股票画像: {profile.get('basic_info', {}).get('name', '')}")
    
    logger.info("数据中心测试完成")
    return True

def test_enhanced_provider(token, ts_code='000001.SZ'):
    """测试增强数据提供器功能"""
    logger.info("测试增强数据提供器...")
    
    # 初始化数据提供器
    provider = EnhancedDataProvider(token=token)
    
    # 测试股票数据
    stock_data = provider.get_stock_data(ts_code, limit=30)
    logger.info(f"股票数据: {len(stock_data)} 条数据")
    if not stock_data.empty:
        # 检查技术指标
        indicators = ['ma5', 'ma20', 'macd', 'rsi_6', 'kdj_k', 'boll_upper']
        missing = [ind for ind in indicators if ind not in stock_data.columns]
        if missing:
            logger.warning(f"缺少技术指标: {missing}")
        else:
            logger.info("所有技术指标计算正确")
    
    # 测试财务数据
    financial = provider.get_financial_data(ts_code)
    logger.info(f"财务数据: 利润表 {len(financial['income'])} 条, 资产负债表 {len(financial['balance'])} 条")
    
    # 测试股票画像
    profile = provider.get_stock_profile(ts_code)
    logger.info(f"股票画像: {profile.get('basic_info', {}).get('name', '')}")
    if 'market_summary' in profile and 'technical_summary' in profile:
        logger.info("画像数据完整")
    
    # 测试行业数据
    industry = profile.get('industry', '')
    if industry:
        industry_stocks = provider.get_industry_stocks(industry)
        logger.info(f"行业 '{industry}' 股票数量: {len(industry_stocks)}")
        
        industry_perf = provider.get_industry_performance(industry, days=30)
        logger.info(f"行业表现: 平均涨跌幅 {industry_perf.get('avg_change_pct', 0):.2f}%")
    
    # 测试市场概览
    overview = provider.get_market_overview()
    logger.info(f"市场概览: 上证指数 {overview.get('indices', {}).get('sh', 0)}")
    
    # 测试股票筛选
    criteria = {
        'min_pe': 5,
        'max_pe': 30,
        'min_pb': 0.5,
        'max_pb': 5
    }
    screened = provider.screen_stocks(criteria)
    logger.info(f"筛选结果: {len(screened)} 只股票")
    
    logger.info("增强数据提供器测试完成")
    return True

def export_test_data(token, ts_code='000001.SZ', export_dir='./export_data'):
    """导出测试数据为CSV文件"""
    logger.info(f"导出测试数据到 {export_dir}...")
    
    # 创建导出目录
    os.makedirs(export_dir, exist_ok=True)
    
    # 初始化数据提供器
    provider = EnhancedDataProvider(token=token)
    
    # 导出股票列表
    stock_list = provider.data_center.get_stock_list()
    stock_list.to_csv(f"{export_dir}/stock_list.csv", index=False)
    logger.info(f"股票列表导出完成: {len(stock_list)} 条数据")
    
    # 导出股票日线数据
    stock_data = provider.get_stock_data(ts_code, limit=365)
    stock_data.to_csv(f"{export_dir}/{ts_code}_daily.csv", index=False)
    logger.info(f"股票日线数据导出完成: {len(stock_data)} 条数据")
    
    # 导出财务数据
    financial = provider.get_financial_data(ts_code)
    financial['income'].to_csv(f"{export_dir}/{ts_code}_income.csv", index=False)
    financial['balance'].to_csv(f"{export_dir}/{ts_code}_balance.csv", index=False)
    financial['cashflow'].to_csv(f"{export_dir}/{ts_code}_cashflow.csv", index=False)
    financial['indicator'].to_csv(f"{export_dir}/{ts_code}_indicator.csv", index=False)
    logger.info(f"财务数据导出完成")
    
    # 导出行业数据
    industry = provider.industry_map.get(ts_code, '')
    if industry:
        industry_stocks = provider.get_industry_stocks(industry)
        industry_stocks.to_csv(f"{export_dir}/{industry}_stocks.csv", index=False)
        logger.info(f"行业 '{industry}' 股票导出完成: {len(industry_stocks)} 条数据")
    
    # 导出市场概览
    overview = provider.get_market_overview()
    if overview and 'industry_performance' in overview:
        pd.DataFrame(overview['industry_performance']).to_csv(f"{export_dir}/industry_performance.csv", index=False)
        logger.info(f"行业表现导出完成: {len(overview['industry_performance'])} 条数据")
    
    logger.info("数据导出完成")
    return True

def main():
    parser = argparse.ArgumentParser(description='Tushare数据集成测试工具')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--ts_code', type=str, default='000001.SZ', help='股票代码')
    parser.add_argument('--test', choices=['data_center', 'provider', 'all'], default='all', help='测试内容')
    parser.add_argument('--export', action='store_true', help='是否导出测试数据')
    parser.add_argument('--export_dir', type=str, default='./export_data', help='导出目录')
    
    args = parser.parse_args()
    
    logger.info("开始Tushare数据集成测试...")
    
    try:
        if args.test in ['data_center', 'all']:
            test_data_center(args.token, args.ts_code)
            
        if args.test in ['provider', 'all']:
            test_enhanced_provider(args.token, args.ts_code)
            
        if args.export:
            export_test_data(args.token, args.ts_code, args.export_dir)
            
        logger.info("集成测试完成")
        return 0
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 