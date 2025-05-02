import pandas as pd
from trading_system import TradingSystem
import yfinance as yf
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler()
    ]
)

def fetch_market_data(symbol: str, period: str = '1y') -> pd.DataFrame:
    """获取市场数据"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        return df
    except Exception as e:
        logging.error(f'获取市场数据失败: {str(e)}')
        return None

def main():
    # 初始化交易系统
    logging.info('初始化3L交易系统...')
    trading_system = TradingSystem()
    
    # 设置要分析的股票代码
    symbol = '^GSPC'  # S&P 500指数
    
    # 获取市场数据
    logging.info(f'获取{symbol}的市场数据...')
    market_data = fetch_market_data(symbol)
    
    if market_data is None:
        logging.error('无法获取市场数据，程序退出')
        return
    
    # 运行市场分析
    logging.info('开始市场分析...')
    signals = trading_system.analyze_market(market_data)
    
    # 输出分析结果
    logging.info('\n=== 市场分析结果 ===')
    logging.info(f'动量信号: {signals.get("momentum", "N/A")}')
    logging.info(f'强势板块: {signals.get("strong_sectors", "N/A")}')
    logging.info(f'领头羊股票: {signals.get("leading_stocks", "N/A")}')
    logging.info(f'逻辑得分: {signals.get("logic_score", "N/A")}')
    logging.info('==================\n')

if __name__ == '__main__':
    main()