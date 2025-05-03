#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
显示复盘池中的股票，不依赖于增强版复盘功能
"""

import os
import json
import sys
from datetime import datetime

def print_review_pool():
    """打印复盘池中的所有股票"""
    # 读取基础复盘池
    review_pool_file = 'review_pool.json'
    try:
        with open(review_pool_file, 'r', encoding='utf-8') as f:
            review_pool = json.load(f)
        
        stocks = review_pool.get('stocks', [])
        
        print("\n===== 复盘池股票列表 =====\n")
        print(f"总股票数: {len(stocks)}只")
        
        print("\n观察中的股票:")
        watching_stocks = [s for s in stocks if s.get('status') == 'watching']
        if watching_stocks:
            for i, stock in enumerate(watching_stocks, 1):
                print(f"{i}. {stock.get('name', '')}({stock.get('symbol', '')}) - 添加日期: {stock.get('date_added', '')}")
                print(f"   - 分析得分: {stock.get('analysis_score', 0)}")
                print(f"   - 市场状态: {stock.get('market_status', '')}")
                print(f"   - 来源: {stock.get('source', '')}")
                if stock.get('notes'):
                    print(f"   - 备注: {stock.get('notes', '')}")
                if stock.get('recommendation'):
                    print(f"   - 推荐: {stock.get('recommendation', '')}")
                print()
        else:
            print("暂无观察中的股票\n")
        
        print("\n已买入的股票:")
        bought_stocks = [s for s in stocks if s.get('status') == 'bought']
        if bought_stocks:
            for i, stock in enumerate(bought_stocks, 1):
                print(f"{i}. {stock.get('name', '')}({stock.get('symbol', '')}) - 买入日期: {stock.get('buy_date', '')}")
                print(f"   - 买入价格: {stock.get('buy_price', 0)}")
                print()
        else:
            print("暂无已买入的股票\n")
        
        print("\n===== 复盘池信息 =====")
        print(f"最后更新时间: {review_pool.get('last_updated', '')}")
        
        return True
    except Exception as e:
        print(f"读取复盘池失败: {str(e)}")
        return False

def show_enhanced_pool():
    """打印增强版复盘池中的所有股票"""
    enhanced_review_file = 'enhanced_review_pool.json'
    try:
        with open(enhanced_review_file, 'r', encoding='utf-8') as f:
            enhanced_pool = json.load(f)
        
        stocks = enhanced_pool.get('stocks', [])
        
        print("\n===== 增强版复盘池股票列表 =====\n")
        print(f"总股票数: {len(stocks)}只")
        
        print("\n观察中的股票:")
        watching_stocks = [s for s in stocks if s.get('status') == 'watching']
        if watching_stocks:
            for i, stock in enumerate(watching_stocks, 1):
                print(f"{i}. {stock.get('name', '')}({stock.get('symbol', '')}) - 添加日期: {stock.get('date_added', '')}")
                print(f"   - 分析得分: {stock.get('analysis_score', 0)}")
                print(f"   - 市场状态: {stock.get('market_status', '')}")
                print(f"   - 来源: {stock.get('source', '')}")
                if stock.get('notes'):
                    print(f"   - 备注: {stock.get('notes', '')}")
                if stock.get('recommendation'):
                    print(f"   - 推荐: {stock.get('recommendation', '')}")
                print()
        else:
            print("暂无观察中的股票\n")
        
        print("\n===== 增强版复盘池信息 =====")
        if enhanced_pool.get('settings'):
            settings = enhanced_pool.get('settings', {})
            print(f"数据源: {settings.get('data_source', '')}")
            print(f"自动更新: {'开启' if settings.get('auto_update') else '关闭'}")
            print(f"最后更新时间: {settings.get('last_updated', '')}")
        
        return True
    except Exception as e:
        print(f"读取增强版复盘池失败: {str(e)}")
        return False

def show_smart_pool():
    """打印智能复盘池中的所有股票"""
    smart_review_file = './smart_review_data/smart_review_pool.json'
    try:
        with open(smart_review_file, 'r', encoding='utf-8') as f:
            smart_pool = json.load(f)
        
        stocks = smart_pool.get('stocks', [])
        
        print("\n===== 智能复盘池股票列表 =====\n")
        print(f"总股票数: {len(stocks)}只")
        
        print("\n观察中的股票:")
        watching_stocks = [s for s in stocks if s.get('status') == 'watching']
        if watching_stocks:
            for i, stock in enumerate(watching_stocks, 1):
                print(f"{i}. {stock.get('name', '')}({stock.get('symbol', '')}) - 添加日期: {stock.get('date_added', '')}")
                print(f"   - 智能评分: {stock.get('smart_score', 0)}")
                print(f"   - 重要性: {stock.get('importance', 0)}")
                if stock.get('tags'):
                    print(f"   - 标签: {', '.join(stock.get('tags', []))}")
                if stock.get('notes'):
                    print(f"   - 备注: {stock.get('notes', '')}")
                print()
        else:
            print("暂无观察中的股票\n")
        
        print("\n===== 智能复盘池信息 =====")
        print(f"创建时间: {smart_pool.get('created_at', '')}")
        print(f"最后更新时间: {smart_pool.get('last_updated', '')}")
        print(f"版本: {smart_pool.get('version', '')}")
        
        return True
    except Exception as e:
        print(f"读取智能复盘池失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("显示所有复盘池中的股票...\n")
    
    print_review_pool()
    print("\n" + "="*50 + "\n")
    show_enhanced_pool()
    print("\n" + "="*50 + "\n")
    show_smart_pool() 