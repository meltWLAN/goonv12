import tushare as ts
import pandas as pd
import argparse
import sys
import os
import json
import time
from datetime import datetime, timedelta

def get_cache_path(cache_dir, endpoint, **params):
    """生成缓存文件路径"""
    # 从参数创建缓存键
    params_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()) if k not in ['fields'])
    filename = f"{endpoint}_{params_str}.json"
    # 替换无效字符
    filename = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
    return os.path.join(cache_dir, filename)

def is_cache_valid(cache_path, expire_hours=24):
    """检查缓存是否有效"""
    if not os.path.exists(cache_path):
        return False
        
    # 检查文件修改时间
    file_mtime = os.path.getmtime(cache_path)
    cache_age = time.time() - file_mtime
    
    # 默认缓存有效期为24小时
    cache_duration = expire_hours * 3600
    
    return cache_age < cache_duration

def load_from_cache(cache_path):
    """从缓存加载数据"""
    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
        
        # 转换回DataFrame
        if data:
            df = pd.DataFrame(data)
            print(f"从缓存加载了 {len(df)} 行数据: {cache_path}")
            return df
    except Exception as e:
        print(f"加载缓存失败: {e}")
    
    return None

def save_to_cache(cache_path, df):
    """保存数据到缓存"""
    if df is None or df.empty:
        print("没有数据可缓存")
        return
        
    try:
        # 将DataFrame转换为字典列表以进行JSON序列化
        data = df.to_dict('records')
        with open(cache_path, 'w') as f:
            json.dump(data, f)
        
        print(f"缓存了 {len(df)} 行数据到: {cache_path}")
    except Exception as e:
        print(f"缓存数据失败: {e}")

def call_api(pro, endpoint, use_cache=True, cache_dir='./data_cache', **params):
    """调用Tushare API，支持缓存"""
    # 处理缓存
    cache_path = None
    if use_cache:
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_path = get_cache_path(cache_dir, endpoint, **params)
        if is_cache_valid(cache_path):
            cached_data = load_from_cache(cache_path)
            if cached_data is not None:
                print(f"使用 {endpoint} 的缓存数据")
                return cached_data
    
    # 调用API
    try:
        print(f"调用Tushare API: {endpoint}，参数: {params}")
        api_method = getattr(pro, endpoint)
        df = api_method(**params)
        
        # 如果需要，缓存结果
        if use_cache and cache_path and df is not None and not df.empty:
            save_to_cache(cache_path, df)
            
        return df
    except AttributeError:
        print(f"错误: Tushare没有提供'{endpoint}'接口")
        return None
    except Exception as e:
        print(f"API调用失败: {endpoint}，错误: {str(e)}")
        return None

def display_data_summary(df, data_type):
    """显示数据摘要"""
    if df is None or df.empty:
        print(f"没有返回数据。可能指定的参数下没有数据。")
        return
    
    print("\n数据获取成功:")
    print(f"形状: {df.shape} (行数, 列数)")
    
    print("\n列名:")
    for col in df.columns:
        print(f"  - {col}")
    
    print("\n数据示例 (前5行):")
    pd.set_option('display.max_columns', 10)  # 限制显示的列数
    pd.set_option('display.width', 1000)      # 设置显示宽度
    print(df.head())
    
    if 'trade_date' in df.columns:
        print(f"\n日期范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")
    
    # 对特定类型的数据提供额外信息
    if data_type == 'stk_factor':
        if 'close' in df.columns:
            print(f"\n收盘价统计:")
            print(df['close'].describe())
        
        factor_cols = [col for col in df.columns if col in ['macd', 'pe', 'pb', 'rsi_6', 'rsi_12']]
        if factor_cols:
            print(f"\n主要因子统计:")
            print(df[factor_cols].describe())

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试Tushare API')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--ts_code', type=str, default='000001.SZ', help='股票代码 (默认: 000001.SZ)')
    parser.add_argument('--start_date', type=str, help='开始日期 (格式: YYYYMMDD)')
    parser.add_argument('--end_date', type=str, help='结束日期 (格式: YYYYMMDD)')
    parser.add_argument('--data_type', type=str, default='stk_factor', 
                        choices=['stk_factor', 'daily', 'weekly', 'monthly', 'stock_basic', 
                                'income', 'balancesheet', 'stk_holdernumber'],
                        help='数据类型 (默认: stk_factor)')
    parser.add_argument('--use_cache', action='store_true', help='使用缓存')
    parser.add_argument('--cache_dir', type=str, default='./data_cache', help='缓存目录')
    
    args = parser.parse_args()
    
    # 设置默认日期
    if not args.start_date:
        args.start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    if not args.end_date:
        args.end_date = datetime.now().strftime('%Y%m%d')
    
    try:
        # 设置Tushare API连接
        ts.set_token(args.token)
        pro = ts.pro_api()
        print(f"API连接已初始化，token: {args.token[:4]}{'*' * (len(args.token) - 8)}{args.token[-4:]}")
        
        # 准备参数
        params = {
            'ts_code': args.ts_code,
            'start_date': args.start_date,
            'end_date': args.end_date
        }
        
        # 根据数据类型调整参数
        if args.data_type == 'stock_basic':
            # 股票基本信息不需要日期参数
            params = {'ts_code': args.ts_code} if args.ts_code != 'all' else {}
        elif args.data_type in ['income', 'balancesheet']:
            # 财务数据使用period而不是日期范围
            period = args.end_date[:6] if args.end_date else datetime.now().strftime('%Y%m')
            params = {'ts_code': args.ts_code, 'period': period}
        elif args.data_type == 'stk_holdernumber':
            # 股东数量数据需要ts_code
            params = {'ts_code': args.ts_code}
            # 可以添加日期参数（如果提供）
            if args.start_date:
                params['start_date'] = args.start_date
            if args.end_date:
                params['end_date'] = args.end_date
        
        print(f"获取{args.data_type}数据，参数: {params}...")
        
        # 调用API
        df = call_api(pro, args.data_type, use_cache=args.use_cache, cache_dir=args.cache_dir, **params)
        
        # 显示数据
        display_data_summary(df, args.data_type)
        
        # 导出数据（可选）
        if df is not None and not df.empty:
            export_path = f"{args.ts_code}_{args.data_type}_{args.start_date}_{args.end_date}.csv"
            df.to_csv(export_path, index=False)
            print(f"\n数据已导出到: {export_path}")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 