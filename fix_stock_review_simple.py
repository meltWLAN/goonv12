#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版修复复盘池展示问题脚本
"""

import os
import json
from datetime import datetime

# 文件路径
BASIC_REVIEW_FILE = 'review_pool.json'
ENHANCED_REVIEW_FILE = 'enhanced_review_pool.json'
SMART_REVIEW_DIR = './smart_review_data'
SMART_REVIEW_FILE = os.path.join(SMART_REVIEW_DIR, 'smart_review_pool.json')

# 创建智能复盘池目录
os.makedirs(SMART_REVIEW_DIR, exist_ok=True)

# 示例股票数据
DEMO_STOCKS = [
    {"symbol": "000001.SZ", "name": "平安银行", "recommendation": "强烈推荐买入", "score": 92, "market_status": "上涨趋势"},
    {"symbol": "600519.SH", "name": "贵州茅台", "recommendation": "强烈推荐买入", "score": 95, "market_status": "强势整理"},
    {"symbol": "000858.SZ", "name": "五粮液", "recommendation": "强烈推荐买入", "score": 91, "market_status": "上涨趋势"},
    {"symbol": "600036.SH", "name": "招商银行", "recommendation": "强烈推荐买入", "score": 89, "market_status": "上涨趋势"},
    {"symbol": "601318.SH", "name": "中国平安", "recommendation": "强烈推荐买入", "score": 90, "market_status": "突破上涨"},
    {"symbol": "600276.SH", "name": "恒瑞医药", "recommendation": "强烈推荐买入", "score": 88, "market_status": "强势整理"},
    {"symbol": "000333.SZ", "name": "美的集团", "recommendation": "强烈推荐买入", "score": 87, "market_status": "上涨趋势"},
    {"symbol": "601888.SH", "name": "中国中免", "recommendation": "强烈推荐买入", "score": 86, "market_status": "强势整理"},
    {"symbol": "600887.SH", "name": "伊利股份", "recommendation": "强烈推荐买入", "score": 85, "market_status": "上涨趋势"},
    {"symbol": "601166.SH", "name": "兴业银行", "recommendation": "强烈推荐买入", "score": 84, "market_status": "突破上涨"}
]

def load_json_file(filename, default_value):
    """加载JSON文件，如果失败则返回默认值"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 {filename} 失败: {str(e)}")
    return default_value

def save_json_file(filename, data):
    """保存JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"已保存数据到 {filename}")
        return True
    except Exception as e:
        print(f"保存 {filename} 失败: {str(e)}")
        return False

def fix_review_pools():
    """修复所有复盘池"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 加载所有复盘池数据
    basic_review = load_json_file(BASIC_REVIEW_FILE, {'stocks': [], 'last_updated': today})
    enhanced_review = load_json_file(ENHANCED_REVIEW_FILE, {'stocks': [], 'settings': {
        'auto_update': True, 
        'notification': True,
        'data_source': 'tushare',
        'created_at': today,
        'last_updated': today
    }})
    smart_review = load_json_file(SMART_REVIEW_FILE, {'stocks': [], 'created_at': today, 'last_updated': today, 'version': '2.0'})
    
    # 确保复盘池有数据 - 添加示例股票
    if not basic_review.get('stocks'):
        basic_stocks = []
        for stock in DEMO_STOCKS:
            basic_stocks.append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'date_added': today,
                'status': 'watching',
                'buy_price': None,
                'sell_price': None,
                'buy_date': None,
                'sell_date': None,
                'profit_percent': None,
                'holding_days': None,
                'notes': '',
                'source': '演示数据',
                'analysis_score': stock.get('score', 0),
                'market_status': stock.get('market_status', ''),
                'recommendation': stock.get('recommendation', '')
            })
        basic_review['stocks'] = basic_stocks
        basic_review['last_updated'] = today
        print(f"已添加 {len(basic_stocks)} 只示例股票到基础复盘池")
    
    # 同步到增强版复盘池
    if not enhanced_review.get('stocks') and basic_review.get('stocks'):
        enhanced_review['stocks'] = basic_review['stocks']
        enhanced_review['settings']['last_updated'] = today
        print("已从基础复盘池同步股票数据到增强版复盘池")
    
    # 同步到智能复盘池
    if not smart_review.get('stocks') and basic_review.get('stocks'):
        smart_stocks = []
        for stock in basic_review['stocks']:
            smart_stocks.append({
                'symbol': stock.get('symbol'),
                'name': stock.get('name'),
                'date_added': stock.get('date_added', today),
                'status': stock.get('status', 'watching'),
                'analysis': {},
                'trade_history': [],
                'notes': stock.get('notes', ''),
                'tags': ['推荐', '强烈买入'],
                'importance': 5,
                'smart_score': stock.get('analysis_score', 0)
            })
        smart_review['stocks'] = smart_stocks
        smart_review['last_updated'] = today
        print("已从基础复盘池同步股票数据到智能复盘池")
    
    # 保存所有复盘池数据
    save_json_file(BASIC_REVIEW_FILE, basic_review)
    save_json_file(ENHANCED_REVIEW_FILE, enhanced_review)
    save_json_file(SMART_REVIEW_FILE, smart_review)
    
    # 打印统计信息
    print("\n===== 复盘池统计信息 =====")
    print(f"基础复盘池: {len(basic_review.get('stocks', []))}只股票")
    print(f"增强版复盘池: {len(enhanced_review.get('stocks', []))}只股票")
    print(f"智能复盘池: {len(smart_review.get('stocks', []))}只股票")
    
    return True

if __name__ == "__main__":
    print("开始修复复盘池展示问题...\n")
    fix_review_pools()
    print("\n修复完成！建议重新启动股票分析应用，然后查看复盘池中的股票。") 