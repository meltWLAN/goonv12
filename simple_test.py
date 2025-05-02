import argparse
import logging
from china_stock_provider import ChinaStockProvider

def main():
    parser = argparse.ArgumentParser(description='Test the enhanced China Stock Provider')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--symbol', type=str, default='000001.SZ', help='Stock symbol to test with')
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('test')
    
    logger.info(f"Testing provider with symbol {args.symbol}")
    
    # Initialize provider
    provider = ChinaStockProvider(tushare_token=args.token)
    
    # Test stock data (correct data_type is 'stock', not 'daily')
    daily = provider.get_data('stock', args.symbol)
    if daily is not None and not daily.empty:
        logger.info(f"Successfully retrieved stock data: {len(daily)} rows")
        logger.info(f"Columns: {daily.columns.tolist()}")
        logger.info(f"Sample data:\n{daily.head(3)}")
    else:
        logger.error("Failed to retrieve stock data")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())