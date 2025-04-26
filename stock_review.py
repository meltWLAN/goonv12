import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import akshare as ak
from visual_stock_system import VisualStockSystem
from backtesting_wrapper import Backtesting

class StockReview:
    """股票复盘模块
    用于跟踪和分析系统推荐的强烈买入股票，建立专门的股票池进行后续复盘和回测
    提供交易指导和绩效分析
    """
    def __init__(self, token=None):
        self.token = token
        self.visual_system = VisualStockSystem(token)
        self.backtesting = Backtesting()
        self.review_pool_file = 'review_pool.json'
        self.performance_file = 'review_performance.json'
        self.review_pool = self._load_review_pool()
        self.performance_data = self._load_performance_data()
        
    def _load_review_pool(self):
        """加载复盘股票池"""
        if os.path.exists(self.review_pool_file):
            try:
                with open(self.review_pool_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载复盘股票池失败: {str(e)}")
                return {'stocks': []}
        else:
            return {'stocks': []}
    
    def _save_review_pool(self):
        """保存复盘股票池"""
        try:
            with open(self.review_pool_file, 'w', encoding='utf-8') as f:
                json.dump(self.review_pool, f, ensure_ascii=False, indent=4)
            print(f"复盘股票池已保存到 {self.review_pool_file}")
            return True
        except Exception as e:
            print(f"保存复盘股票池失败: {str(e)}")
            return False
    
    def _load_performance_data(self):
        """加载绩效数据"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载绩效数据失败: {str(e)}")
                return {'performances': []}
        else:
            return {'performances': []}
    
    def _save_performance_data(self):
        """保存绩效数据"""
        try:
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, ensure_ascii=False, indent=4)
            print(f"绩效数据已保存到 {self.performance_file}")
            return True
        except Exception as e:
            print(f"保存绩效数据失败: {str(e)}")
            return False
    
    def add_recommendations_to_pool(self, recommendations):
        """将推荐的股票添加到复盘股票池
        
        Args:
            recommendations: 推荐股票列表，每个元素应包含symbol, name, recommendation等信息
            
        Returns:
            添加的股票数量
        """
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        
        # 筛选出强烈推荐买入的股票
        for rec in recommendations:
            if isinstance(rec, dict) and rec.get('recommendation') == '强烈推荐买入':
                # 添加日期和初始状态
                rec['date_added'] = today
                rec['status'] = 'watching'  # 状态：watching, bought, sold
                rec['buy_price'] = None
                rec['sell_price'] = None
                rec['buy_date'] = None
                rec['sell_date'] = None
                rec['profit_percent'] = None
                rec['holding_days'] = None
                rec['notes'] = ''
                rec['source'] = '全市场分析'  # 标记数据来源
                rec['analysis_score'] = rec.get('score', 0)  # 保存分析得分
                rec['market_status'] = rec.get('market_status', '')  # 记录当时的市场状态
                
                # 检查是否已存在，如果存在则更新
                exists = False
                for stock in self.review_pool['stocks']:
                    if stock['symbol'] == rec['symbol']:
                        # 更新现有记录
                        stock.update(rec)
                        exists = True
                        break
                
                if not exists:
                    self.review_pool['stocks'].append(rec)
                    count += 1
        
        # 保存复盘池
        self._save_review_pool()
        
        print(f"已添加 {count} 只强烈推荐买入的股票到复盘池")
        return count
    
    def update_stock_status(self, symbol, status, price=None, date=None, notes=None):
        """更新股票状态
        
        Args:
            symbol: 股票代码
            status: 状态 (watching, bought, sold)
            price: 价格
            date: 日期，默认为今天
            notes: 备注信息
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        updated = False
        for stock in self.review_pool['stocks']:
            if stock['symbol'] == symbol:
                stock['status'] = status
                
                if status == 'bought':
                    stock['buy_price'] = price
                    stock['buy_date'] = date
                elif status == 'sold' and stock['buy_price'] is not None:
                    stock['sell_price'] = price
                    stock['sell_date'] = date
                    
                    # 计算收益率和持有天数
                    if stock['buy_price'] > 0:
                        stock['profit_percent'] = round((price - stock['buy_price']) / stock['buy_price'] * 100, 2)
                    
                    buy_date_obj = datetime.strptime(stock['buy_date'], "%Y-%m-%d")
                    sell_date_obj = datetime.strptime(date, "%Y-%m-%d")
                    stock['holding_days'] = (sell_date_obj - buy_date_obj).days
                    
                    # 添加到绩效数据
                    self._add_performance(stock)
                
                if notes:
                    stock['notes'] = notes
                    
                updated = True
                break
        
        if updated:
            self._save_review_pool()
            print(f"已更新股票 {symbol} 的状态为 {status}")
            return True
        else:
            print(f"未找到股票 {symbol}")
            return False
    
    def _add_performance(self, stock):
        """添加绩效数据"""
        performance = {
            'symbol': stock['symbol'],
            'name': stock['name'],
            'buy_date': stock['buy_date'],
            'buy_price': stock['buy_price'],
            'sell_date': stock['sell_date'],
            'sell_price': stock['sell_price'],
            'profit_percent': stock['profit_percent'],
            'holding_days': stock['holding_days'],
            'notes': stock['notes']
        }
        
        self.performance_data['performances'].append(performance)
        self._save_performance_data()
    
    def add_to_review_pool(self, stock_code, stock_name=None):
        """添加股票到复盘池"""
        if not stock_name:
            stock_name = self.visual_system.get_stock_name(stock_code)
        
        new_stock = {
            'symbol': stock_code,
            'name': stock_name,  # 明确存储股票名称
            'add_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'watching'
        }
        self.review_pool['stocks'].append(new_stock)
        self._save_review_pool()
        
    def analyze_performance(self, symbol, start_date=None, end_date=None):
        """分析股票的表现
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，默认为None（使用过去30天）
            end_date: 结束日期，默认为None（使用当前日期）
            
        Returns:
            分析结果字典，包含趋势、强度、价格和交易量等信息
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
            # 获取股票数据
            stock_data = self.visual_system.get_stock_data(symbol, start_date, end_date)
            if stock_data is None or stock_data.empty:
                return {'error': f"无法获取股票 {symbol} 的数据"}
                
            # 计算技术指标
            try:
                # 计算移动均线
                stock_data['ma5'] = stock_data['close'].rolling(window=5).mean()
                stock_data['ma10'] = stock_data['close'].rolling(window=10).mean()
                stock_data['ma20'] = stock_data['close'].rolling(window=20).mean()
                
                # 计算MACD
                exp12 = stock_data['close'].ewm(span=12, adjust=False).mean()
                exp26 = stock_data['close'].ewm(span=26, adjust=False).mean()
                stock_data['macd'] = exp12 - exp26
                stock_data['signal'] = stock_data['macd'].ewm(span=9, adjust=False).mean()
                stock_data['hist'] = stock_data['macd'] - stock_data['signal']
                
                # 计算RSI
                delta = stock_data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                stock_data['rsi'] = 100 - (100 / (1 + rs))
                
                # 获取最新数据
                latest = stock_data.iloc[-1]
                
                # 判断趋势
                trend = 'unknown'
                if latest['ma5'] > latest['ma10'] > latest['ma20']:
                    trend = 'uptrend'
                elif latest['ma5'] < latest['ma10'] < latest['ma20']:
                    trend = 'downtrend'
                elif latest['ma5'] > latest['ma10'] and latest['ma10'] < latest['ma20']:
                    trend = 'consolidation'
                
                # 计算趋势强度 (简化版ADX)
                strength = abs(latest['rsi'] - 50) * 2  # 简化计算，0-100
                
                # 成交量分析
                volume_trend = 'normal'
                avg_volume = stock_data['volume'].rolling(window=10).mean().iloc[-1]
                if latest['volume'] > avg_volume * 1.5:
                    volume_trend = 'increasing'
                elif latest['volume'] < avg_volume * 0.5:
                    volume_trend = 'decreasing'
                
                # 汇总结果
                result = {
                    'symbol': symbol,
                    'name': self.visual_system.get_stock_name(symbol),
                    'trend': trend,
                    'strength': strength,
                    'last_close': latest['close'],
                    'volume': latest['volume'],
                    'volume_trend': volume_trend,
                    'ma5': latest['ma5'],
                    'ma10': latest['ma10'],
                    'ma20': latest['ma20'],
                    'macd': latest['macd'],
                    'signal': latest['signal'],
                    'hist': latest['hist'],
                    'rsi': latest['rsi'],
                    'start_date': start_date,
                    'end_date': end_date
                }
                
                return result
                
            except Exception as inner_e:
                print(f"计算技术指标时出错: {str(inner_e)}")
                return {'error': f"计算技术指标时出错: {str(inner_e)}"}
            
        except Exception as e:
            print(f"分析股票 {symbol} 的表现时出错: {str(e)}")
            return {'error': f"分析出错: {str(e)}"}
    
    def get_review_pool(self, status=None):
        """获取复盘股票池"""
        if status:
            return [s for s in self.review_pool['stocks'] if s['status'] == status]
        return self.review_pool['stocks']
    
    def get_performance_stats(self):
        """获取绩效统计"""
        performances = self.performance_data['performances']
        if not performances:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_holding_days': 0,
                'max_profit': 0,
                'max_loss': 0,
                'total_profit': 0
            }
        
        total_trades = len(performances)
        win_trades = len([p for p in performances if p['profit_percent'] > 0])
        win_rate = round(win_trades / total_trades * 100, 2) if total_trades > 0 else 0
        
        profits = [p['profit_percent'] for p in performances]
        avg_profit = round(sum(profits) / len(profits), 2) if profits else 0
        max_profit = round(max(profits), 2) if profits else 0
        max_loss = round(min(profits), 2) if profits else 0
        total_profit = round(sum(profits), 2) if profits else 0
        
        holding_days = [p['holding_days'] for p in performances]
        avg_holding_days = round(sum(holding_days) / len(holding_days), 2) if holding_days else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_holding_days': avg_holding_days,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'total_profit': total_profit
        }
    
    def visualize_performance(self):
        """可视化绩效分析结果
        
        Returns:
            包含多个图表的字典
        """
        try:
            performances = self.performance_data['performances']
            if not performances:
                return None
                
            # 创建绩效分析图表
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('收益分布', '持仓时间分布', '累计收益趋势', '月度收益统计')
            )
            
            # 收益分布直方图
            profits = [p['profit_percent'] for p in performances]
            fig.add_trace(
                go.Histogram(x=profits, name='收益分布'),
                row=1, col=1
            )
            
            # 持仓时间分布
            holding_days = [p['holding_days'] for p in performances]
            fig.add_trace(
                go.Histogram(x=holding_days, name='持仓时间'),
                row=1, col=2
            )
            
            # 累计收益趋势
            dates = [p['sell_date'] for p in performances]
            cumulative_profits = np.cumsum(profits)
            fig.add_trace(
                go.Scatter(x=dates, y=cumulative_profits, name='累计收益'),
                row=2, col=1
            )
            
            # 月度收益统计
            df = pd.DataFrame(performances)
            df['sell_date'] = pd.to_datetime(df['sell_date'])
            monthly_profits = df.groupby(df['sell_date'].dt.strftime('%Y-%m'))['profit_percent'].mean()
            fig.add_trace(
                go.Bar(x=monthly_profits.index, y=monthly_profits.values, name='月度收益'),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                showlegend=True,
                title_text='交易绩效分析'
            )
            
            return fig
            
        except Exception as e:
            print(f"生成绩效分析图表时出错：{str(e)}")
            return None
            
    def get_enhanced_performance_stats(self):
        """获取增强版绩效统计
        
        Returns:
            详细的绩效统计指标字典
        """
        try:
            performances = self.performance_data['performances']
            if not performances:
                return None
                
            profits = [p['profit_percent'] for p in performances]
            holding_days = [p['holding_days'] for p in performances]
            
            stats = {
                '总交易次数': len(performances),
                '盈利次数': len([p for p in profits if p > 0]),
                '亏损次数': len([p for p in profits if p < 0]),
                '胜率': f"{len([p for p in profits if p > 0]) / len(profits) * 100:.2f}%",
                '平均收益率': f"{np.mean(profits):.2f}%",
                '最大收益': f"{max(profits):.2f}%",
                '最大亏损': f"{min(profits):.2f}%",
                '收益标准差': f"{np.std(profits):.2f}%",
                '平均持仓天数': f"{np.mean(holding_days):.1f}",
                '夏普比率': f"{np.mean(profits) / (np.std(profits) if np.std(profits) > 0 else 1):.2f}",
                '盈亏比': f"{np.mean([p for p in profits if p > 0]) / abs(np.mean([p for p in profits if p < 0])) if any(p < 0 for p in profits) else 'N/A'}"
            }
            
            # 计算连续盈亏情况
            profit_streak = 0
            loss_streak = 0
            max_profit_streak = 0
            max_loss_streak = 0
            current_streak = 0
            
            for profit in profits:
                if profit > 0:
                    if current_streak > 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                    max_profit_streak = max(max_profit_streak, current_streak)
                else:
                    if current_streak < 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                    max_loss_streak = min(max_loss_streak, current_streak)
            
            stats.update({
                '最大连续盈利次数': max_profit_streak,
                '最大连续亏损次数': abs(max_loss_streak)
            })
            
            return stats
            
        except Exception as e:
            print(f"计算增强版绩效统计时出错：{str(e)}")
            return None
    
    def plot_performance(self):
        """绘制绩效图表"""
        performances = self.performance_data['performances']
        if not performances:
            print("没有绩效数据可供绘制")
            return None
        
        # 按日期排序
        performances = sorted(performances, key=lambda x: x['sell_date'])
        
        # 创建图表
        fig = make_subplots(rows=2, cols=1,
                           shared_xaxes=True,
                           vertical_spacing=0.1,
                           subplot_titles=('交易收益率 (%)', '累计收益率 (%)'))
        
        # 交易收益率
        dates = [p['sell_date'] for p in performances]
        profits = [p['profit_percent'] for p in performances]
        symbols = [f"{p['name']} ({p['symbol']})" for p in performances]
        
        colors = ['green' if p > 0 else 'red' for p in profits]
        
        fig.add_trace(
            go.Bar(
                x=dates,
                y=profits,
                marker_color=colors,
                text=symbols,
                name='交易收益率'
            ),
            row=1, col=1
        )
        
        # 累计收益率
        cumulative_profits = np.cumsum(profits)
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative_profits,
                mode='lines+markers',
                name='累计收益率',
                line=dict(color='blue', width=2)
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title='交易绩效分析',
            height=800,
            showlegend=False
        )
        
        return fig
    
    def backtest_review_pool(self, start_date=None, end_date=None):
        """对复盘股票池进行回测
        
        Args:
            start_date: 回测开始日期，默认为所有股票添加日期的最早日期
            end_date: 回测结束日期，默认为今天
        """
        stocks = self.review_pool['stocks']
        if not stocks:
            print("复盘股票池为空，无法进行回测")
            return None
        
        # 确定日期范围
        if start_date is None:
            dates = [stock['date_added'] for stock in stocks]
            start_date = min(dates) if dates else datetime.now().strftime("%Y-%m-%d")
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 准备回测数据
        symbols = [stock['symbol'] for stock in stocks]
        names = [stock['name'] for stock in stocks]
        
        print(f"开始对 {len(symbols)} 只股票进行回测，时间范围: {start_date} 至 {end_date}")
        
        # 调用回测系统
        results = self.backtesting.backtest_portfolio(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000000,  # 初始资金100万
            position_size=0.1,        # 每只股票仓位10%
            stop_loss=0.05,           # 止损5%
            take_profit=0.15          # 止盈15%
        )
        
        return results
    
    def generate_trading_guidance(self):
        """生成交易指导"""
        watching_stocks = self.get_review_pool(status='watching')
        if not watching_stocks:
            return []
        
        guidance = []
        for stock in watching_stocks:
            try:
                # 获取最新分析
                analysis, _ = self.visual_system.analyze_stock(stock['symbol'])
                if not analysis:
                    continue
                
                # 生成交易建议
                advice = {
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'current_price': analysis['close'],
                    'recommendation': analysis['recommendation'],
                    'trend': analysis['trend'],
                    'macd_signal': analysis['technical_indicators']['macd']['explanation'],
                    'volume_status': analysis['volume_analysis']['status'],
                    'support_price': analysis['support_resistance']['support'],
                    'resistance_price': analysis['support_resistance']['resistance'],
                    'advice': self._generate_advice(analysis, stock),
                    'date': datetime.now().strftime("%Y-%m-%d")
                }
                
                guidance.append(advice)
            except Exception as e:
                print(f"生成 {stock['symbol']} 的交易指导时出错: {str(e)}")
        
        return guidance
    
    def _generate_advice(self, analysis, stock):
        """根据分析结果生成具体建议"""
        # 获取关键指标
        trend = analysis['trend']
        macd_hist = analysis['technical_indicators']['macd']['hist']
        volume_ratio = analysis['volume_analysis']['ratio']
        rsi = analysis['technical_indicators']['rsi']['value']
        current_price = analysis['close']
        
        # 生成建议
        if trend == 'uptrend' and macd_hist > 0 and volume_ratio > 1.2:
            return {
                'action': '买入',
                'reason': f"上升趋势确立，MACD金叉，成交量放大({volume_ratio}倍)，多重指标共振看多",
                'target_price': round(current_price * 1.05, 2),
                'stop_loss': round(current_price * 0.95, 2)
            }
        elif trend == 'uptrend' and macd_hist > 0:
            return {
                'action': '观望偏多',
                'reason': f"上升趋势形成，但量能不足({volume_ratio}倍)，建议等待放量确认",
                'target_price': round(current_price * 1.03, 2),
                'stop_loss': round(current_price * 0.97, 2)
            }
        elif trend == 'downtrend' and macd_hist < 0 and volume_ratio > 1.2:
            return {
                'action': '卖出',
                'reason': f"下跌趋势明显，MACD死叉，成交量放大({volume_ratio}倍)，建议止损",
                'target_price': None,
                'stop_loss': round(current_price * 0.98, 2)
            }
        elif rsi < 30 and trend == 'downtrend':
            return {
                'action': '关注超跌',
                'reason': f"RSI({rsi})显示超跌，可能出现反弹，建议关注不操作",
                'target_price': round(current_price * 1.05, 2),
                'stop_loss': None
            }
        elif rsi > 70 and trend == 'uptrend':
            return {
                'action': '注意获利了结',
                'reason': f"RSI({rsi})显示超买，可能出现回调，建议设置止盈",
                'target_price': round(current_price * 1.02, 2),
                'stop_loss': round(current_price * 0.98, 2)
            }
        else:
            return {
                'action': '观望',
                'reason': '市场信号不明确，建议观望',
                'target_price': None,
                'stop_loss': None
            }
    
    def print_guidance(self, guidance):
        """打印交易指导"""
        if not guidance:
            print("没有可用的交易指导")
            return
        
        print("\n===== 交易指导 =====")
        for advice in guidance:
            print(f"\n{advice['name']} ({advice['symbol']})")
            print(f"当前价格: {advice['current_price']}")
            print(f"趋势: {advice['trend']}")
            print(f"MACD信号: {advice['macd_signal']}")
            print(f"成交量状态: {advice['volume_status']}")
            print(f"支撑位: {advice['support_price']}")
            print(f"阻力位: {advice['resistance_price']}")
            print(f"建议操作: {advice['advice']['action']}")
            print(f"理由: {advice['advice']['reason']}")
            if advice['advice']['target_price']:
                print(f"目标价: {advice['advice']['target_price']}")
            if advice['advice']['stop_loss']:
                print(f"止损价: {advice['advice']['stop_loss']}")

def main():
    """复盘模块主函数"""
    try:
        # 创建复盘系统实例
        print("初始化股票复盘系统...")
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'  # 可以从配置文件读取
        review_system = StockReview(token)
        
        # 交互式菜单
        while True:
            print("\n===== 股票复盘系统 =====")
            print("1. 查看复盘股票池")
            print("2. 生成交易指导")
            print("3. 更新股票状态")
            print("4. 查看绩效统计")
            print("5. 绘制绩效图表")
            print("6. 回测复盘股票池")
            print("0. 退出")
            
            choice = input("\n请选择操作: ")
            
            if choice == '1':
                # 查看复盘股票池
                status = input("筛选状态 (watching/bought/sold/all): ") or 'all'
                stocks = review_system.get_review_pool(None if status == 'all' else status)
                
                if not stocks:
                    print("复盘股票池为空")
                    continue
                    
                print(f"\n===== 复盘股票池 ({status}) =====")
                for stock in stocks:
                    print(f"{stock['name']} ({stock['symbol']}) - 状态: {stock['status']}")
                    if stock['buy_price']:
                        print(f"  买入价: {stock['buy_price']} 买入日期: {stock['buy_date']}")
                    if stock['sell_price']:
                        print(f"  卖出价: {stock['sell_price']} 卖出日期: {stock['sell_date']}")
                        print(f"  收益率: {stock['profit_percent']}% 持有天数: {stock['holding_days']}")
                    print(f"  备注: {stock['notes']}")
                    
            elif choice == '2':
                # 生成交易指导
                guidance = review_system.generate_trading_guidance()
                review_system.print_guidance(guidance)
                
            elif choice == '3':
                # 更新股票状态
                symbol = input("请输入股票代码: ")
                status = input("请输入新状态 (watching/bought/sold): ")
                price = input("请输入价格 (可选): ")
                price = float(price) if price else None
                notes = input("请输入备注 (可选): ")
                
                review_system.update_stock_status(symbol, status, price, None, notes)
                
            elif choice == '4':
                # 查看绩效统计
                stats = review_system.get_performance_stats()
                print("\n===== 绩效统计 =====")
                print(f"总交易次数: {stats['total_trades']}")
                print(f"胜率: {stats['win_rate']}%")
                print(f"平均收益率: {stats['avg_profit']}%")
                print(f"平均持有天数: {stats['avg_holding_days']}")
                print(f"最大收益率: {stats['max_profit']}%")
                print(f"最大亏损率: {stats['max_loss']}%")
                print(f"总收益率: {stats['total_profit']}%")
                
            elif choice == '5':
                # 绘制绩效图表
                fig = review_system.plot_performance()
                if fig:
                    fig.show()
                
            elif choice == '6':
                # 回测复盘股票池
                start_date = input("请输入回测开始日期 (YYYY-MM-DD，可选): ")
                start_date = start_date if start_date else None
                end_date = input("请输入回测结束日期 (YYYY-MM-DD，可选): ")
                end_date = end_date if end_date else None
                
                results = review_system.backtest_review_pool(start_date, end_date)
                if results:
                    print("\n===== 回测结果 =====")
                    print(f"总收益率: {results['total_return']}%")
                    print(f"年化收益率: {results['annual_return']}%")
                    print(f"最大回撤: {results['max_drawdown']}%")
                    print(f"夏普比率: {results['sharpe_ratio']}")
                    
            elif choice == '0':
                print("退出系统")
                break
                
            else:
                print("无效的选择，请重新输入")
                
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()


    def analyze_stock_details(self, symbol):
        """获取股票的详细分析信息
        
        Args:
            symbol: 股票代码
        
        Returns:
            详细分析结果字典
        """
        try:
            # 使用 SingleStockAnalyzer 进行详细分析
            analyzer = SingleStockAnalyzer(self.token)
            analysis = analyzer.analyze_stock(symbol)
            
            # 获取历史推荐记录
            history = self._get_recommendation_history(symbol)
            
            return {
                'technical_analysis': analysis,
                'recommendation_history': history
            }
        except Exception as e:
            print(f"分析股票 {symbol} 时出错：{str(e)}")
            return None
    
    def _get_recommendation_history(self, symbol):
        """获取股票的历史推荐记录
        
        Args:
            symbol: 股票代码
        
        Returns:
            历史推荐记录列表
        """
        history = []
        for stock in self.review_pool['stocks']:
            if stock['symbol'] == symbol:
                history.append({
                    'date': stock.get('date_added'),
                    'status': stock.get('status'),
                    'analysis_score': stock.get('analysis_score'),
                    'market_status': stock.get('market_status'),
                    'notes': stock.get('notes')
                })
        return history
    
    def check_trading_signals(self):
        """检查观察股票池中的交易信号
        
        Returns:
            包含买卖信号的字典列表
        """
        signals = []
        for stock in self.review_pool['stocks']:
            if stock['status'] != 'sold':
                try:
                    # 获取最新行情数据
                    data = self.visual_system.get_stock_data(stock['symbol'])
                    if data is None:
                        continue
                        
                    # 计算技术指标
                    latest_price = data['close'].iloc[-1]
                    ma5 = data['close'].rolling(5).mean().iloc[-1]
                    ma10 = data['close'].rolling(10).mean().iloc[-1]
                    ma20 = data['close'].rolling(20).mean().iloc[-1]
                    
                    # 检查买入信号
                    if stock['status'] == 'watching':
                        buy_signals = []
                        if latest_price > ma5 > ma10:
                            buy_signals.append('均线金叉')
                        if data['volume'].iloc[-1] > data['volume'].rolling(5).mean().iloc[-1] * 1.5:
                            buy_signals.append('放量')
                            
                        if buy_signals:
                            signals.append({
                                'symbol': stock['symbol'],
                                'name': stock['name'],
                                'type': 'buy',
                                'price': latest_price,
                                'reasons': buy_signals,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                    
                    # 检查卖出信号
                    elif stock['status'] == 'bought':
                        sell_signals = []
                        if latest_price < ma5 < ma10:
                            sell_signals.append('均线死叉')
                        if latest_price < stock['buy_price'] * 0.95:  # 止损位
                            sell_signals.append('触及止损位')
                        elif latest_price > stock['buy_price'] * 1.2:  # 止盈位
                            sell_signals.append('达到止盈目标')
                            
                        if sell_signals:
                            signals.append({
                                'symbol': stock['symbol'],
                                'name': stock['name'],
                                'type': 'sell',
                                'price': latest_price,
                                'reasons': sell_signals,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                            
                except Exception as e:
                    print(f"检查股票 {stock['symbol']} 的交易信号时出错：{str(e)}")
                    continue
                    
        return signals
    
    def check_risk_alerts(self):
        """检查风险预警信号
        
        Returns:
            风险预警信息列表
        """
        alerts = []
        for stock in self.review_pool['stocks']:
            if stock['status'] != 'sold':
                try:
                    # 获取最新行情数据
                    data = self.visual_system.get_stock_data(stock['symbol'])
                    if data is None:
                        continue
                        
                    # 计算风险指标
                    latest_price = data['close'].iloc[-1]
                    price_change = (latest_price - data['close'].iloc[-2]) / data['close'].iloc[-2] * 100
                    volume_ratio = data['volume'].iloc[-1] / data['volume'].rolling(5).mean().iloc[-1]
                    
                    risk_factors = []
                    
                    # 检查价格异常波动
                    if abs(price_change) > 5:
                        risk_factors.append(f"价格异常波动：{price_change:.2f}%")
                    
                    # 检查成交量异常
                    if volume_ratio > 3:
                        risk_factors.append(f"成交量异常放大：{volume_ratio:.2f}倍")
                    
                    # 检查趋势反转
                    ma5 = data['close'].rolling(5).mean()
                    ma20 = data['close'].rolling(20).mean()
                    if ma5.iloc[-1] < ma20.iloc[-1] and ma5.iloc[-2] > ma20.iloc[-2]:
                        risk_factors.append("趋势可能反转")
                    
                    if risk_factors:
                        alerts.append({
                            'symbol': stock['symbol'],
                            'name': stock['name'],
                            'risk_factors': risk_factors,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'price': latest_price
                        })
                        
                except Exception as e:
                    print(f"检查股票 {stock['symbol']} 的风险预警时出错：{str(e)}")
                    continue
                    
        return alerts