#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Tushare股票行业相关API
"""

import sys
import time
from datetime import datetime, timedelta

def test_tushare_api():
    """测试Tushare的股票行业相关API"""
    try:
        print("正在测试Tushare API...")
        
        # 导入tushare
        try:
            import tushare as ts
            print(f"成功导入Tushare，版本: {ts.__version__}")
        except ImportError:
            print("错误: 未安装Tushare。请运行 './install_deps.sh' 安装依赖")
            return False
            
        # 设置token
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        ts.set_token(token)
        pro = ts.pro_api()
        print(f"成功设置Tushare token")
        
        # 测试获取行业列表
        try:
            start_time = time.time()
            print("正在获取申万行业列表...")
            industry_list = pro.index_classify(level='L1', src='SW')
            end_time = time.time()
            
            if industry_list is not None and not industry_list.empty:
                print(f"成功获取申万行业列表，共 {len(industry_list)} 个行业")
                print(f"请求耗时: {end_time - start_time:.2f} 秒")
                print("\n前5个行业:")
                print(industry_list.head())
            else:
                print("错误: 获取行业列表返回空数据")
                return False
        except Exception as e:
            print(f"错误: 获取行业列表失败: {str(e)}")
            return False
            
        # 测试获取行业历史数据
        if not industry_list.empty:
            # 选择第一个行业进行测试
            test_industry = industry_list.iloc[0]
            test_industry_code = test_industry['index_code']
            test_industry_name = test_industry['industry_name']
            print(f"\n正在获取行业 '{test_industry_name}' 的历史数据...")
            
            try:
                # 设置开始日期为90天前
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
                end_date = datetime.now().strftime('%Y%m%d')
                
                start_time = time.time()
                industry_hist = pro.index_daily(
                    ts_code=test_industry_code,
                    start_date=start_date,
                    end_date=end_date
                )
                end_time = time.time()
                
                if industry_hist is not None and not industry_hist.empty:
                    print(f"成功获取行业历史数据，共 {len(industry_hist)} 条记录")
                    print(f"请求耗时: {end_time - start_time:.2f} 秒")
                    print("\n前5条历史数据:")
                    print(industry_hist.head())
                    
                    # 查看列名
                    print("\n数据包含以下列:")
                    for col in industry_hist.columns:
                        print(f"- {col}")
                        
                    return True
                else:
                    print("错误: 获取行业历史数据返回空数据")
                    return False
            except Exception as e:
                print(f"错误: 获取行业历史数据失败: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("====== 测试Tushare股票行业API ======\n")
    
    success = test_tushare_api()
    
    print("\n====== 测试结果 ======")
    if success:
        print("✅ 测试通过! Tushare股票行业API可用")
    else:
        print("❌ 测试失败! 请检查错误信息并解决问题")
    
    sys.exit(0 if success else 1) 