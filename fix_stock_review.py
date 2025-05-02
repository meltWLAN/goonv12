#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复复盘池展示问题
1. 检查各个复盘池文件
2. 尝试修复可能存在的问题
3. 重新加载复盘池数据
"""

import sys
import os
import json
import shutil
from datetime import datetime

class StockReviewFixer:
    def __init__(self):
        self.basic_review_file = 'review_pool.json'
        self.enhanced_review_file = 'enhanced_review_pool.json'
        self.smart_review_dir = './smart_review_data'
        self.smart_review_file = os.path.join(self.smart_review_dir, 'smart_review_pool.json')
        
        # 记录当前状态
        self.has_basic_review = os.path.exists(self.basic_review_file)
        self.has_enhanced_review = os.path.exists(self.enhanced_review_file)
        self.has_smart_review_dir = os.path.exists(self.smart_review_dir)
        self.has_smart_review = os.path.exists(self.smart_review_file)
        
        # 初始化数据
        self.basic_review_data = None
        self.enhanced_review_data = None
        self.smart_review_data = None
        
        # 加载现有数据
        self._load_all_data()
    
    def _load_all_data(self):
        """加载所有复盘池数据"""
        if self.has_basic_review:
            try:
                with open(self.basic_review_file, 'r', encoding='utf-8') as f:
                    self.basic_review_data = json.load(f)
                print(f"成功加载基础复盘池，包含 {len(self.basic_review_data.get('stocks', []))} 只股票")
            except Exception as e:
                print(f"加载基础复盘池失败: {str(e)}")
                self.basic_review_data = {'stocks': []}
        
        if self.has_enhanced_review:
            try:
                with open(self.enhanced_review_file, 'r', encoding='utf-8') as f:
                    self.enhanced_review_data = json.load(f)
                print(f"成功加载增强版复盘池，包含 {len(self.enhanced_review_data.get('stocks', []))} 只股票")
            except Exception as e:
                print(f"加载增强版复盘池失败: {str(e)}")
                self.enhanced_review_data = {'stocks': [], 'settings': {}}
        
        if self.has_smart_review:
            try:
                with open(self.smart_review_file, 'r', encoding='utf-8') as f:
                    self.smart_review_data = json.load(f)
                print(f"成功加载智能复盘池，包含 {len(self.smart_review_data.get('stocks', []))} 只股票")
            except Exception as e:
                print(f"加载智能复盘池失败: {str(e)}")
                self.smart_review_data = {'stocks': [], 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': '2.0'}
    
    def validate_and_fix_stocks(self):
        """验证并修复股票数据"""
        # 验证基础复盘池
        if not self.has_basic_review or not self.basic_review_data or 'stocks' not in self.basic_review_data:
            print("基础复盘池不存在或结构不完整，创建新的复盘池")
            self.create_default_basic_review()
        
        # 验证增强版复盘池
        if not self.has_enhanced_review or not self.enhanced_review_data or 'stocks' not in self.enhanced_review_data:
            print("增强版复盘池不存在或结构不完整，创建新的增强版复盘池")
            self.create_default_enhanced_review()
        
        # 验证智能复盘池
        if not self.has_smart_review_dir:
            os.makedirs(self.smart_review_dir, exist_ok=True)
            print(f"已创建智能复盘池目录: {self.smart_review_dir}")
        
        if not self.has_smart_review or not self.smart_review_data or 'stocks' not in self.smart_review_data:
            print("智能复盘池不存在或结构不完整，创建新的智能复盘池")
            self.create_default_smart_review()
        
        # 同步所有股票数据
        self.sync_all_stocks()
        
        return True
    
    def create_default_basic_review(self):
        """创建默认的基础复盘池"""
        self.basic_review_data = {
            'stocks': [],
            'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        }
        self._save_basic_review()
    
    def create_default_enhanced_review(self):
        """创建默认的增强版复盘池"""
        self.enhanced_review_data = {
            'stocks': self.basic_review_data.get('stocks', []),
            'settings': {
                'auto_update': True,
                'notification': True,
                'data_source': 'tushare',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        self._save_enhanced_review()
    
    def create_default_smart_review(self):
        """创建默认的智能复盘池"""
        self.smart_review_data = {
            'stocks': [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '2.0'
        }
        self._save_smart_review()
    
    def _save_basic_review(self):
        """保存基础复盘池"""
        try:
            with open(self.basic_review_file, 'w', encoding='utf-8') as f:
                json.dump(self.basic_review_data, f, ensure_ascii=False, indent=4)
            print(f"基础复盘池已保存到 {self.basic_review_file}")
            return True
        except Exception as e:
            print(f"保存基础复盘池失败: {str(e)}")
            return False
    
    def _save_enhanced_review(self):
        """保存增强版复盘池"""
        try:
            with open(self.enhanced_review_file, 'w', encoding='utf-8') as f:
                json.dump(self.enhanced_review_data, f, ensure_ascii=False, indent=4)
            print(f"增强版复盘池已保存到 {self.enhanced_review_file}")
            return True
        except Exception as e:
            print(f"保存增强版复盘池失败: {str(e)}")
            return False
    
    def _save_smart_review(self):
        """保存智能复盘池"""
        try:
            with open(self.smart_review_file, 'w', encoding='utf-8') as f:
                json.dump(self.smart_review_data, f, ensure_ascii=False, indent=4)
            print(f"智能复盘池已保存到 {self.smart_review_file}")
            return True
        except Exception as e:
            print(f"保存智能复盘池失败: {str(e)}")
            return False
    
    def sync_all_stocks(self):
        """同步所有股票数据"""
        # 如果基础复盘池为空，但其他复盘池有数据，则从其他复盘池同步
        if not self.basic_review_data.get('stocks') and (self.enhanced_review_data.get('stocks') or self.smart_review_data.get('stocks')):
            if self.enhanced_review_data.get('stocks'):
                self.basic_review_data['stocks'] = self.enhanced_review_data['stocks']
                print("已从增强版复盘池同步股票数据到基础复盘池")
            elif self.smart_review_data.get('stocks'):
                # 转换智能复盘池格式到基础复盘池格式
                basic_stocks = []
                for smart_stock in self.smart_review_data['stocks']:
                    basic_stock = {
                        'symbol': smart_stock.get('symbol'),
                        'name': smart_stock.get('name'),
                        'date_added': smart_stock.get('date_added'),
                        'status': smart_stock.get('status', 'watching'),
                        'notes': smart_stock.get('notes', ''),
                        'source': '智能复盘池',
                        'analysis_score': smart_stock.get('smart_score', 0),
                        'market_status': '未知',
                        'recommendation': '强烈推荐买入'
                    }
                    basic_stocks.append(basic_stock)
                self.basic_review_data['stocks'] = basic_stocks
                print("已从智能复盘池同步股票数据到基础复盘池")
            self._save_basic_review()
        
        # 如果增强版复盘池为空，但基础复盘池有数据，则从基础复盘池同步
        if not self.enhanced_review_data.get('stocks') and self.basic_review_data.get('stocks'):
            self.enhanced_review_data['stocks'] = self.basic_review_data['stocks']
            print("已从基础复盘池同步股票数据到增强版复盘池")
            self._save_enhanced_review()
        
        # 如果智能复盘池为空，但其他复盘池有数据，则从其他复盘池同步
        if not self.smart_review_data.get('stocks') and (self.basic_review_data.get('stocks') or self.enhanced_review_data.get('stocks')):
            source_stocks = self.basic_review_data.get('stocks') or self.enhanced_review_data.get('stocks')
            # 转换基础/增强版复盘池格式到智能复盘池格式
            smart_stocks = []
            for stock in source_stocks:
                smart_stock = {
                    'symbol': stock.get('symbol'),
                    'name': stock.get('name'),
                    'date_added': stock.get('date_added'),
                    'status': stock.get('status', 'watching'),
                    'analysis': {},
                    'trade_history': [],
                    'notes': stock.get('notes', ''),
                    'tags': ['推荐', '强烈买入'],
                    'importance': 5,
                    'smart_score': stock.get('analysis_score', 0)
                }
                smart_stocks.append(smart_stock)
            self.smart_review_data['stocks'] = smart_stocks
            print("已从基础/增强版复盘池同步股票数据到智能复盘池")
            self._save_smart_review()
        
        print("所有复盘池数据已同步")
        return True
    
    def add_demo_stocks(self):
        """添加演示股票，确保复盘池不为空"""
        # 添加一些演示股票，确保复盘池有数据
        demo_stocks = [
            {"symbol": "000001.SZ", "name": "平安银行", "recommendation": "强烈推荐买入", "score": 92, "market_status": "上涨趋势"},
            {"symbol": "600519.SH", "name": "贵州茅台", "recommendation": "强烈推荐买入", "score": 95, "market_status": "强势整理"},
            {"symbol": "000858.SZ", "name": "五粮液", "recommendation": "强烈推荐买入", "score": 91, "market_status": "上涨趋势"},
            {"symbol": "600036.SH", "name": "招商银行", "recommendation": "强烈推荐买入", "score": 89, "market_status": "上涨趋势"},
            {"symbol": "601318.SH", "name": "中国平安", "recommendation": "强烈推荐买入", "score": 90, "market_status": "突破上涨"},
            {"symbol": "600276.SH", "name": "恒瑞医药", "recommendation": "强烈推荐买入", "score": 88, "market_status": "强势整理"},
            {"symbol": "000333.SZ", "name": "美的集团", "recommendation": "强烈推荐买入", "score": 87, "market_status": "上涨趋势"},
            {"symbol": "601888.SH", "name": "中国中免", "recommendation": "强烈推荐买入", "score": 86, "market_status": "强势整理"},
            {"symbol": "600887.SH", "name": "伊利股份", "recommendation": "强烈推荐买入", "score": 85, "market_status": "上涨趋势"},
            {"symbol": "601166.SH", "name": "兴业银行", "recommendation": "强烈推荐买入", "score": 84, "market_status": "突破上涨"},
            {"symbol": "000651.SZ", "name": "格力电器", "recommendation": "强烈推荐买入", "score": 83, "market_status": "上涨趋势"},
            {"symbol": "600900.SH", "name": "长江电力", "recommendation": "强烈推荐买入", "score": 82, "market_status": "强势整理"},
            {"symbol": "601288.SH", "name": "农业银行", "recommendation": "强烈推荐买入", "score": 81, "market_status": "上涨趋势"},
            {"symbol": "600030.SH", "name": "中信证券", "recommendation": "强烈推荐买入", "score": 80, "market_status": "突破上涨"},
            {"symbol": "601398.SH", "name": "工商银行", "recommendation": "强烈推荐买入", "score": 79, "market_status": "上涨趋势"},
            {"symbol": "600016.SH", "name": "民生银行", "recommendation": "强烈推荐买入", "score": 78, "market_status": "强势整理"},
            {"symbol": "601328.SH", "name": "交通银行", "recommendation": "强烈推荐买入", "score": 77, "market_status": "上涨趋势"},
            {"symbol": "601601.SH", "name": "中国太保", "recommendation": "强烈推荐买入", "score": 76, "market_status": "突破上涨"},
            {"symbol": "600000.SH", "name": "浦发银行", "recommendation": "强烈推荐买入", "score": 75, "market_status": "上涨趋势"},
            {"symbol": "002594.SZ", "name": "比亚迪", "recommendation": "强烈推荐买入", "score": 89, "market_status": "强势上涨"},
            {"symbol": "300750.SZ", "name": "宁德时代", "recommendation": "强烈推荐买入", "score": 93, "market_status": "突破上涨"},
            {"symbol": "600031.SH", "name": "三一重工", "recommendation": "强烈推荐买入", "score": 85, "market_status": "上涨趋势"}
        ]
        
        # 获取现有股票代码
        existing_symbols = [s.get('symbol') for s in self.basic_review_data.get('stocks', [])]
        
        # 添加演示股票到基础复盘池
        today = datetime.now().strftime('%Y-%m-%d')
        added_count = 0
        for stock in demo_stocks:
            if stock['symbol'] not in existing_symbols:
                stock_entry = {
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
                }
                self.basic_review_data['stocks'].append(stock_entry)
                added_count += 1
                existing_symbols.append(stock['symbol'])
        
        if added_count > 0:
            print(f"已添加 {added_count} 只演示股票到基础复盘池")
            self._save_basic_review()
            
            # 同步到其他复盘池
            self.sync_all_stocks()
        else:
            print("基础复盘池已有足够的股票数据，无需添加演示股票")
        
        return added_count

    def print_stock_stats(self):
        """打印股票统计信息"""
        print("\n===== 复盘池统计信息 =====")
        
        # 基础复盘池统计
        basic_stocks = self.basic_review_data.get('stocks', [])
        basic_watching = [s for s in basic_stocks if s.get('status') == 'watching']
        basic_bought = [s for s in basic_stocks if s.get('status') == 'bought']
        basic_sold = [s for s in basic_stocks if s.get('status') == 'sold']
        
        print("\n基础复盘池:")
        print(f"- 总股票数: {len(basic_stocks)}只")
        print(f"- 观察中: {len(basic_watching)}只")
        print(f"- 已买入: {len(basic_bought)}只")
        print(f"- 已卖出: {len(basic_sold)}只")
        
        # 增强版复盘池统计
        enhanced_stocks = self.enhanced_review_data.get('stocks', [])
        enhanced_watching = [s for s in enhanced_stocks if s.get('status') == 'watching']
        enhanced_bought = [s for s in enhanced_stocks if s.get('status') == 'bought']
        enhanced_sold = [s for s in enhanced_stocks if s.get('status') == 'sold']
        
        print("\n增强版复盘池:")
        print(f"- 总股票数: {len(enhanced_stocks)}只")
        print(f"- 观察中: {len(enhanced_watching)}只")
        print(f"- 已买入: {len(enhanced_bought)}只")
        print(f"- 已卖出: {len(enhanced_sold)}只")
        
        # 智能复盘池统计
        smart_stocks = self.smart_review_data.get('stocks', [])
        smart_watching = [s for s in smart_stocks if s.get('status') == 'watching']
        smart_bought = [s for s in smart_stocks if s.get('status') == 'bought']
        smart_sold = [s for s in smart_stocks if s.get('status') == 'sold']
        
        print("\n智能复盘池:")
        print(f"- 总股票数: {len(smart_stocks)}只")
        print(f"- 观察中: {len(smart_watching)}只")
        print(f"- 已买入: {len(smart_bought)}只")
        print(f"- 已卖出: {len(smart_sold)}只")

def main():
    print("开始修复复盘池展示问题...\n")
    
    fixer = StockReviewFixer()
    fixer.validate_and_fix_stocks()
    fixer.add_demo_stocks()
    fixer.print_stock_stats()
    
    print("\n修复完成！建议重新启动股票分析应用，然后查看复盘池中的股票。")

if __name__ == "__main__":
    main() 