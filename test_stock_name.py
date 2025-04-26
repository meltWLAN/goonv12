import akshare as ak
import time
import pytest
from single_stock_analyzer import SingleStockAnalyzer


@pytest.mark.parametrize('symbol', ['600519', '300750', '000001'])
def test_stock_name(symbol):
    analyzer = SingleStockAnalyzer()
    result = analyzer._update_stock_name({'status': 'success', 'data': {}}, symbol)
    assert isinstance(result['data'].get('name', ''), str)
    try:
        print(f"测试获取股票 {symbol} 的名称...")
        stock_code = symbol.split('.')[0] if '.' in symbol else symbol
        stock_info = ak.stock_individual_info_em(symbol=stock_code)
        print("获取到的股票信息:")
        print(stock_info)
        
        if not stock_info.empty and '名称' in stock_info.columns:
            name = stock_info.iloc[0]['名称']
            print(f"股票名称: {name}")
            print(f"股票名称类型: {type(name)}")
            print(f"股票名称编码: {name.encode()}")
            return name
        else:
            print("未获取到股票名称或数据为空")
            return None
    except Exception as e:
        print(f"获取股票名称时发生错误: {str(e)}")
        return None

# 测试几个不同的股票代码
test_stocks = ['000001', '600000', '300059']

for stock in test_stocks:
    name = test_stock_name(stock)
    print(f"股票 {stock} 的名称: {name}")
    print("-" * 50)
    time.sleep(1)  # 避免频繁请求