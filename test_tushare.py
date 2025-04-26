import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

def test_tushare_fetch():
    # 设置Tushare token
    token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 设置日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
    
    print(f"使用Tushare获取股票数据, 开始日期: {start_date}, 结束日期: {end_date}")
    
    # 测试一些不同的股票代码
    test_stocks = ['000001.SZ', '600000.SH', '002648.SZ', '300750.SZ', '688981.SH']
    
    for stock_code in test_stocks:
        try:
            print(f"\n测试股票: {stock_code}")
            
            # 方法1：使用daily接口
            df1 = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
            print(f"方法1 (daily接口): 获取到 {len(df1)} 条数据")
            if not df1.empty:
                print(f"最新日期: {df1['trade_date'].iloc[0]}")
            
            # 方法2：使用旧版接口
            df2 = ts.pro_bar(ts_code=stock_code, adj='qfq', start_date=start_date, end_date=end_date)
            print(f"方法2 (pro_bar接口): 获取到 {len(df2) if df2 is not None else 0} 条数据")
            if df2 is not None and not df2.empty:
                print(f"最新日期: {df2['trade_date'].iloc[0]}")
            
        except Exception as e:
            print(f"获取数据出错: {str(e)}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_tushare_fetch() 