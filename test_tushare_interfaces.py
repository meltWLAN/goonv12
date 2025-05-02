import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

def test_tushare_interfaces():
    """测试Tushare各个接口的可用性"""
    
    # 设置Tushare token
    token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    print(f"正在使用Token: {token}")
    ts.set_token(token)
    
    try:
        pro = ts.pro_api()
        print("Tushare API初始化成功")
    except Exception as e:
        print(f"Tushare API初始化失败: {str(e)}")
        sys.exit(1)
    
    # 设置日期范围
    today = datetime.now()
    end_date = today.strftime('%Y%m%d')
    start_date = (today - timedelta(days=30)).strftime('%Y%m%d')
    
    print(f"\n测试时间范围: {start_date} 至 {end_date}")
    
    # 测试基础行情接口
    interfaces = [
        {"name": "股票日线数据", "func": lambda: pro.daily(ts_code='000001.SZ', start_date=start_date, end_date=end_date)},
        {"name": "股票周线数据", "func": lambda: pro.weekly(ts_code='000001.SZ', start_date=start_date, end_date=end_date)},
        {"name": "股票月线数据", "func": lambda: pro.monthly(ts_code='000001.SZ', start_date=start_date, end_date=end_date)},
        {"name": "股票列表", "func": lambda: pro.stock_basic(exchange='', list_status='L')},
        {"name": "指数日线数据", "func": lambda: pro.index_daily(ts_code='000001.SH', start_date=start_date, end_date=end_date)},
        {"name": "指数成分", "func": lambda: pro.index_weight(index_code='000001.SH', start_date=start_date, end_date=end_date)},
        {"name": "概念股列表", "func": lambda: pro.concept()},
        {"name": "概念成分", "func": lambda: pro.concept_detail(id='TS2')},
    ]
    
    # 测试财务数据接口
    financial_interfaces = [
        {"name": "利润表", "func": lambda: pro.income(ts_code='000001.SZ', period='20201231')},
        {"name": "资产负债表", "func": lambda: pro.balancesheet(ts_code='000001.SZ', period='20201231')},
        {"name": "现金流量表", "func": lambda: pro.cashflow(ts_code='000001.SZ', period='20201231')},
        {"name": "业绩快报", "func": lambda: pro.express(ts_code='000001.SZ', period='20211231')},
    ]
    
    # 测试市场数据接口
    market_interfaces = [
        {"name": "融资融券", "func": lambda: pro.margin(ts_code='000001.SZ', start_date=start_date, end_date=end_date)},
        {"name": "龙虎榜", "func": lambda: pro.top_list(trade_date=(datetime.now() - timedelta(days=60)).strftime('%Y%m%d'))},
        {"name": "每日指标", "func": lambda: pro.daily_basic(ts_code='000001.SZ', start_date=start_date, end_date=end_date)},
        {"name": "复权因子", "func": lambda: pro.adj_factor(ts_code='000001.SZ', start_date=start_date, end_date=end_date)},
    ]
    
    # 测试公司信息接口
    company_interfaces = [
        {"name": "公司基本信息", "func": lambda: pro.stock_company(ts_code='000001.SZ')},
        {"name": "股东人数", "func": lambda: pro.stk_holdernumber(ts_code='000001.SZ')},
        {"name": "股东增减持", "func": lambda: pro.stk_holdertrade(ts_code='000001.SZ')},
        {"name": "机构调研", "func": lambda: pro.stk_surv(ts_code='000001.SZ')},
    ]
    
    # 合并所有接口组
    all_interfaces = interfaces + financial_interfaces + market_interfaces + company_interfaces
    
    # 测试所有接口
    success_count = 0
    failed_interfaces = []
    
    for i, interface in enumerate(all_interfaces, 1):
        name = interface["name"]
        func = interface["func"]
        
        print(f"\n{i}/{len(all_interfaces)} 测试接口: {name}")
        try:
            start_time = time.time()
            df = func()
            end_time = time.time()
            
            if df is not None and not df.empty:
                row_count = len(df)
                col_count = len(df.columns)
                print(f"✓ 接口调用成功，获取到 {row_count} 行 {col_count} 列的数据")
                print(f"  接口调用耗时: {(end_time - start_time):.2f}秒")
                print(f"  数据首行: {df.iloc[0].to_dict() if row_count > 0 else '无数据'}")
                success_count += 1
            else:
                print(f"! 接口调用成功，但未返回数据")
                failed_interfaces.append({"name": name, "error": "无数据"})
        except Exception as e:
            print(f"✗ 接口调用失败: {str(e)}")
            failed_interfaces.append({"name": name, "error": str(e)})
        
        # 避免请求过快被限流
        time.sleep(1)
    
    # 输出测试总结
    print("\n" + "=" * 50)
    print(f"测试完成! 总共测试 {len(all_interfaces)} 个接口")
    print(f"成功: {success_count}")
    print(f"失败: {len(failed_interfaces)}")
    
    if failed_interfaces:
        print("\n失败的接口:")
        for i, interface in enumerate(failed_interfaces, 1):
            print(f"{i}. {interface['name']}: {interface['error']}")
    
    # 返回总体结果
    return {
        "total": len(all_interfaces),
        "success": success_count,
        "failed": len(failed_interfaces),
        "failed_interfaces": failed_interfaces,
    }

if __name__ == "__main__":
    print("开始测试Tushare接口...\n")
    results = test_tushare_interfaces()
    print("\n测试结果总结:")
    print(f"接口总数: {results['total']}")
    print(f"成功数量: {results['success']}")
    print(f"成功率: {(results['success'] / results['total'] * 100):.2f}%") 