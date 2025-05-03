from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QApplication, QMessageBox, QInputDialog, QLabel, QFrame, QLineEdit, 
    QTableWidget, QDateEdit, QSpinBox, QDoubleSpinBox, QComboBox, QHeaderView, QCheckBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt
import pandas as pd
import os
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
            # 检查增强版行业分析器是否可用
            try:
                from integrate_enhanced_sector import EnhancedSectorIntegrator
                self.enhanced_sector_available = True
                self.logger.info("增强版行业分析器已成功集成")
                print("增强版行业分析器已成功集成")
            except ImportError:
                self.enhanced_sector_available = False
                self.logger.warning("增强版行业分析器不可用")
                print("警告：增强版行业分析器不可用")
            
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
        sector_btn = self.create_styled_button('增强行业分析')
        sector_btn.clicked.connect(self.analyze_sectors)
        control_layout.addWidget(sector_btn)

        # 添加体积价格分析按钮
        volume_price_btn = self.create_styled_button('体积价格分析')
        volume_price_btn.clicked.connect(self.analyze_volume_price)
        control_layout.addWidget(volume_price_btn)
        
        # 添加智能推荐系统按钮
        smart_recommendation_btn = self.create_styled_button('智能推荐系统')
        smart_recommendation_btn.clicked.connect(self.open_smart_recommendation)
        control_layout.addWidget(smart_recommendation_btn)

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
            
            # 为每只股票添加推荐级别
            for stock in sorted_recommendations:
                # 设置推荐级别
                trend_score = 2 if stock['trend'] == 'uptrend' else -1
                macd_score = 2 if stock['macd_hist'] > 0 else -1
                volume_score = 1 if stock['volume'] / stock['volume_ma20'] > 1.2 else 0
                
                total_score = trend_score + macd_score + volume_score
                
                if total_score >= 4:
                    stock['recommendation'] = "强烈推荐买入"
                elif total_score == 3:
                    stock['recommendation'] = "积极买入"
                elif total_score > 0:
                    stock['recommendation'] = "建议买入"
                elif total_score == 0:
                    stock['recommendation'] = "中性观望"
                else:
                    stock['recommendation'] = "建议回避"
            
            # 显示前10只股票
            self.display_analysis(sorted_recommendations[:10])
            
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
            from evolving_backtester_integration import run_backtest
            import pandas as pd
            from datetime import datetime, timedelta
            
            self.result_text.clear()
            self.result_text.append("正在准备策略回测...")
            QApplication.processEvents()
            
            # 创建回测参数对话框
            backtest_dialog = QWidget()
            backtest_dialog.setWindowTitle("策略回测参数配置")
            backtest_dialog.setFixedWidth(450)
            backtest_layout = QVBoxLayout(backtest_dialog)
            
            # 股票代码输入
            stock_code_layout = QHBoxLayout()
            stock_code_layout.addWidget(QLabel("股票代码:"))
            stock_code_input = QLineEdit()
            stock_code_input.setPlaceholderText("请输入股票代码 (例如: 000001 或 000001.SZ)")
            stock_code_layout.addWidget(stock_code_input)
            backtest_layout.addLayout(stock_code_layout)
            
            # 日期选择
            date_layout = QHBoxLayout()
            date_layout.addWidget(QLabel("回测区间:"))
            start_date_edit = QDateEdit()
            start_date_edit.setDate(QDate.currentDate().addDays(-365))
            start_date_edit.setCalendarPopup(True)
            date_layout.addWidget(start_date_edit)
            date_layout.addWidget(QLabel("至"))
            end_date_edit = QDateEdit()
            end_date_edit.setDate(QDate.currentDate())
            end_date_edit.setCalendarPopup(True)
            date_layout.addWidget(end_date_edit)
            backtest_layout.addLayout(date_layout)
            
            # 初始资金
            capital_layout = QHBoxLayout()
            capital_layout.addWidget(QLabel("初始资金:"))
            capital_input = QDoubleSpinBox()
            capital_input.setRange(10000, 10000000)
            capital_input.setValue(100000)
            capital_input.setSingleStep(10000)
            capital_input.setSuffix(" 元")
            capital_layout.addWidget(capital_input)
            backtest_layout.addLayout(capital_layout)
            
            # 策略选择
            strategy_layout = QHBoxLayout()
            strategy_layout.addWidget(QLabel("回测策略:"))
            strategy_combo = QComboBox()
            strategy_options = ['MACD金叉策略', 'KDJ金叉策略', '双均线策略', '布林带策略', '量价策略']
            strategy_combo.addItems(strategy_options)
            strategy_layout.addWidget(strategy_combo)
            backtest_layout.addLayout(strategy_layout)
            
            # 回测模式
            mode_layout = QHBoxLayout()
            mode_layout.addWidget(QLabel("回测模式:"))
            mode_combo = QComboBox()
            backtest_modes = ['标准回测', '自进化回测 (AI增强)', '自学习回测 (进阶版)']
            mode_combo.addItems(backtest_modes)
            mode_layout.addWidget(mode_combo)
            backtest_layout.addLayout(mode_layout)
            
            # 添加模式说明标签
            mode_description = QLabel("标准回测 - 常规回测功能")
            mode_description.setStyleSheet("color: gray; font-size: 9pt;")
            backtest_layout.addWidget(mode_description)
            
            # 模式切换时更新说明文本
            def update_mode_description(index):
                descriptions = [
                    "标准回测 - 常规回测功能，使用传统技术指标计算",
                    "自进化回测 - AI增强型回测，能够根据市场状态自动调整参数",
                    "自学习回测 - 进阶版自适应回测，具备机器学习能力，可从历史交易中学习优化"
                ]
                mode_description.setText(descriptions[index])
            
            mode_combo.currentIndexChanged.connect(update_mode_description)
            
            # 根据模式显示/隐藏学习设置
            learning_checkbox = QCheckBox("启用自学习功能 (学习交易模式并持续优化策略)")
            learning_checkbox.setChecked(True)
            learning_checkbox.setVisible(False)
            backtest_layout.addWidget(learning_checkbox)
            
            def update_learning_visibility(index):
                # 仅对自进化和自学习模式显示学习选项
                learning_checkbox.setVisible(index > 0)
            
            mode_combo.currentIndexChanged.connect(update_learning_visibility)
            
            # 添加按钮
            button_layout = QHBoxLayout()
            cancel_btn = QPushButton("取消")
            run_btn = QPushButton("开始回测")
            run_btn.setStyleSheet("background-color: #2196F3; color: white;")
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(run_btn)
            backtest_layout.addLayout(button_layout)
            
            backtest_dialog.show()
            
            # 保存用户选择的参数
            backtest_params = {'confirmed': False}
            
            # 设置按钮事件
            def on_cancel():
                backtest_dialog.close()
                
            def on_confirm():
                # 验证股票代码
                if not stock_code_input.text().strip():
                    QMessageBox.warning(backtest_dialog, "错误", "请输入有效的股票代码")
                    return
                    
                backtest_params['confirmed'] = True
                backtest_params['stock_code'] = stock_code_input.text().strip()
                backtest_params['start_date'] = start_date_edit.date().toString('yyyy-MM-dd')
                backtest_params['end_date'] = end_date_edit.date().toString('yyyy-MM-dd')
                backtest_params['initial_capital'] = capital_input.value()
                backtest_params['strategy'] = strategy_combo.currentText()
                backtest_params['backtest_mode'] = mode_combo.currentText()
                backtest_params['learning_enabled'] = learning_checkbox.isChecked()
                backtest_dialog.close()
                
            cancel_btn.clicked.connect(on_cancel)
            run_btn.clicked.connect(on_confirm)
            
            # 执行对话框的事件循环
            while backtest_dialog.isVisible():
                QApplication.processEvents()
                
            # 如果用户取消，则返回
            if not backtest_params.get('confirmed', False):
                self.result_text.append("已取消回测")
                return
                
            # 解析参数
            stock_code = backtest_params['stock_code']
            start_date = backtest_params['start_date']
            end_date = backtest_params['end_date']
            initial_capital = backtest_params['initial_capital']
            strategy = backtest_params['strategy']
            backtest_mode = backtest_params['backtest_mode']
            learning_enabled = backtest_params['learning_enabled']
            
            # 将回测模式映射为系统支持的模式
            mode_mapping = {
                '标准回测': 'standard',
                '自进化回测 (AI增强)': 'adaptive', 
                '自学习回测 (进阶版)': 'evolving'
            }
            
            selected_mode = mode_mapping.get(backtest_mode, 'standard')
                
            self.result_text.append(f"正在对 {stock_code} 进行 {strategy} 回测...")
            self.result_text.append(f"回测模式: {backtest_mode}")
            self.result_text.append(f"自学习功能: {'已启用' if learning_enabled and selected_mode != 'standard' else '未启用'}")
            self.result_text.append(f"回测区间: {start_date} 至 {end_date}")
            self.result_text.append(f"初始资金: {initial_capital:,.2f} 元")
            QApplication.processEvents()
            
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
            
            # 使用新的回测调用接口
            if selected_mode in ['adaptive', 'evolving']:
                # 使用新的集成回测函数
                result = run_backtest(
                    stock_code=stock_code,
                    stock_data=stock_data,
                    strategy=strategy,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    mode=selected_mode,
                    learning_mode=learning_enabled if selected_mode != 'standard' else False
                )
                
                if not result.get('success', False):
                    self.result_text.clear()
                    self.result_text.append(f"回测失败: {result.get('error', '未知错误')}")
                    return
                    
                # 使用结果字典展示数据
                backtester_result = result
                final_capital = result.get('final_capital', initial_capital)
                total_return = result.get('total_return', 0)
                annual_return = result.get('annual_return', 0)
                max_drawdown = result.get('max_drawdown', 0)
                sharpe_ratio = result.get('sharpe_ratio', 0)
                trade_count = result.get('trade_count', 0)
                win_rate = result.get('win_rate', 0)
                profit_ratio = result.get('profit_ratio', 0)
                avg_holding_period = result.get('avg_holding_period', 0)
                
                # 如果有AI指标，获取它们
                ai_metrics = result.get('ml_metrics', {})
                strategy_adaptation_score = result.get('strategy_adaptation_score', 0)
                
            else:
                # 使用传统回测方式
                backtester = EnhancedBacktester(initial_capital=initial_capital)
            
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
                
                # 取回测器中的结果
                backtester_result = None
                final_capital = backtester.current_capital
                total_return = ((final_capital/initial_capital)-1)*100
                
                # 获取其他指标
                if hasattr(backtester, 'annual_return'):
                    annual_return = backtester.annual_return * 100
                else:
                    # 计算简单年化收益率
                    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
                    if days > 0:
                        annual_return = ((final_capital/initial_capital)**(365/days) - 1) * 100
                    else:
                        annual_return = 0
                
                max_drawdown = getattr(backtester, 'max_drawdown', 0) * 100
                sharpe_ratio = getattr(backtester, 'sharpe_ratio', 0)
                trade_count = getattr(backtester, 'trade_count', len(backtester.trades) if hasattr(backtester, 'trades') and backtester.trades else 0)
                win_rate = getattr(backtester, 'win_rate', 0) * 100
                profit_ratio = getattr(backtester, 'profit_ratio', 0)
                avg_holding_period = getattr(backtester, 'avg_holding_period', 0)
                
                ai_metrics = {}
                strategy_adaptation_score = 0
            
            # 结果对话框
            result_dialog = QWidget()
            result_dialog.setWindowTitle(f"{stock_code} {strategy} 回测结果")
            result_dialog.setFixedSize(700, 500)
            result_layout = QVBoxLayout(result_dialog)
            
            # 创建标题
            title_label = QLabel(f"{stock_code} {strategy} 回测结果")
            title_label.setFont(QFont('PingFang SC', 16, QFont.Bold))
            title_label.setAlignment(Qt.AlignCenter)
            result_layout.addWidget(title_label)
            
            # 创建分隔线
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            result_layout.addWidget(line)
            
            # 基本信息
            info_widget = QWidget()
            info_layout = QHBoxLayout(info_widget)
            
            # 左侧基本信息
            left_info = QWidget()
            left_layout = QVBoxLayout(left_info)
            left_layout.addWidget(QLabel(f"<b>回测模式:</b> {backtest_mode}"))
            if selected_mode in ['adaptive', 'evolving']:
                left_layout.addWidget(QLabel(f"<b>自学习功能:</b> {'已启用' if learning_enabled else '未启用'}"))
            left_layout.addWidget(QLabel(f"<b>回测区间:</b> {start_date} 至 {end_date}"))
            left_layout.addWidget(QLabel(f"<b>初始资金:</b> {initial_capital:,.2f} 元"))
            left_layout.addWidget(QLabel(f"<b>最终资金:</b> {final_capital:,.2f} 元"))
            info_layout.addWidget(left_info)
            
            # 右侧基本收益信息
            right_info = QWidget()
            right_layout = QVBoxLayout(right_info)
            
            # 用颜色标记正负收益
            total_return_color = "green" if total_return >= 0 else "red"
            annual_return_color = "green" if annual_return >= 0 else "red"
            
            right_layout.addWidget(QLabel(f"<b>总收益率:</b> <font color='{total_return_color}'>{total_return:.2f}%</font>"))
            right_layout.addWidget(QLabel(f"<b>年化收益率:</b> <font color='{annual_return_color}'>{annual_return:.2f}%</font>"))
            right_layout.addWidget(QLabel(f"<b>最大回撤:</b> {max_drawdown:.2f}%"))
            right_layout.addWidget(QLabel(f"<b>夏普比率:</b> {sharpe_ratio:.2f}"))
            info_layout.addWidget(right_info)
            
            result_layout.addWidget(info_widget)
            
            # 交易统计
            trade_stats = QWidget()
            trade_layout = QHBoxLayout(trade_stats)
            
            # 左侧交易统计
            left_stats = QWidget()
            left_stats_layout = QVBoxLayout(left_stats)
            left_stats_layout.addWidget(QLabel(f"<b>交易次数:</b> {trade_count}"))
            left_stats_layout.addWidget(QLabel(f"<b>胜率:</b> {win_rate:.2f}%"))
            trade_layout.addWidget(left_stats)
            
            # 右侧交易统计
            right_stats = QWidget()
            right_stats_layout = QVBoxLayout(right_stats)
            right_stats_layout.addWidget(QLabel(f"<b>盈亏比:</b> {profit_ratio:.2f}"))
            right_stats_layout.addWidget(QLabel(f"<b>平均持仓周期:</b> {avg_holding_period:.1f} 天"))
            trade_layout.addWidget(right_stats)
            
            result_layout.addWidget(trade_stats)
            
            # 添加AI增强指标部分 (仅对进化模式显示)
            if selected_mode == 'evolving':
                # 创建AI指标标题
                ai_title = QLabel("AI 增强指标")
                ai_title.setFont(QFont('PingFang SC', 14, QFont.Bold))
                ai_title.setAlignment(Qt.AlignCenter)
                result_layout.addWidget(ai_title)
                
                # 创建分隔线
                ai_line = QFrame()
                ai_line.setFrameShape(QFrame.HLine)
                ai_line.setFrameShadow(QFrame.Sunken)
                result_layout.addWidget(ai_line)
                
                # AI指标内容
                ai_widget = QWidget()
                ai_layout = QHBoxLayout(ai_widget)
                
                # 左侧AI指标
                left_ai = QWidget()
                left_ai_layout = QVBoxLayout(left_ai)
                left_ai_layout.addWidget(QLabel(f"<b>策略适应性评分:</b> {strategy_adaptation_score:.2f}"))
                
                # 添加入场信号相关指标
                if 'entry_model_accuracy' in ai_metrics:
                    left_ai_layout.addWidget(QLabel(f"<b>入场信号准确率:</b> {ai_metrics.get('entry_model_accuracy', 0):.2f}"))
                if 'entry_model_precision' in ai_metrics:
                    left_ai_layout.addWidget(QLabel(f"<b>入场信号精确度:</b> {ai_metrics.get('entry_model_precision', 0):.2f}"))
                ai_layout.addWidget(left_ai)
                
                # 右侧AI指标
                right_ai = QWidget()
                right_ai_layout = QVBoxLayout(right_ai)
                
                # 添加出场信号相关指标
                if 'exit_model_accuracy' in ai_metrics:
                    right_ai_layout.addWidget(QLabel(f"<b>出场信号准确率:</b> {ai_metrics.get('exit_model_accuracy', 0):.2f}"))
                if 'position_model_rmse' in ai_metrics:
                    right_ai_layout.addWidget(QLabel(f"<b>仓位模型RMSE:</b> {ai_metrics.get('position_model_rmse', 0):.4f}"))
                ai_layout.addWidget(right_ai)
                
                result_layout.addWidget(ai_widget)
                
                # 添加市场状态分析
                if 'market_regimes' in ai_metrics:
                    market_widget = QWidget()
                    market_layout = QVBoxLayout(market_widget)
                    market_layout.addWidget(QLabel("<b>市场状态分析:</b>"))
                    
                    regimes = ai_metrics.get('market_regimes', {})
                    regime_text = ""
                    for regime, percentage in regimes.items():
                        regime_text += f"{regime}: {percentage:.1f}% "
                    
                    market_layout.addWidget(QLabel(regime_text))
                    result_layout.addWidget(market_widget)
            
            # 添加按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.addStretch()
            close_btn = QPushButton("关闭")
            close_btn.setFixedWidth(100)
            
            # 如果有生成的图表，添加查看图表按钮
            if selected_mode == 'evolving' and 'chart_files' in result:
                chart_button = QPushButton("查看AI分析图表")
                chart_button.setStyleSheet("background-color: #4CAF50; color: white;")
                chart_button.setFixedWidth(150)
                
                def view_charts():
                    try:
                        # 创建图表查看对话框
                        chart_dialog = QWidget()
                        chart_dialog.setWindowTitle(f"{stock_code} {strategy} 分析图表")
                        chart_dialog.setMinimumSize(900, 700)
                        chart_layout = QVBoxLayout(chart_dialog)
                        
                        # 创建滚动区域来展示多个图表
                        from PyQt5.QtWidgets import QScrollArea
                        from PyQt5.QtGui import QPixmap
                        
                        scroll_area = QScrollArea()
                        scroll_area.setWidgetResizable(True)
                        scroll_content = QWidget()
                        scroll_layout = QVBoxLayout(scroll_content)
                        
                        charts_loaded = False
                        # 添加图表
                        for chart_file in result['chart_files']:
                            if not os.path.exists(chart_file):
                                continue
                                
                            # 创建图表标题
                            if 'performance' in chart_file:
                                title = "策略性能分析"
                            elif 'ai_metrics' in chart_file:
                                title = "AI增强指标分析"
                            else:
                                title = "回测分析图表"
                                
                            chart_title = QLabel(title)
                            chart_title.setFont(QFont('PingFang SC', 14, QFont.Bold))
                            chart_title.setAlignment(Qt.AlignCenter)
                            scroll_layout.addWidget(chart_title)
                            
                            try:
                                # 加载并显示图表
                                chart_label = QLabel()
                                pixmap = QPixmap(chart_file)
                                # 确保图片正确加载
                                if pixmap.isNull():
                                    raise Exception(f"无法加载图表: {chart_file}")
                                    
                                # 缩放图片以适应窗口宽度
                                pixmap = pixmap.scaledToWidth(850)
                                chart_label.setPixmap(pixmap)
                                chart_label.setAlignment(Qt.AlignCenter)
                                scroll_layout.addWidget(chart_label)
                                
                                # 添加间隔
                                spacer = QLabel()
                                spacer.setFixedHeight(20)
                                scroll_layout.addWidget(spacer)
                                charts_loaded = True
                            except Exception as e:
                                # 图表加载失败
                                error_label = QLabel(f"加载图表失败: {str(e)}")
                                error_label.setStyleSheet("color: red;")
                                scroll_layout.addWidget(error_label)
                        
                        # 如果没有加载到任何图表，显示提示信息
                        if not charts_loaded:
                            info_label = QLabel("未找到可用的分析图表。这可能是因为图表生成失败或者文件已被移除。")
                            info_label.setStyleSheet("color: #666; padding: 20px;")
                            info_label.setWordWrap(True)
                            info_label.setAlignment(Qt.AlignCenter)
                            scroll_layout.addWidget(info_label)
                        
                        scroll_area.setWidget(scroll_content)
                        chart_layout.addWidget(scroll_area)
                        
                        # 添加关闭按钮
                        close_chart_btn = QPushButton("关闭")
                        close_chart_btn.setFixedWidth(100)
                        close_chart_btn.clicked.connect(chart_dialog.close)
                        
                        btn_layout = QHBoxLayout()
                        btn_layout.addStretch()
                        btn_layout.addWidget(close_chart_btn)
                        btn_layout.addStretch()
                        chart_layout.addLayout(btn_layout)
                        
                        chart_dialog.show()
                        
                        # 等待用户关闭对话框
                        while chart_dialog.isVisible():
                            QApplication.processEvents()
                    except Exception as e:
                        QMessageBox.warning(self, "查看图表出错", f"加载图表时出错: {str(e)}")
                        self.logger.error(f"查看图表出错: {str(e)}")
                
                chart_button.clicked.connect(view_charts)
                button_layout.addWidget(chart_button)
                button_layout.addSpacing(20)
            
            button_layout.addWidget(close_btn)
            button_layout.addStretch()
            result_layout.addWidget(button_widget)
            
            close_btn.clicked.connect(result_dialog.close)
            
            result_dialog.show()
            
            # 显示回测结果
            self.result_text.clear()
            self.result_text.append(f"===== {stock_code} {strategy} 回测结果 =====\n")
            self.result_text.append(f"回测模式: {backtest_mode}")
            if selected_mode in ['adaptive', 'evolving']:
                self.result_text.append(f"自学习功能: {'已启用' if learning_enabled else '未启用'}")
            self.result_text.append(f"初始资金: {initial_capital:,.2f} 元")
            self.result_text.append(f"最终资金: {final_capital:,.2f} 元")
            self.result_text.append(f"总收益率: {total_return:.2f}%")
            self.result_text.append(f"年化收益率: {annual_return:.2f}%")
            self.result_text.append(f"最大回撤: {max_drawdown:.2f}%")
            self.result_text.append(f"夏普比率: {sharpe_ratio:.2f}")
            self.result_text.append(f"交易次数: {trade_count}")
            self.result_text.append(f"胜率: {win_rate:.2f}%")
            self.result_text.append(f"盈亏比: {profit_ratio:.2f}")
            self.result_text.append(f"平均持仓周期: {avg_holding_period:.1f} 天")
            
            # 如果是进阶模式，显示AI指标
            if selected_mode == 'evolving' and ai_metrics:
                self.result_text.append(f"\n===== AI 增强指标 =====")
                self.result_text.append(f"策略适应性评分: {strategy_adaptation_score:.2f}")
                
                for metric_name, metric_value in ai_metrics.items():
                    if isinstance(metric_value, (int, float)):
                        self.result_text.append(f"{metric_name}: {metric_value:.4f}")
                    elif isinstance(metric_value, dict):
                        self.result_text.append(f"{metric_name}:")
                        for sub_key, sub_value in metric_value.items():
                            if isinstance(sub_value, (int, float)):
                                self.result_text.append(f"  {sub_key}: {sub_value:.4f}")
            
            # 保存回测结果
            try:
                with open('backtest_results.json', 'w') as f:
                    import json
                    
                    # 组织回测结果数据
                    result_data = {
                        'stock_code': stock_code,
                        'strategy': strategy,
                        'backtest_mode': backtest_mode,
                        'learning_enabled': learning_enabled if selected_mode in ['adaptive', 'evolving'] else False,
                        'start_date': start_date,
                        'end_date': end_date,
                        'initial_capital': initial_capital,
                        'final_capital': final_capital,
                        'total_return': total_return,
                        'annual_return': annual_return,
                        'max_drawdown': max_drawdown,
                        'sharpe_ratio': sharpe_ratio,
                        'trade_count': trade_count,
                        'win_rate': win_rate,
                        'profit_ratio': profit_ratio,
                        'avg_holding_period': avg_holding_period,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 如果有AI指标，也保存它们
                    if selected_mode == 'evolving':
                        result_data['strategy_adaptation_score'] = strategy_adaptation_score
                        result_data['ml_metrics'] = ai_metrics
                    
                    json.dump(result_data, f, indent=4)
                    
                self.result_text.append("\n回测结果已保存到 backtest_results.json")
            except Exception as e:
                self.result_text.append(f"\n保存回测结果时出错: {str(e)}")
                
            # 显示结果页面，直到用户关闭
            while result_dialog.isVisible():
                QApplication.processEvents()
                
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.result_text.clear()
            self.result_text.append(f"回测过程中出错: {str(e)}")
            self.result_text.append("\n详细错误信息:")
            self.result_text.append(error_msg)
            self.logger.error(f"回测错误: {str(e)}\n{error_msg}")
        
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
        
    def analyze_sectors(self):
        """分析热门行业"""
        try:
            # 使用集成器获取行业数据
            if hasattr(self, 'enhanced_sector_available') and self.enhanced_sector_available:
                # 使用增强版分析器
                from integrate_enhanced_sector import EnhancedSectorIntegrator
                integrator = EnhancedSectorIntegrator()
                is_enhanced = True
                self.logger.info("使用增强版行业分析器")
            else:
                # 使用简化版分析器
                from integrate_sector_analyzer import SectorAnalyzerIntegrator
                integrator = SectorAnalyzerIntegrator()
                is_enhanced = False
                self.logger.info("使用简化版行业分析器")
            
            # 清空之前的结果
            self.result_text.clear()
            self.result_text.append('正在分析行业数据...')
            QApplication.processEvents()
            
            # 获取当前热门行业
            current_result = integrator.get_hot_sectors()
            if current_result['status'] != 'success':
                raise Exception(current_result.get('message', '获取热门行业失败'))
                
            # 获取统一分析结果（包含技术分析）
            unified_result = integrator.get_unified_analysis()
            
            # 如果是增强版，生成投资报告
            investment_report = None
            if is_enhanced:
                investment_report = integrator.generate_investment_report()
            
            # 显示结果
            self.result_text.clear()
            title_prefix = "增强版" if is_enhanced else ""
            self.result_text.append(f'==== {title_prefix}热门行业分析 ====')
            self.result_text.append(f'[更新时间] {current_result["data"]["update_time"]}')
            self.result_text.append('')
            
            # 显示热门行业列表
            self.result_text.append('== 当前热门行业 ==')
            for i, sector in enumerate(current_result['data']['hot_sectors'][:10], 1):
                hot_level = sector.get('hot_level', '')
                hot_score = sector.get('hot_score', 0)
                
                # 获取技术评分（如果有）
                tech_score_str = ""
                if is_enhanced:
                    tech_score = sector.get('tech_score', '')
                    tech_score_str = f" | 技术评分: {tech_score}" if tech_score else ""
                
                self.result_text.append(f'{i}. {sector["name"]} - 热度: {hot_score:.2f} ({hot_level}){tech_score_str}')
            
            # 如果有技术分析数据，显示技术分析结果
            if 'technical_analysis' in unified_result['data']:
                tech = unified_result['data']['technical_analysis']
                self.result_text.append('')
                self.result_text.append(f'== {tech["sector"]}行业技术分析 ==')
                
                if is_enhanced:
                    # 增强版技术分析显示
                    self.result_text.append(f'趋势: {tech["trend_analysis"]["trend"]}')
                    self.result_text.append(f'看多指数: {tech["tech_score"]}')
                    self.result_text.append(f'分析: {tech["trend_analysis"]["description"]}')
                    
                    # 显示技术指标
                    self.result_text.append('')
                    self.result_text.append('技术指标信号:')
                    for indicator, data in tech['indicators'].items():
                        if 'signal' in data:
                            self.result_text.append(f'- {indicator.upper()}: {data["signal"]}')
                    
                    # 显示交易信号
                    if 'trade_signal' in tech:
                        self.result_text.append('')
                        self.result_text.append(f'交易信号: {tech["trade_signal"]["action"]}')
                        self.result_text.append(f'信号强度: {tech["trade_signal"]["strength"]}')
                        if 'description' in tech["trade_signal"]:
                            self.result_text.append(f'说明: {tech["trade_signal"]["description"]}')
            else:
                    # 简化版技术分析显示
                    self.result_text.append(f'趋势: {tech["prediction"]["trend"]}')
                    self.result_text.append(f'看多指数: {tech["prediction"]["bull_score"]}')
                    self.result_text.append(f'分析: {tech["prediction"]["analysis"]}')
            
            # 如果是增强版且有投资报告，显示投资报告
            if is_enhanced and investment_report and investment_report['status'] == 'success':
                report = investment_report['data']
                self.result_text.append('')
                self.result_text.append('== 行业投资报告 ==')
                
                # 安全获取市场趋势
                market_trend = report.get('market_trend', '中性')
                self.result_text.append(f'市场趋势: {market_trend}')
                
                # 安全获取市场评论
                market_comment = report.get('market_comment', '')
                if market_comment:
                    self.result_text.append(f'整体评论: {market_comment}')
                elif 'market_overview' in report and 'comment' in report['market_overview']:
                    self.result_text.append(f'整体评论: {report["market_overview"]["comment"]}')
                
                # 显示投资建议
                if 'recommendations' in report and report['recommendations']:
                    self.result_text.append('')
                    self.result_text.append('投资建议:')
                    for i, rec in enumerate(report['recommendations'][:3], 1):
                        action = rec.get('action', rec.get('investment_advice', '观望'))
                        self.result_text.append(f'{i}. {rec["sector"]}: {action}')
                        if 'reason' in rec:
                            self.result_text.append(f'   理由: {rec["reason"]}')
                
                # 显示风险因素
                if 'risk_factors' in report and report['risk_factors']:
                    self.result_text.append('')
                    self.result_text.append('风险因素:')
                    for risk in report['risk_factors']:
                        self.result_text.append(f'- {risk}')
            
            self.logger.info(f"{'增强版' if is_enhanced else ''}行业分析完成")
            
        except Exception as e:
            self.result_text.clear()
            self.result_text.append(f'分析行业数据失败: {str(e)}')
            self.logger.error(f"分析行业数据失败: {str(e)}")
            QMessageBox.warning(self, '错误', f'分析行业数据失败: {str(e)}')

    def display_analysis(self, recommendations):
        self.result_text.clear()
        self.result_text.append('=== 市场分析报告 ===\n')
        self.result_text.append(f'分析时间：{pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        # 导入智能推荐系统
        try:
            from smart_recommendation_system import get_recommendation_system, create_recommendation
            recommendation_system = get_recommendation_system()
            added_count = 0
        except Exception as e:
            self.logger.error(f"导入智能推荐系统失败: {str(e)}")
            recommendation_system = None
        
        self.result_text.append('最具投资价值的股票：')
        for stock in recommendations:
            stock_name = self.visual_system.get_stock_name(stock['symbol'])
            self.result_text.append(f"\n股票代码：{stock['symbol']} {stock_name}")
            self.result_text.append(f"当前趋势：{stock['trend']}")
            self.result_text.append(f"收盘价：{stock['close']:.2f}")
            self.result_text.append(f"成交量/20日均量：{stock['volume']/stock['volume_ma20']:.2f}")
            self.result_text.append(f"MACD柱状图：{stock['macd_hist']:.4f}")
            self.result_text.append(f"ATR：{stock['atr']:.4f}")
            
            recommendation = stock.get('recommendation', '观望')
            self.result_text.append(f"建议：{recommendation}")
            
            # 如果是强烈推荐买入的股票，添加到智能推荐系统
            if recommendation_system and '买入' in recommendation and ('强烈' in recommendation or '积极' in recommendation):
                try:
                    # 计算推荐评分 (0-100)
                    score = 75.0  # 基础分
                    
                    # 趋势加分
                    if stock['trend'] == 'uptrend':
                        score += 10.0
                    
                    # MACD信号加分
                    if stock['macd_hist'] > 0:
                        score += 5.0 * min(1.0, abs(stock['macd_hist']) * 10)
                    
                    # 成交量加分
                    volume_ratio = stock['volume'] / stock['volume_ma20']
                    if volume_ratio > 1.2:
                        score += 5.0 * min(1.0, (volume_ratio - 1.0) * 2)
                    
                    # 设置目标价和止损价
                    current_price = stock['close']
                    target_price = current_price * 1.15  # 目标15%收益
                    stop_loss = current_price * 0.92  # 8%止损
                    
                    # 创建推荐理由
                    reason = f"{recommendation}。技术面：{stock['trend']}趋势"
                    if 'macd_hist' in stock and stock['macd_hist'] > 0:
                        reason += f"，MACD金叉信号({stock['macd_hist']:.4f})"
                    if volume_ratio > 1.2:
                        reason += f"，成交量放大({volume_ratio:.2f}倍)"
                    
                    # 创建标签
                    tags = []
                    if 'industry' in stock and stock['industry']:
                        tags.append(stock['industry'])
                    if 'concept' in stock and stock['concept']:
                        tags.append(stock['concept'])
                    if stock['trend'] == 'uptrend':
                        tags.append('上升趋势')
                    if 'macd_hist' in stock and stock['macd_hist'] > 0:
                        tags.append('MACD金叉')
                    if volume_ratio > 1.2:
                        tags.append('成交量放大')
                    
                    # 创建推荐对象
                    new_recommendation = create_recommendation(
                        stock_code=stock['symbol'],
                        stock_name=stock_name,
                        entry_price=current_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        reason=reason,
                        source="全市场扫描",
                        score=min(100, score),
                        tags=tags
                    )
                    
                    # 添加到推荐系统
                    added = recommendation_system.add_recommendation(new_recommendation)
                    if added:
                        added_count += 1
                        self.result_text.append(f"  [已添加到智能推荐系统，评分: {score:.1f}]")
                    
                except Exception as e:
                    self.logger.error(f"添加股票 {stock['symbol']} 到推荐系统失败: {str(e)}")
            
            self.result_text.append('-' * 30)
            
        # 显示添加统计
        if recommendation_system and added_count > 0:
            self.result_text.append(f"\n已将 {added_count} 只强烈推荐股票添加到智能推荐系统")

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

    def open_smart_recommendation(self):
        """打开智能推荐系统"""
        try:
            self.result_text.append("正在打开智能股票推荐系统...")
            QApplication.processEvents()
            
            # 导入智能推荐系统UI
            from smart_recommendation_ui import SmartRecommendationWidget
            
            # 创建一个新窗口显示智能推荐系统
            self.result_text.append("正在启动智能推荐系统，请稍候...")
            QApplication.processEvents()
            
            # 创建窗口 (使用当前应用的QApplication实例)
            self.rec_window = QMainWindow()
            self.rec_window.setWindowTitle("智能股票推荐系统")
            self.rec_window.resize(900, 700)
            
            # 创建智能推荐界面
            recommendation_widget = SmartRecommendationWidget()
            self.rec_window.setCentralWidget(recommendation_widget)
            
            # 显示窗口
            self.rec_window.show()
            
            self.result_text.append("智能推荐系统已启动")
            
        except Exception as e:
            self.logger.error(f"打开智能推荐系统出错: {str(e)}")
            self.result_text.append(f"打开出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            QMessageBox.warning(self, '错误', f'打开智能推荐系统时出错: {str(e)}')

# 添加主入口代码
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = StockAnalyzerApp()
    window.show()
    sys.exit(app.exec_())