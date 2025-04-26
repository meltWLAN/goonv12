import pandas as pd
import akshare as ak
from visual_stock_system import VisualStockSystem
from datetime import datetime
from tqdm import tqdm

def get_all_stocks():
    """获取沪深两市所有股票，增加错误处理和重试机制"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 获取股票列表
            try:
                stocks = ak.stock_info_a_code_name()
                
                # 验证数据有效性
                if stocks is None or stocks.empty:
                    raise ValueError("获取股票列表失败，返回空数据")
                    
                # 标准化列名 - 处理可能的列名差异
                if '代码' in stocks.columns and '名称' in stocks.columns:
                    stocks = stocks.rename(columns={
                        '代码': 'symbol',
                        '名称': 'name'
                    })
                elif 'code' in stocks.columns and 'name' in stocks.columns:
                    stocks = stocks.rename(columns={
                        'code': 'symbol',
                        'name': 'name'
                    })
                else:
                    # 尝试其他可能的列名组合
                    columns = stocks.columns.tolist()
                    if len(columns) >= 2:
                        # 假设第一列是代码，第二列是名称
                        stocks = stocks.rename(columns={
                            columns[0]: 'symbol',
                            columns[1]: 'name'
                        })
                    else:
                        raise ValueError(f"无法识别股票数据列: {columns}")
            except Exception as e:
                print(f"通过AKShare获取股票列表失败: {str(e)}，尝试备选方案...")
                # 尝试通过tushare获取股票列表
                import tushare as ts
                ts.set_token('0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10')
                pro = ts.pro_api()
                stocks = pro.stock_basic(exchange='', list_status='L', 
                                        fields='ts_code,symbol,name,area,industry,market,list_date')
                
                # 确保symbol列存在
                if 'ts_code' in stocks.columns and 'symbol' not in stocks.columns:
                    # 如果已有ts_code列但没有symbol列，从ts_code提取
                    stocks['symbol'] = stocks['ts_code'].apply(lambda x: x.split('.')[0])
                    
                # 验证数据有效性
                if stocks is None or stocks.empty:
                    raise ValueError("通过tushare获取股票列表也失败")
            
            # 确保ts_code列存在
            if 'ts_code' not in stocks.columns:
                # 添加交易所后缀
                def add_exchange_suffix(code):
                    if code.startswith(('600', '601', '603', '605', '688')):
                        return code + '.SH'
                    elif code.startswith(('000', '001', '002', '003', '300', '301')):
                        return code + '.SZ'
                    elif code.startswith(('430', '83', '87', '82')):
                        return code + '.BJ'  # 北交所
                    else:
                        return code + '.SZ'  # 默认深交所
                
                stocks['ts_code'] = stocks['symbol'].apply(add_exchange_suffix)
            
            # 确保必要的列都存在
            required_columns = ['symbol', 'name', 'ts_code']
            for col in required_columns:
                if col not in stocks.columns:
                    raise ValueError(f"获取的股票数据缺少{col}列")
            
            # 过滤掉ST股票和退市股票
            stocks = stocks[~stocks['name'].str.contains('ST|退', na=False)]
            
            print(f"成功获取 {len(stocks)} 只股票信息")
            return stocks
            
        except Exception as e:
            retry_count += 1
            print(f"获取股票列表失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                print("3秒后重试...")
                import time
                time.sleep(3)
    
    # 所有重试都失败后，创建一个简单的测试列表以便测试其他功能
    print("无法获取股票列表，创建测试数据...")
    test_stocks = pd.DataFrame({
        'symbol': ['000001', '600000', '600036', '000651', '300750'],
        'name': ['平安银行', '浦发银行', '招商银行', '格力电器', '宁德时代'],
        'ts_code': ['000001.SZ', '600000.SH', '600036.SH', '000651.SZ', '300750.SZ']
    })
    print("使用测试数据继续...")
    return test_stocks

def filter_stocks(system, stocks, top_n=10, filter_params=None):
    """筛选最符合条件的股票
    
    Args:
        system: 股票分析系统实例
        stocks: 股票列表DataFrame
        top_n: 返回的股票数量
        filter_params: 筛选参数字典，可自定义筛选条件
        
    Returns:
        筛选后的股票列表
    """
    if filter_params is None:
        filter_params = {
            'min_price': 5.0,       # 最低价格
            'max_price': 200.0,     # 最高价格
            'min_volume_ratio': 0.8, # 最小成交量比率
            'min_market_cap': 5e9,  # 最小市值(50亿)
            'max_market_cap': 1e11, # 最大市值(1000亿)
            'min_net_profit_growth': 5.0,  # 最小扣非净利润增长率
            'min_roe': 8.0,         # 最小净资产收益率
            'min_gross_margin': 15.0, # 最小毛利率
            'exclude_industries': ['银行', '保险'] # 排除的行业
        }
    
    print(f"\n开始分析 {len(stocks)} 只股票...")
    print(f"筛选条件: 价格({filter_params['min_price']}-{filter_params['max_price']}元), 市值({filter_params['min_market_cap']/1e9:.1f}亿-{filter_params['max_market_cap']/1e9:.1f}亿元)")
    print(f"财务指标要求: 净利润增长>{filter_params['min_net_profit_growth']}%, ROE>{filter_params['min_roe']}%, 毛利率>{filter_params['min_gross_margin']}%")
    print("-" * 50)
    
    # 使用批处理方式处理大量股票，避免一次性请求过多
    batch_size = 50
    all_recommendations = []
    total_batches = (len(stocks) + batch_size - 1) // batch_size
    
    print(f"\n开始分批处理，共 {total_batches} 个批次，每批 {batch_size} 只股票")
    
    with tqdm(total=len(stocks), desc="分析进度", ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        for i in range(0, len(stocks), batch_size):
            batch = stocks['ts_code'].tolist()[i:i+batch_size]
            batch_start = i + 1
            batch_end = min(i+batch_size, len(stocks))
            batch_num = i // batch_size + 1
            
            try:
                # 显示当前批次中的部分股票名称
                sample_stocks = stocks.iloc[i:i+min(5, len(batch))]
                # 确保'name'列存在
                if 'name' in sample_stocks.columns:
                    sample_names = [f"{code}({name})" for code, name in zip(sample_stocks['ts_code'], sample_stocks['name'])]
                    print(f"\n批次 {batch_num}/{total_batches} 包含: {', '.join(sample_names)}...")
                else:
                    # 如果没有名称列，只显示代码
                    print(f"\n批次 {batch_num}/{total_batches} 包含: {', '.join(sample_stocks['ts_code'].tolist())}...")
                
                # 显示批次进度百分比
                batch_percent = round(batch_num / total_batches * 100)
                pbar.set_description(f"分析进度 ({batch_percent}%)")
                
                batch_recommendations = system.scan_stocks(batch)
                if batch_recommendations:
                    all_recommendations.extend(batch_recommendations)
                pbar.update(len(batch))
                pbar.set_postfix({"批次": f"{batch_num}/{total_batches}", "处理": f"{batch_start}-{batch_end}", "发现": len(all_recommendations)})
            except Exception as e:
                print(f"\n分析批次 {batch_num}/{total_batches} 时出错: {str(e)}")
                pbar.update(len(batch))
    
    print(f"\n分析完成! 初步发现 {len(all_recommendations)} 只潜在股票")
    
    # 应用初步筛选条件
    filtered_recommendations = []
    for rec in all_recommendations:
        try:
            # 跳过数据不完整的股票
            if not all(k in rec for k in ['symbol', 'price', 'trend', 'volume', 'volume_ma20', 'macd_hist', 'atr', 'market_cap', 'net_profit_growth', 'roe', 'gross_margin']):
                continue
                
            # 应用价格筛选
            if not (filter_params['min_price'] <= rec['price'] <= filter_params['max_price']):
                continue
                
            # 应用市值筛选
            if not (filter_params['min_market_cap'] <= rec['market_cap'] <= filter_params['max_market_cap']):
                continue
                
            # 应用财务指标筛选
            if rec['net_profit_growth'] < filter_params['min_net_profit_growth']:
                continue
            if rec['roe'] < filter_params['min_roe']:
                continue
            if rec['gross_margin'] < filter_params['min_gross_margin']:
                continue
                
            # 应用成交量筛选
            volume_ratio = rec['volume'] / rec['volume_ma20'] if rec['volume_ma20'] > 0 else 0
            if volume_ratio < filter_params['min_volume_ratio']:
                continue
                
            # 添加到筛选结果
            filtered_recommendations.append(rec)
        except Exception as e:
            print(f"筛选股票 {rec.get('symbol', 'unknown')} 时出错: {str(e)}")
    
    print(f"初步筛选后剩余 {len(filtered_recommendations)} 只股票")
    
    # 如果筛选后股票数量不足，放宽条件
    if len(filtered_recommendations) < top_n:
        print("筛选结果不足，放宽条件重新筛选...")
        # 添加递归深度控制，防止无限递归
        if filter_params.get('recursion_depth', 0) >= 3:
            print("已达到最大递归深度，返回当前筛选结果...")
            return sorted(filtered_recommendations, key=lambda x: x.get('total_score', 0), reverse=True)
            
        # 放宽条件时保持数值有效性
        new_params = {
            'min_price': max(0.1, filter_params['min_price'] * 0.8),
            'max_price': min(10000, filter_params['max_price'] * 1.2),
            'min_volume_ratio': max(0.1, filter_params['min_volume_ratio'] * 0.7),
            'min_market_cap': max(1e8, filter_params['min_market_cap'] * 0.8),
            'max_market_cap': min(1e12, filter_params['max_market_cap'] * 1.2),
            'min_net_profit_growth': max(0, filter_params['min_net_profit_growth'] * 0.8),
            'min_roe': max(0, filter_params['min_roe'] * 0.8),
            'min_gross_margin': max(0, filter_params['min_gross_margin'] * 0.8),
            'exclude_industries': [],
            'recursion_depth': filter_params.get('recursion_depth', 0) + 1
        }
        return filter_stocks(system, stocks, top_n, new_params)
    
    # 综合评分排序
    for rec in filtered_recommendations:
        # 计算综合评分
        trend_score = 5 if rec['trend'] == 'uptrend' else 3 if rec['trend'] == 'sideways' else 1
        macd_score = min(5, abs(rec['macd_hist']) * 10)
        volume_score = min(5, (rec['volume'] / rec['volume_ma20']) * 2) if rec['volume_ma20'] > 0 else 0
        volatility_score = min(5, rec['atr'] * 5) if 'atr' in rec else 0
        
        # 综合评分 (各指标权重可调整)
        rec['total_score'] = trend_score * 0.4 + macd_score * 0.3 + volume_score * 0.2 + volatility_score * 0.1
    
    # 按综合评分排序
    sorted_recommendations = sorted(filtered_recommendations, key=lambda x: x.get('total_score', 0), reverse=True)
    
    # 打印过滤结果统计
    print("\n" + "="*50)
    print(f"筛选结果统计:")
    print(f"初步分析: {len(all_recommendations)} 只股票")
    print(f"通过筛选: {len(filtered_recommendations)} 只股票")
    print(f"最终推荐: {min(top_n, len(sorted_recommendations))} 只股票")
    print("="*50)
    
    # 返回前N只股票
    return sorted_recommendations[:top_n]

def main():
    try:
        # 创建可视化股票系统实例
        print("初始化股票分析系统...")
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'  # 可以从配置文件读取
        system = VisualStockSystem(token)
        
        # 获取当前日期
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"今日日期: {today}")
        
        # 获取所有股票
        print("\n获取股票列表...")
        stocks = get_all_stocks()
        if stocks.empty:
            print("无法获取股票列表，程序终止")
            return
            
        print(f"共获取到 {len(stocks)} 只股票")
        
        # 筛选出最符合条件的股票
        print("\n开始筛选股票...")
        top_n = 15  # 增加推荐数量
        top_stocks = filter_stocks(system, stocks, top_n)
        
        if not top_stocks:
            print("未找到符合条件的股票，请调整筛选参数")
            return
        
        # 打印推荐结果
        print("\n===== 今日推荐股票 =====")
        system.print_recommendations(top_stocks)
        
        # 保存推荐结果到文件
        result_file = f"stock_recommendations_{today}.csv"
        try:
            pd.DataFrame(top_stocks).to_csv(result_file, index=False, encoding='utf-8-sig')
            print(f"\n推荐结果已保存到 {result_file}")
        except Exception as e:
            print(f"保存推荐结果失败: {str(e)}")
        
        # 为每只推荐的股票生成可视化分析
        print("\n生成可视化分析...")
        for rec in top_stocks:
            try:
                system.plot_stock_analysis(rec['symbol'])
            except Exception as e:
                print(f"生成 {rec['symbol']} 的可视化分析失败: {str(e)}")
                
        print("\n股票筛选分析完成!")
        
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()