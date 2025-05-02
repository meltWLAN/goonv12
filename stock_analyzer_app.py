from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QApplication, QMessageBox, QInputDialog, QLabel, QFrame, QLineEdit, 
    QTableWidget, QDateEdit, QSpinBox, QDoubleSpinBox, QComboBox, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt
import pandas as pd
from visual_stock_system import VisualStockSystem
from single_stock_analyzer import SingleStockAnalyzer
import sys
import logging

class StockAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        print("正在初始化股票分析系统...")
        self.token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        
        # 初始化日志
        self.logger = logging.getLogger('StockAnalyzerApp')
        
        try:
            self.visual_system = VisualStockSystem(self.token)
            print("成功初始化数据系统")
            self.initUI()
            print("GUI界面已启动，程序准备就绪")
        except Exception as e:
            print(f"系统初始化失败：{str(e)}")
            QMessageBox.critical(self, '错误', f'系统初始化失败：{str(e)}')
            sys.exit(1)
        
    def initUI(self):
        # 设置主窗口
        self.setWindowTitle('可视化股票分析系统')
        self.setGeometry(100, 100, 1000, 800)
        
        # 设置应用字体 - 使用macOS系统字体
        app_font = QFont('PingFang SC', 10)  # macOS上常用的中文字体
        QApplication.setFont(app_font)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标题
        title_label = QLabel('可视化股票分析系统')
        title_label.setFont(QFont('PingFang SC', 16, QFont.Bold))  # 修改字体
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 创建顶部控制区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        # 添加分析按钮
        analyze_btn = self.create_styled_button('分析全市场')
        analyze_btn.clicked.connect(self.analyze_stocks)
        control_layout.addWidget(analyze_btn)
        
        # 添加单只股票分析按钮
        single_stock_btn = self.create_styled_button('单只股票分析')
        single_stock_btn.clicked.connect(self.analyze_single_stock)
        control_layout.addWidget(single_stock_btn)
        
        # 添加可视化按钮
        visualize_btn = self.create_styled_button('可视化分析')
        visualize_btn.clicked.connect(self.visualize_stocks)
        control_layout.addWidget(visualize_btn)
        
        # 添加回测按钮
        backtest_btn = self.create_styled_button('策略回测')
        backtest_btn.clicked.connect(self.analyze_backtest)
        control_layout.addWidget(backtest_btn)
        
        # 添加热门行业分析按钮
        sector_btn = self.create_styled_button('热门行业')
        sector_btn.clicked.connect(self.analyze_sectors)
        control_layout.addWidget(sector_btn)
        
        # 添加复盘功能按钮
        review_btn = self.create_styled_button('股票复盘')
        review_btn.clicked.connect(self.show_stock_review)
        control_layout.addWidget(review_btn)

        # 添加体积价格分析按钮
        volume_price_btn = self.create_styled_button('体积价格分析')
        volume_price_btn.clicked.connect(self.analyze_volume_price)
        control_layout.addWidget(volume_price_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 添加结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont('PingFang SC', 10))
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.result_text)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                color: #333;
            }
        """)
        
        # 显示初始化成功消息
        self.result_text.append("系统初始化完成，可以开始分析股票数据。")

    def create_styled_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont('PingFang SC', 10))
        btn.setMinimumSize(120, 35)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        return btn
    
    def analyze_stocks(self):
        try:
            # 获取行业列表
            industries = self.visual_system.get_industry_list()
            if not industries:
                QMessageBox.warning(self, '错误', '获取行业列表失败')
                return

            # 让用户选择行业
            industry, ok = QInputDialog.getItem(
                self,
                '选择行业',
                '请选择要分析的行业：',
                ['全部'] + industries,
                0,
                False
            )

            if not ok:
                return

            self.result_text.clear()
            self.result_text.append(f'正在分析{"全市场" if industry == "全部" else industry}股票...')
            QApplication.processEvents()
            
            # 分析股票
            recommendations = self.visual_system.scan_stocks(industry=None if industry == '全部' else industry)
            
            if not recommendations:
                self.result_text.append('未找到符合条件的股票')
                return
                
            self.result_text.append(f'共分析 {len(recommendations)} 只股票')
            QApplication.processEvents()
            
            # 按照条件排序
            sorted_recommendations = sorted(recommendations, 
                key=lambda x: (
                    1 if x['trend'] == 'uptrend' else 0,
                    abs(x['macd_hist']),
                    x['volume'] / x['volume_ma20'],
                    x['atr']
                ), 
                reverse=True
            )
            
            # 显示前10只股票
            self.display_analysis(sorted_recommendations[:10])
            
            # 将推荐股票添加到复盘池 - 使用增强版复盘模块
            try:
                # 尝试使用增强版复盘模块
                from enhanced_stock_review import EnhancedStockReview
                review = EnhancedStockReview(self.token)
                added_count = review.add_recommendations_to_pool(sorted_recommendations)
                self.result_text.append(f'\n已添加 {added_count} 只强烈推荐买入的股票到复盘池')
            except Exception as e:
                # 如果增强版失败，回退到基础版
                from stock_review import StockReview
                review = StockReview(self.token)
                added_count = review.add_recommendations_to_pool(sorted_recommendations)
                self.result_text.append(f'\n已添加 {added_count} 只强烈推荐买入的股票到复盘池')
                self.result_text.append(f'注意: 增强版复盘模块加载失败，使用基础版: {str(e)}')
            
        except Exception as e:
            QMessageBox.warning(self, '错误', f'分析过程中出错：{str(e)}')
    
    def visualize_stocks(self):
        self.result_text.clear()
        self.result_text.append("正在准备可视化分析...")
        # 这里添加可视化分析的代码
        self.result_text.append("可视化分析功能尚未实现。")
    
    def analyze_backtest(self):
        """实现策略回测功能"""
        try:
            from enhanced_backtesting import EnhancedBacktester
            import pandas as pd
            from datetime import datetime, timedelta
            
            self.result_text.clear()
            self.result_text.append("正在准备策略回测...")
            QApplication.processEvents()
            
            # 获取用户输入的股票代码
            stock_code, ok = QInputDialog.getText(
                self, '输入股票代码',
                '请输入要回测的股票代码：\n支持以下格式：\n1. 六位数字代码（如：000001）\n2. 带交易所后缀（如：000001.SZ）',
                QLineEdit.Normal
            )
            
            if not ok or not stock_code:
                self.result_text.append("已取消回测")
                return
                
            # 获取回测参数
            start_date = QInputDialog.getText(
                self, '开始日期',
                '请输入回测开始日期 (YYYY-MM-DD)：',
                QLineEdit.Normal,
                (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            )[0]
            
            end_date = QInputDialog.getText(
                self, '结束日期',
                '请输入回测结束日期 (YYYY-MM-DD)：',
                QLineEdit.Normal,
                datetime.now().strftime('%Y-%m-%d')
            )[0]
            
            initial_capital = QInputDialog.getDouble(
                self, '初始资金',
                '请输入初始资金（元）：',
                100000, 10000, 10000000, 2
            )[0]
            
            # 获取策略选择
            strategy_options = ['MACD金叉策略', 'KDJ金叉策略', '双均线策略', '布林带策略', '量价策略']
            strategy, ok = QInputDialog.getItem(
                self, '选择策略',
                '请选择回测策略：',
                strategy_options,
                0,
                False
            )
            
            if not ok:
                self.result_text.append("已取消回测")
                return
                
            self.result_text.append(f"正在对 {stock_code} 进行 {strategy} 回测...")
            self.result_text.append(f"回测区间: {start_date} 至 {end_date}")
            self.result_text.append(f"初始资金: {initial_capital:,.2f} 元")
            QApplication.processEvents()
            
            # 初始化回测器
            backtester = EnhancedBacktester(initial_capital=initial_capital)
            
            # 获取股票数据
            stock_data = self.visual_system.get_stock_data(
                stock_code, 
                start_date=start_date,
                end_date=end_date
            )
            
            if stock_data is None or stock_data.empty:
                self.result_text.append(f"获取股票 {stock_code} 数据失败")
                return
                
            # 执行回测
            self.result_text.append("正在执行回测计算...")
            QApplication.processEvents()
            
            # 根据选择的策略执行回测
            if strategy == 'MACD金叉策略':
                result = backtester.backtest_macd_strategy(stock_data, stock_code)
            elif strategy == 'KDJ金叉策略':
                result = backtester.backtest_kdj_strategy(stock_data, stock_code)
            elif strategy == '双均线策略':
                result = backtester.backtest_ma_strategy(stock_data, stock_code)
            elif strategy == '布林带策略':
                result = backtester.backtest_bollinger_strategy(stock_data, stock_code)
            elif strategy == '量价策略':
                result = backtester.backtest_volume_price_strategy(stock_data, stock_code)
            else:
                result = backtester.backtest_macd_strategy(stock_data, stock_code)  # 默认策略
            
            # 显示回测结果
            self.result_text.clear()
            self.result_text.append(f"===== {stock_code} {strategy} 回测结果 =====\n")
            self.result_text.append(f"初始资金: {initial_capital:,.2f} 元")
            self.result_text.append(f"最终资金: {backtester.current_capital:,.2f} 元")
            self.result_text.append(f"总收益率: {((backtester.current_capital/initial_capital)-1)*100:.2f}%")
            self.result_text.append(f"年化收益率: {backtester.annual_return*100:.2f}%")
            self.result_text.append(f"最大回撤: {backtester.max_drawdown*100:.2f}%")
            self.result_text.append(f"夏普比率: {backtester.sharpe_ratio:.2f}")
            self.result_text.append(f"交易次数: {backtester.trade_count}")
            self.result_text.append(f"胜率: {backtester.win_rate*100:.2f}%")
            self.result_text.append(f"盈亏比: {backtester.profit_ratio:.2f}")
            self.result_text.append(f"平均持仓周期: {backtester.avg_holding_period:.1f} 天")
            
            # 显示交易记录
            if backtester.trades:
                self.result_text.append("\n===== 交易记录 =====")
                for i, trade in enumerate(backtester.trades[-10:], 1):  # 只显示最近10条
                    self.result_text.append(f"\n{i}. {trade.timestamp.strftime('%Y-%m-%d')} - {trade.action.upper()}")
                    self.result_text.append(f"   价格: {trade.price:.2f} 数量: {trade.volume:.0f} 股")
                    if trade.action == 'sell':
                        self.result_text.append(f"   收益: {trade.profit:.2f} 元")
            
            # 保存回测结果
            try:
                with open('backtest_results.json', 'w') as f:
                    import json
                    json.dump({
                        'stock_code': stock_code,
                        'strategy': strategy,
                        'start_date': start_date,
                        'end_date': end_date,
                        'initial_capital': initial_capital,
                        'final_capital': backtester.current_capital,
                        'total_return': ((backtester.current_capital/initial_capital)-1)*100,
                        'annual_return': backtester.annual_return*100,
                        'max_drawdown': backtester.max_drawdown*100,
                        'sharpe_ratio': backtester.sharpe_ratio,
                        'trade_count': backtester.trade_count,
                        'win_rate': backtester.win_rate*100,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }, f, indent=4)
                self.result_text.append("\n回测结果已保存到 backtest_results.json")
            except Exception as e:
                self.result_text.append(f"\n保存回测结果失败: {str(e)}")
                
        except Exception as e:
            self.show_error_message('回测错误', f'执行回测时出错：{str(e)}')
            self.result_text.clear()
            self.result_text.append(f'回测失败：{str(e)}')
        
    def analyze_single_stock(self):
        """分析单只股票"""
        try:
            # 获取用户输入的股票代码
            stock_code, ok = QInputDialog.getText(
                self, '输入股票代码',
                '请输入股票代码：\n支持以下格式：\n1. 六位数字代码（如：000001）\n2. 带交易所后缀（如：000001.SZ）',
                QLineEdit.Normal
            )
            
            if ok and stock_code:
                # 清空之前的结果
                self.result_text.clear()
                self.result_text.append(f'正在分析股票 {stock_code} ...')
                QApplication.processEvents()
                
                # 获取分析结果
                analyzer = SingleStockAnalyzer(self.token)
                result = analyzer.get_detailed_analysis(stock_code)
                
                if result['status'] == 'success':
                    data = result['data']
                    
                    # 确保所有必要的数据结构存在，避免KeyError
                    if 'trend_analysis' not in data:
                        data['trend_analysis'] = {'trend': '未知', 'strength': 0, 'rsi_value': 0}
                    if 'volume_analysis' not in data:
                        data['volume_analysis'] = {'status': '未知', 'ratio': 0}
                    if 'technical_indicators' not in data:
                        data['technical_indicators'] = {'macd': 0, 'macd_signal': 0, 'macd_hist': 0}
                    if 'trading_advice' not in data:
                        data['trading_advice'] = '数据不足，无法提供交易建议'
                    
                    # 格式化输出分析结果
                    output = f"""分析结果：
股票代码：{data.get('symbol', stock_code)}
股票名称：{data.get('name', '未知')}
最新价格：{data.get('last_price', 0):.2f}
{data.get('price_explanation', '')}

趋势分析：
- 趋势：{data['trend_analysis'].get('trend', '未知')}
- 强度：{data['trend_analysis'].get('strength', 0):.2f}
{data['trend_analysis'].get('strength_explanation', '')}
- RSI：{data['trend_analysis'].get('rsi_value', 0):.2f}
{data['trend_analysis'].get('rsi_explanation', '')}

量价分析：
- 状态：{data['volume_analysis'].get('status', '未知')}
- 量比：{data['volume_analysis'].get('ratio', 0):.2f}
{data['volume_analysis'].get('volume_explanation', '')}

技术指标：
- MACD：{data['technical_indicators'].get('macd', 0):.3f}
- MACD信号线：{data['technical_indicators'].get('macd_signal', 0):.3f}
- MACD柱状：{data['technical_indicators'].get('macd_hist', 0):.3f}
{data['technical_indicators'].get('macd_explanation', '')}
- KDJ指标：
  K值：{data['technical_indicators'].get('k', 0):.2f}
  D值：{data['technical_indicators'].get('d', 0):.2f}
  J值：{data['technical_indicators'].get('j', 0):.2f}
{data['technical_indicators'].get('kdj_explanation', '')}

市场分析：
- 波动率：{data.get('market_analysis', {}).get('volatility', 0):.2f}
{data.get('market_analysis', {}).get('volatility_explanation', '')}
- 周期共振：{data.get('market_analysis', {}).get('cycle_resonance', 0):.2f}
{data.get('market_analysis', {}).get('resonance_explanation', '')}

价格区间分析：
- 支撑位：{data.get('trading_ranges', {}).get('support', 0):.2f}
- 压力位：{data.get('trading_ranges', {}).get('resistance', 0):.2f}

交易区间建议：
买入区间：{data.get('trading_ranges', {}).get('buy_range', {}).get('low', 0):.2f} - {data.get('trading_ranges', {}).get('buy_range', {}).get('high', 0):.2f}
卖出区间：{data.get('trading_ranges', {}).get('sell_range', {}).get('low', 0):.2f} - {data.get('trading_ranges', {}).get('sell_range', {}).get('high', 0):.2f}
{data.get('trading_ranges', {}).get('explanation', '')}

交易建议：
{data.get('trading_advice', '数据不足，无法提供交易建议')}"""
                    
                    self.result_text.clear()
                    self.result_text.append(output)
                else:
                    self.show_error_message('分析失败', result.get('message', '未知错误'))
                    self.result_text.clear()
                    self.result_text.append(f'分析失败：{result.get("message", "未知错误")}')
        
        except Exception as e:
            self.show_error_message('系统错误', f'发生未知错误：{str(e)}')
            self.result_text.clear()
            self.result_text.append(f'系统错误：{str(e)}')
    
    def show_error_message(self, title, message):
        """显示错误消息对话框"""
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.exec_()
        
    def show_stock_review(self):
        """显示股票复盘功能"""
        try:
            # 尝试使用增强版复盘模块
            try:
                from enhanced_stock_review import EnhancedStockReview
                # 初始化增强版复盘模块
                review = EnhancedStockReview(self.token)
                # 集成UI功能
                review_functions = review.integrate_with_ui(self)
                # 显示增强版复盘
                review_functions['show_enhanced_review']()
                
                # 添加增强版功能按钮
                self.add_enhanced_review_buttons(review_functions)
                
                return
            except (ImportError, Exception) as e:
                print(f"加载增强版复盘模块失败，将使用基础版：{str(e)}")
                pass
            
            # 如果增强版加载失败，使用基础版
            from stock_review import StockReview
            
            # 清空之前的结果
            self.result_text.clear()
            self.result_text.append('正在加载复盘数据...')
            QApplication.processEvents()
            
            # 初始化复盘模块
            review = StockReview(self.token)
            
            # 获取复盘股票池
            all_stocks = review.get_review_pool()
            watching_stocks = review.get_review_pool(status='watching')
            bought_stocks = review.get_review_pool(status='bought')
            sold_stocks = review.get_review_pool(status='sold')
            
            # 获取绩效统计
            performance = review.get_performance_stats()
            
            # 格式化输出复盘结果
            output = f"""股票复盘分析：

复盘池概况：
- 总股票数：{len(all_stocks)}只
- 观察中：{len(watching_stocks)}只
- 已买入：{len(bought_stocks)}只
- 已卖出：{len(sold_stocks)}只

交易绩效统计：
- 总交易次数：{performance['total_trades']}次
- 胜率：{performance['win_rate']}%
- 平均收益：{performance['avg_profit']}%
- 平均持仓天数：{performance['avg_holding_days']}天
- 最大收益：{performance['max_profit']}%
- 最大亏损：{performance['max_loss']}%
- 总收益：{performance['total_profit']}%

最近交易记录："""
            
            # 添加最近的交易记录
            recent_trades = sorted(
                [s for s in all_stocks if s['status'] == 'sold'],
                key=lambda x: x.get('sell_date', ''),
                reverse=True
            )[:5]  # 最近5条记录
            
            if recent_trades:
                for i, trade in enumerate(recent_trades, 1):
                    profit_color = '红色' if trade.get('profit_percent', 0) > 0 else '绿色'
                    output += f"\n{i}. {trade.get('name', '')}({trade.get('symbol', '')})："
                    output += f"\n   - 买入日期：{trade.get('buy_date', '')}"
                    output += f"\n   - 买入价格：{trade.get('buy_price', 0)}"
                    output += f"\n   - 卖出日期：{trade.get('sell_date', '')}"
                    output += f"\n   - 卖出价格：{trade.get('sell_price', 0)}"
                    output += f"\n   - 收益率：{trade.get('profit_percent', 0)}%"
                    output += f"\n   - 持有天数：{trade.get('holding_days', 0)}天"
            else:
                output += "\n暂无交易记录"
                
            # 添加当前持仓
            output += "\n\n当前持仓："
            if bought_stocks:
                for i, stock in enumerate(bought_stocks, 1):
                    output += f"\n{i}. {stock.get('name', '')}({stock.get('symbol', '')})："
                    output += f"\n   - 买入日期：{stock.get('buy_date', '')}"
                    output += f"\n   - 买入价格：{stock.get('buy_price', 0)}"
                    output += f"\n   - 持有天数：{(datetime.now() - datetime.strptime(stock.get('buy_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')).days}天"
            else:
                output += "\n暂无持仓"
                
            # 添加观察中的股票
            output += "\n\n观察中的股票："
            if watching_stocks:
                for i, stock in enumerate(watching_stocks, 1):  # 移除[:10]限制，显示所有观察中的股票
                    output += f"\n{i}. {stock.get('name', '')}({stock.get('symbol', '')}) - 添加日期：{stock.get('date_added', '')}"
                    output += f"\n   - 分析得分：{stock.get('analysis_score', 0)}"
                    output += f"\n   - 市场状态：{stock.get('market_status', '')}"
                    output += f"\n   - 来源：{stock.get('source', '')}"
                    if stock.get('notes'):
                        output += f"\n   - 备注：{stock.get('notes', '')}"
            else:
                output += "\n暂无观察中的股票"
            
            self.result_text.clear()
            self.result_text.append(output)
            
        except Exception as e:
            self.show_error_message('错误', f'加载复盘数据时出错：{str(e)}')
            self.result_text.clear()
            self.result_text.append(f'加载失败：{str(e)}')
            
    def add_enhanced_review_buttons(self, review_functions):
        """添加增强版复盘功能按钮"""
        try:
            from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QWidget
            from PyQt5.QtCore import Qt
            
            # 创建按钮容器
            if hasattr(self, 'review_button_container'):
                # 如果已存在，先移除
                self.review_button_container.deleteLater()
                
            self.review_button_container = QWidget()
            button_layout = QHBoxLayout(self.review_button_container)
            button_layout.setContentsMargins(0, 10, 0, 0)
            button_layout.setSpacing(10)
            
            # 添加手动添加股票按钮
            add_stock_btn = self.create_styled_button('添加股票')
            add_stock_btn.clicked.connect(review_functions['add_stock_manually'])
            button_layout.addWidget(add_stock_btn)
            
            # 添加自动跟踪按钮
            review_instance = review_functions['review_instance']
            tracking_btn = self.create_styled_button(
                '停止自动跟踪' if review_instance.auto_tracking_enabled else '启动自动跟踪'
            )
            tracking_btn.clicked.connect(lambda: self.toggle_tracking_button(tracking_btn, review_functions))
            button_layout.addWidget(tracking_btn)
            
            # 添加刷新按钮
            refresh_btn = self.create_styled_button('刷新数据')
            refresh_btn.clicked.connect(review_functions['show_enhanced_review'])
            button_layout.addWidget(refresh_btn)
            
            # 添加到主布局
            layout = self.centralWidget().layout()
            layout.insertWidget(layout.count()-1, self.review_button_container)
            
        except Exception as e:
            print(f"添加增强版复盘按钮失败：{str(e)}")
    
    def toggle_tracking_button(self, button, review_functions):
        """切换自动跟踪按钮状态"""
        review_functions['toggle_auto_tracking']()
        review_instance = review_functions['review_instance']
        button.setText('停止自动跟踪' if review_instance.auto_tracking_enabled else '启动自动跟踪')
        
    def analyze_sectors(self):
        """分析热门行业"""
        try:
            # 使用集成器获取行业数据
            from integrate_sector_analyzer import SectorAnalyzerIntegrator
            integrator = SectorAnalyzerIntegrator()
            
            # 清空之前的结果
            self.result_text.clear()
            self.result_text.append('正在分析行业数据...')
            QApplication.processEvents()
            
            # 获取当前热门行业
            current_result = integrator.get_hot_sectors()
            if current_result['status'] != 'success':
                raise Exception(current_result.get('message', '获取热门行业失败'))
                
            # 获取统一分析结果
            unified_result = integrator.get_unified_analysis()
            
            # 显示结果
            self.result_text.clear()
            self.result_text.append('==== 热门行业分析 ====')
            self.result_text.append(f'[更新时间] {current_result["data"]["update_time"]}')
            self.result_text.append('')
            
            # 显示热门行业列表
            self.result_text.append('== 当前热门行业 ==')
            for i, sector in enumerate(current_result['data']['hot_sectors'][:10], 1):
                hot_level = sector.get('hot_level', '')
                hot_score = sector.get('hot_score', 0)
                self.result_text.append(f'{i}. {sector["name"]} - 热度: {hot_score:.2f} ({hot_level})')
            
            # 如果有技术分析数据，显示第一个行业的分析
            if 'technical_analysis' in unified_result['data']:
                tech = unified_result['data']['technical_analysis']
                self.result_text.append('')
                self.result_text.append(f'== {tech["sector"]}行业技术分析 ==')
                self.result_text.append(f'趋势: {tech["prediction"]["trend"]}')
                self.result_text.append(f'看多指数: {tech["prediction"]["bull_score"]}')
                self.result_text.append(f'分析: {tech["prediction"]["analysis"]}')
                
            self.logger.info("行业分析完成")
            
        except Exception as e:
            self.result_text.clear()
            self.result_text.append(f'分析行业数据失败: {str(e)}')
            self.logger.error(f"分析行业数据失败: {str(e)}")
            QMessageBox.warning(self, '错误', f'分析行业数据失败: {str(e)}')
    
    def display_analysis(self, recommendations):
        self.result_text.clear()
        self.result_text.append('=== 市场分析报告 ===\n')
        self.result_text.append(f'分析时间：{pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        self.result_text.append('最具投资价值的股票：')
        for stock in recommendations:
            stock_name = self.visual_system.get_stock_name(stock['symbol'])
            self.result_text.append(f"\n股票代码：{stock['symbol']} {stock_name}")
            self.result_text.append(f"当前趋势：{stock['trend']}")
            self.result_text.append(f"收盘价：{stock['close']:.2f}")
            self.result_text.append(f"成交量/20日均量：{stock['volume']/stock['volume_ma20']:.2f}")
            self.result_text.append(f"MACD柱状图：{stock['macd_hist']:.4f}")
            self.result_text.append(f"ATR：{stock['atr']:.4f}")
            self.result_text.append(f"建议：{stock.get('recommendation', '观望')}")
            self.result_text.append('-' * 30)

    def format_text_output(self, text):
        return f"<span style='color: #333; font-size: 10pt;'>{text}</span>"

    def analyze_volume_price(self):
        """执行体积价格分析"""
        try:
            # 获取用户输入的股票代码
            stock_code, ok = QInputDialog.getText(
                self,
                '输入股票代码',
                '请输入要分析的股票代码：',
                QLineEdit.Normal
            )
            
            if not ok or not stock_code:
                return
                
            self.result_text.clear()
            self.result_text.append(f'正在分析股票{stock_code}的量价关系...')
            QApplication.processEvents()
            
            # 获取股票数据
            df = self.visual_system.get_stock_data(stock_code)
            if df is None or df.empty:
                self.show_error_message('错误', f'获取股票{stock_code}数据失败')
                return
                
            # 执行量价分析
            df = self.visual_system.analyze_volume_price(df)
            if df is None:
                self.show_error_message('错误', '量价分析失败')
                return
                
            # 生成分析报告
            report = self._generate_volume_price_report(df)
            self.result_text.clear()
            self.result_text.append(report)
            
        except Exception as e:
            self.show_error_message('错误', f'体积价格分析失败：{str(e)}')
            
    def _generate_volume_price_report(self, df):
        """生成量价分析报告"""
        try:
            last_row = df.iloc[-1]
            
            # 格式化分析结果
            report = "量价分析报告\n" + "-" * 50 + "\n\n"
            
            # 1. 成交量分析
            volume_ratio = last_row['Volume_Ratio']
            report += f"成交量分析：\n"
            report += f"• 当前成交量是20日均量的 {volume_ratio:.2f} 倍\n"
            report += f"• 成交量状态：{'放量' if volume_ratio > 1.2 else '缩量' if volume_ratio < 0.8 else '平稳'}\n\n"
            
            # 2. 趋势分析
            trend_strength = last_row['Trend_Strength']
            trend_confidence = last_row['Trend_Confidence']
            report += f"趋势分析：\n"
            report += f"• 趋势强度：{trend_strength:.2f}\n"
            report += f"• 趋势可信度：{trend_confidence:.2%}\n"
            report += f"• 趋势状态：{'强势上涨' if trend_strength > 0.5 else '强势下跌' if trend_strength < -0.5 else '震荡'}\n\n"
            
            # 3. 支撑与压力
            report += f"支撑与压力：\n"
            report += f"• 上方压力位：{last_row['Upper_Line']:.2f}\n"
            report += f"• 下方支撑位：{last_row['Lower_Line']:.2f}\n"
            report += f"• 通道宽度：{last_row['Channel_Width']:.2f}%\n\n"
            
            # 4. 波动性分析
            report += f"波动性分析：\n"
            report += f"• ATR：{last_row['ATR']:.2f}\n"
            report += f"• 波动率：{last_row['Volatility']:.2f}%\n\n"
            
            # 5. 综合建议
            score = last_row['Volume_Price_Score']
            report += f"综合建议：\n"
            if score > 1.5:
                report += "• 市场活跃度高，可考虑积极参与\n"
            elif score < 0.5:
                report += "• 市场活跃度低，建议谨慎观望\n"
            else:
                report += "• 市场活跃度一般，建议择机参与\n"
                
            return report
            
        except Exception as e:
            return f"生成分析报告时出错：{str(e)}"

# 添加主入口代码
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = StockAnalyzerApp()
    window.show()
    sys.exit(app.exec_())