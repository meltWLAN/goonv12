#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Tushare Token权限和可用接口
使用给定的Tushare token测试可用的所有接口和参数
"""

import tushare as ts
import pandas as pd
import json
import os
import time
import sys
from datetime import datetime

# 配置
TOKEN = "0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10"
CACHE_DIR = "./tushare_api_cache"
REPORT_FILE = "tushare_api_report.md"

def init_tushare():
    """初始化Tushare API"""
    ts.set_token(TOKEN)
    pro = ts.pro_api()
    return pro

def get_token_info(pro):
    """获取Token信息"""
    try:
        # 使用非公开接口获取token信息
        conn = pro._session
        resp = conn.get("https://api.tushare.pro/user/getusage")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                return data.get('data')
        
        print("无法获取token信息，使用替代方法...")
        # 替代方法
        basic_stocks = pro.stock_basic(exchange='', list_status='L')
        remaining_points = pro._token_limit - pro._token_used
        
        return {
            "points_used": pro._token_used,
            "points_remaining": remaining_points,
            "points_limit": pro._token_limit,
            "vip_level": "Unknown",
            "test_succeed": basic_stocks is not None and not basic_stocks.empty
        }
    except Exception as e:
        print(f"获取Token信息失败: {e}")
        return None

def get_api_endpoints(pro):
    """获取所有可用的API端点"""
    try:
        # 使用内部变量获取所有接口名称
        endpoints = list(pro._api_instance.__dict__.keys())
        # 过滤掉内部方法
        endpoints = [e for e in endpoints if not e.startswith('_')]
        return sorted(endpoints)
    except Exception as e:
        print(f"获取API端点列表失败: {e}")
        # 备用方案：返回常用接口列表
        return [
            'stock_basic', 'daily', 'weekly', 'monthly', 
            'stk_factor', 'income', 'balancesheet', 
            'stk_holdernumber', 'trade_cal', 'namechange', 
            'hs_const', 'stock_company', 'new_share', 
            'index_basic', 'index_daily', 'index_weight', 
            'concept', 'concept_detail', 'moneyflow', 
            'suspend', 'express', 'dividend', 'fina_indicator',
            'shibor', 'limit_list', 'margin_detail', 
            'top10_holders', 'top10_floatholders',
            'fund_basic', 'fund_nav', 'fund_div',
            'index_dailybasic', 'index_classify', 'fx_daily'
        ]

def test_endpoint(pro, endpoint):
    """测试单个API端点"""
    try:
        api_method = getattr(pro, endpoint)
        
        # 常用的通用参数
        common_params = {
            'stock_basic': {'exchange': '', 'list_status': 'L'},
            'daily': {'ts_code': '000001.SZ', 'start_date': '20250401', 'end_date': '20250430'},
            'weekly': {'ts_code': '000001.SZ', 'start_date': '20250401', 'end_date': '20250430'},
            'income': {'ts_code': '000001.SZ', 'period': '20250331'},
            'trade_cal': {'exchange': 'SSE', 'start_date': '20250401', 'end_date': '20250430'},
            'index_basic': {'market': 'SSE'},
            'concept': {},
            'fund_basic': {'market': 'E'},
            'fx_daily': {'ts_code': 'USDCNY.CFXT', 'start_date': '20250401', 'end_date': '20250430'},
        }
        
        # 尝试从通用参数中获取，或者使用空参数调用
        params = common_params.get(endpoint, {})
        
        print(f"测试接口 {endpoint}，参数: {params}")
        start_time = time.time()
        df = api_method(**params)
        end_time = time.time()
        
        success = df is not None and not df.empty
        
        result = {
            'name': endpoint,
            'success': success,
            'time': round(end_time - start_time, 2),
            'sample': df.head(3).to_dict('records') if success else None,
            'columns': list(df.columns) if success else None,
            'error': None,
            'row_count': len(df) if success else 0,
            'params_used': params
        }
        
        return result
    except Exception as e:
        return {
            'name': endpoint,
            'success': False,
            'time': 0,
            'sample': None,
            'columns': None,
            'error': str(e),
            'row_count': 0,
            'params_used': params if 'params' in locals() else {}
        }

def save_results(results, token_info):
    """保存API测试结果"""
    # 确保缓存目录存在
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 保存完整结果到JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join(CACHE_DIR, f"tushare_api_test_{timestamp}.json")
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({'results': results, 'token_info': token_info}, f, ensure_ascii=False, indent=2)
    
    print(f"完整测试结果已保存到: {json_file}")
    
    # 生成Markdown报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Tushare API 测试报告\n\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Token信息
        f.write("## Token 信息\n\n")
        if token_info:
            f.write(f"- Token: {TOKEN[:4]}{'*' * (len(TOKEN) - 8)}{TOKEN[-4:]}\n")
            f.write(f"- 积分使用情况: {token_info.get('points_used', 'Unknown')}/{token_info.get('points_limit', 'Unknown')}\n")
            f.write(f"- 剩余积分: {token_info.get('points_remaining', 'Unknown')}\n")
            f.write(f"- VIP级别: {token_info.get('vip_level', 'Unknown')}\n")
        else:
            f.write("无法获取Token信息\n")
        
        # 接口测试结果汇总
        success_count = sum(1 for r in results if r['success'])
        f.write(f"\n## 接口测试结果汇总\n\n")
        f.write(f"测试接口总数: {len(results)}\n")
        f.write(f"成功: {success_count}\n")
        f.write(f"失败: {len(results) - success_count}\n\n")
        
        # 成功的接口列表
        f.write("### 可用接口\n\n")
        f.write("| 接口名称 | 参数 | 返回字段 | 行数 | 耗时(秒) |\n")
        f.write("|---------|------|----------|------|----------|\n")
        
        for result in sorted([r for r in results if r['success']], key=lambda x: x['name']):
            params_str = ", ".join(f"{k}={v}" for k, v in result['params_used'].items())
            columns_count = len(result['columns']) if result['columns'] else 0
            f.write(f"| {result['name']} | {params_str} | {columns_count} | {result['row_count']} | {result['time']} |\n")
        
        # 失败的接口列表
        failed_results = [r for r in results if not r['success']]
        if failed_results:
            f.write("\n### 不可用接口\n\n")
            f.write("| 接口名称 | 错误信息 |\n")
            f.write("|---------|----------|\n")
            
            for result in sorted(failed_results, key=lambda x: x['name']):
                error_msg = result['error'] if result['error'] else "Unknown error"
                error_msg = error_msg.replace("\n", " ").replace("|", "\\|")
                f.write(f"| {result['name']} | {error_msg} |\n")
        
        # 样本数据
        f.write("\n## 样本数据\n\n")
        for result in sorted([r for r in results if r['success']], key=lambda x: x['name']):
            f.write(f"### {result['name']}\n\n")
            
            if result['columns']:
                f.write("**字段列表:**\n\n")
                f.write("```\n")
                f.write(", ".join(result['columns']))
                f.write("\n```\n\n")
            
            if result['sample']:
                f.write("**样本数据:**\n\n")
                f.write("```json\n")
                f.write(json.dumps(result['sample'], ensure_ascii=False, indent=2))
                f.write("\n```\n\n")
    
    print(f"测试报告已生成: {REPORT_FILE}")

def main():
    print(f"开始测试Tushare token: {TOKEN[:4]}{'*' * (len(TOKEN) - 8)}{TOKEN[-4:]}")
    
    # 初始化Tushare API
    try:
        pro = init_tushare()
        print("Tushare API 初始化成功")
    except Exception as e:
        print(f"Tushare API 初始化失败: {e}")
        return 1
    
    # 获取Token信息
    token_info = get_token_info(pro)
    if token_info:
        print(f"Token 有效，积分使用情况: {token_info.get('points_used', 'Unknown')}/{token_info.get('points_limit', 'Unknown')}")
    else:
        print("警告: 无法获取Token信息，但将继续测试API")
    
    # 获取所有API端点
    endpoints = get_api_endpoints(pro)
    print(f"发现 {len(endpoints)} 个API端点")
    
    # 测试所有端点
    results = []
    for i, endpoint in enumerate(endpoints, 1):
        print(f"[{i}/{len(endpoints)}] 测试接口: {endpoint}")
        result = test_endpoint(pro, endpoint)
        if result['success']:
            print(f"  成功 - 返回 {result['row_count']} 行数据，包含 {len(result['columns'])} 个字段")
        else:
            print(f"  失败 - {result['error']}")
        results.append(result)
    
    # 保存测试结果
    save_results(results, token_info)
    
    # 输出摘要
    success_count = sum(1 for r in results if r['success'])
    print(f"\n测试完成，成功率: {success_count}/{len(results)}")
    print(f"详细结果请查看: {REPORT_FILE}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 