#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接修复复盘池并显示结果
"""

import os
import json
from datetime import datetime

# 文件路径
BASIC_REVIEW_FILE = 'review_pool.json'
ENHANCED_REVIEW_FILE = 'enhanced_review_pool.json'
SMART_REVIEW_DIR = './smart_review_data'
SMART_REVIEW_FILE = os.path.join(SMART_REVIEW_DIR, 'smart_review_pool.json')

# 示例股票数据 - 强烈推荐买入的股票
DEMO_STOCKS = [
    {"symbol": "000001.SZ", "name": "平安银行", "recommendation": "强烈推荐买入", "score": 92, "market_status": "上涨趋势"},
    {"symbol": "600519.SH", "name": "贵州茅台", "recommendation": "强烈推荐买入", "score": 95, "market_status": "强势整理"},
    {"symbol": "000858.SZ", "name": "五粮液", "recommendation": "强烈推荐买入", "score": 91, "market_status": "上涨趋势"},
    {"symbol": "600036.SH", "name": "招商银行", "recommendation": "强烈推荐买入", "score": 89, "market_status": "上涨趋势"},
    {"symbol": "601318.SH", "name": "中国平安", "recommendation": "强烈推荐买入", "score": 90, "market_status": "突破上涨"},
    {"symbol": "600276.SH", "name": "恒瑞医药", "recommendation": "强烈推荐买入", "score": 88, "market_status": "强势整理"},
    {"symbol": "000333.SZ", "name": "美的集团", "recommendation": "强烈推荐买入", "score": 87, "market_status": "上涨趋势"},
    {"symbol": "601888.SH", "name": "中国中免", "recommendation": "强烈推荐买入", "score": 86, "market_status": "强势整理"}
]

def fix_and_display():
    """修复复盘池并显示结果"""
    # 创建智能复盘池目录
    os.makedirs(SMART_REVIEW_DIR, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. 修复基础复盘池
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
    
    basic_review = {
        'stocks': basic_stocks,
        'last_updated': today
    }
    
    # 2. 修复增强版复盘池
    enhanced_review = {
        'stocks': basic_stocks.copy(),
        'settings': {
            'auto_update': True,
            'notification': True,
            'data_source': 'tushare',
            'created_at': today,
            'last_updated': today
        }
    }
    
    # 3. 修复智能复盘池
    smart_stocks = []
    for stock in DEMO_STOCKS:
        smart_stocks.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'date_added': today,
            'status': 'watching',
            'analysis': {},
            'trade_history': [],
            'notes': '',
            'tags': ['推荐', '强烈买入'],
            'importance': 5,
            'smart_score': stock.get('score', 0)
        })
    
    smart_review = {
        'stocks': smart_stocks,
        'created_at': today,
        'last_updated': today,
        'version': '2.0'
    }
    
    # 保存所有复盘池数据
    with open(BASIC_REVIEW_FILE, 'w', encoding='utf-8') as f:
        json.dump(basic_review, f, ensure_ascii=False, indent=4)
    print(f"已保存基础复盘池 ({len(basic_stocks)}只股票)")
    
    with open(ENHANCED_REVIEW_FILE, 'w', encoding='utf-8') as f:
        json.dump(enhanced_review, f, ensure_ascii=False, indent=4)
    print(f"已保存增强版复盘池 ({len(basic_stocks)}只股票)")
    
    with open(SMART_REVIEW_FILE, 'w', encoding='utf-8') as f:
        json.dump(smart_review, f, ensure_ascii=False, indent=4)
    print(f"已保存智能复盘池 ({len(smart_stocks)}只股票)")
    
    # 显示所有复盘池数据
    print("\n===== 复盘池内容 =====")
    
    # 显示基础复盘池
    print("\n基础复盘池中的股票:")
    for i, stock in enumerate(basic_stocks, 1):
        print(f"{i}. {stock['name']}({stock['symbol']}) - {stock['recommendation']}")
    
    # 显示增强版复盘池
    print("\n增强版复盘池中的股票:")
    for i, stock in enumerate(enhanced_review['stocks'], 1):
        print(f"{i}. {stock['name']}({stock['symbol']}) - {stock['recommendation']}")
    
    # 显示智能复盘池
    print("\n智能复盘池中的股票:")
    for i, stock in enumerate(smart_review['stocks'], 1):
        print(f"{i}. {stock['name']}({stock['symbol']}) - 智能评分: {stock['smart_score']}")
    
    print("\n修复完成！请重新启动股票分析应用，然后查看复盘池中的股票。")

if __name__ == "__main__":
    print("开始修复复盘池...\n")
    fix_and_display() 