#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
独立的复盘池UI展示模块 - 使用PyQt5实现
"""

import os
import json
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, 
                             QTabWidget, QHeaderView, QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor

class ReviewPoolUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()
        
    def initUI(self):
        # 设置窗口
        self.setWindowTitle('股票复盘池查看器')
        self.setGeometry(100, 100, 1000, 600)
        
        # 创建主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 添加顶部标题
        title_label = QLabel('股票复盘池查看器')
        title_label.setFont(QFont('PingFang SC', 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建标签页组件
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont('PingFang SC', 12))
        
        # 创建三个标签页
        self.basic_tab = QWidget()
        self.enhanced_tab = QWidget()
        self.smart_tab = QWidget()
        
        self.tab_widget.addTab(self.basic_tab, '基础复盘池')
        self.tab_widget.addTab(self.enhanced_tab, '增强版复盘池')
        self.tab_widget.addTab(self.smart_tab, '智能复盘池')
        
        # 设置标签页内容
        self.setup_basic_tab()
        self.setup_enhanced_tab()
        self.setup_smart_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 添加底部按钮区域
        button_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_btn = QPushButton('刷新数据')
        refresh_btn.setFont(QFont('PingFang SC', 12))
        refresh_btn.setMinimumSize(120, 35)
        refresh_btn.clicked.connect(self.loadData)
        button_layout.addWidget(refresh_btn)
        
        # 修复按钮
        fix_btn = QPushButton('修复复盘池')
        fix_btn.setFont(QFont('PingFang SC', 12))
        fix_btn.setMinimumSize(120, 35)
        fix_btn.clicked.connect(self.fixReviewPools)
        button_layout.addWidget(fix_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 添加状态栏
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage('准备就绪')
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QTableWidget {
                background-color: #f5f5f5;
                gridline-color: #d0d0d0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
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
    
    def setup_basic_tab(self):
        """设置基础复盘池标签页"""
        layout = QVBoxLayout(self.basic_tab)
        
        # 创建表格
        self.basic_table = QTableWidget()
        self.basic_table.setColumnCount(7)
        self.basic_table.setHorizontalHeaderLabels(['代码', '名称', '状态', '添加日期', '分析得分', '市场状态', '推荐'])
        self.basic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.basic_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.basic_table)
        
        # 添加信息标签
        self.basic_info_label = QLabel()
        self.basic_info_label.setFont(QFont('PingFang SC', 10))
        layout.addWidget(self.basic_info_label)
    
    def setup_enhanced_tab(self):
        """设置增强版复盘池标签页"""
        layout = QVBoxLayout(self.enhanced_tab)
        
        # 创建表格
        self.enhanced_table = QTableWidget()
        self.enhanced_table.setColumnCount(7)
        self.enhanced_table.setHorizontalHeaderLabels(['代码', '名称', '状态', '添加日期', '分析得分', '市场状态', '推荐'])
        self.enhanced_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.enhanced_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.enhanced_table)
        
        # 添加信息标签
        self.enhanced_info_label = QLabel()
        self.enhanced_info_label.setFont(QFont('PingFang SC', 10))
        layout.addWidget(self.enhanced_info_label)
    
    def setup_smart_tab(self):
        """设置智能复盘池标签页"""
        layout = QVBoxLayout(self.smart_tab)
        
        # 创建表格
        self.smart_table = QTableWidget()
        self.smart_table.setColumnCount(7)
        self.smart_table.setHorizontalHeaderLabels(['代码', '名称', '状态', '添加日期', '智能评分', '重要性', '标签'])
        self.smart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.smart_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.smart_table)
        
        # 添加信息标签
        self.smart_info_label = QLabel()
        self.smart_info_label.setFont(QFont('PingFang SC', 10))
        layout.addWidget(self.smart_info_label)
    
    def loadData(self):
        """加载所有复盘池数据"""
        self.statusBar().showMessage('正在加载数据...')
        
        # 加载基础复盘池
        self.load_basic_pool()
        
        # 加载增强版复盘池
        self.load_enhanced_pool()
        
        # 加载智能复盘池
        self.load_smart_pool()
        
        self.statusBar().showMessage('数据加载完成')
    
    def load_basic_pool(self):
        """加载基础复盘池数据"""
        review_pool_file = 'review_pool.json'
        
        try:
            if not os.path.exists(review_pool_file):
                self.basic_info_label.setText('基础复盘池文件不存在')
                return
            
            with open(review_pool_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks = data.get('stocks', [])
            last_updated = data.get('last_updated', '')
            
            # 清空表格
            self.basic_table.setRowCount(0)
            
            # 填充表格
            watching_count = 0
            bought_count = 0
            sold_count = 0
            
            for stock in stocks:
                status = stock.get('status', '')
                if status == 'watching':
                    watching_count += 1
                elif status == 'bought':
                    bought_count += 1
                elif status == 'sold':
                    sold_count += 1
                
                row = self.basic_table.rowCount()
                self.basic_table.insertRow(row)
                
                # 设置单元格内容
                self.basic_table.setItem(row, 0, QTableWidgetItem(stock.get('symbol', '')))
                self.basic_table.setItem(row, 1, QTableWidgetItem(stock.get('name', '')))
                self.basic_table.setItem(row, 2, QTableWidgetItem(status))
                self.basic_table.setItem(row, 3, QTableWidgetItem(stock.get('date_added', '')))
                self.basic_table.setItem(row, 4, QTableWidgetItem(str(stock.get('analysis_score', ''))))
                self.basic_table.setItem(row, 5, QTableWidgetItem(stock.get('market_status', '')))
                self.basic_table.setItem(row, 6, QTableWidgetItem(stock.get('recommendation', '')))
                
                # 设置单元格颜色
                if status == 'watching':
                    self._set_row_color(self.basic_table, row, QColor(240, 240, 255))  # 浅蓝色
                elif status == 'bought':
                    self._set_row_color(self.basic_table, row, QColor(240, 255, 240))  # 浅绿色
                elif status == 'sold':
                    self._set_row_color(self.basic_table, row, QColor(255, 240, 240))  # 浅红色
            
            # 更新信息标签
            info_text = f"总股票数: {len(stocks)}只 | 观察中: {watching_count}只 | 已买入: {bought_count}只 | 已卖出: {sold_count}只 | 最后更新: {last_updated}"
            self.basic_info_label.setText(info_text)
            
        except Exception as e:
            self.basic_info_label.setText(f'加载基础复盘池失败: {str(e)}')
    
    def load_enhanced_pool(self):
        """加载增强版复盘池数据"""
        enhanced_review_file = 'enhanced_review_pool.json'
        
        try:
            if not os.path.exists(enhanced_review_file):
                self.enhanced_info_label.setText('增强版复盘池文件不存在')
                return
            
            with open(enhanced_review_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks = data.get('stocks', [])
            settings = data.get('settings', {})
            last_updated = settings.get('last_updated', '')
            
            # 清空表格
            self.enhanced_table.setRowCount(0)
            
            # 填充表格
            watching_count = 0
            bought_count = 0
            sold_count = 0
            
            for stock in stocks:
                status = stock.get('status', '')
                if status == 'watching':
                    watching_count += 1
                elif status == 'bought':
                    bought_count += 1
                elif status == 'sold':
                    sold_count += 1
                
                row = self.enhanced_table.rowCount()
                self.enhanced_table.insertRow(row)
                
                # 设置单元格内容
                self.enhanced_table.setItem(row, 0, QTableWidgetItem(stock.get('symbol', '')))
                self.enhanced_table.setItem(row, 1, QTableWidgetItem(stock.get('name', '')))
                self.enhanced_table.setItem(row, 2, QTableWidgetItem(status))
                self.enhanced_table.setItem(row, 3, QTableWidgetItem(stock.get('date_added', '')))
                self.enhanced_table.setItem(row, 4, QTableWidgetItem(str(stock.get('analysis_score', ''))))
                self.enhanced_table.setItem(row, 5, QTableWidgetItem(stock.get('market_status', '')))
                self.enhanced_table.setItem(row, 6, QTableWidgetItem(stock.get('recommendation', '')))
                
                # 设置单元格颜色
                if status == 'watching':
                    self._set_row_color(self.enhanced_table, row, QColor(240, 240, 255))  # 浅蓝色
                elif status == 'bought':
                    self._set_row_color(self.enhanced_table, row, QColor(240, 255, 240))  # 浅绿色
                elif status == 'sold':
                    self._set_row_color(self.enhanced_table, row, QColor(255, 240, 240))  # 浅红色
            
            # 更新信息标签
            data_source = settings.get('data_source', '未知')
            auto_update = '开启' if settings.get('auto_update') else '关闭'
            info_text = f"总股票数: {len(stocks)}只 | 观察中: {watching_count}只 | 已买入: {bought_count}只 | 已卖出: {sold_count}只 | 数据源: {data_source} | 自动更新: {auto_update} | 最后更新: {last_updated}"
            self.enhanced_info_label.setText(info_text)
            
        except Exception as e:
            self.enhanced_info_label.setText(f'加载增强版复盘池失败: {str(e)}')
    
    def load_smart_pool(self):
        """加载智能复盘池数据"""
        smart_review_file = './smart_review_data/smart_review_pool.json'
        
        try:
            if not os.path.exists(smart_review_file):
                self.smart_info_label.setText('智能复盘池文件不存在')
                return
            
            with open(smart_review_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks = data.get('stocks', [])
            last_updated = data.get('last_updated', '')
            version = data.get('version', '')
            
            # 清空表格
            self.smart_table.setRowCount(0)
            
            # 填充表格
            watching_count = 0
            bought_count = 0
            sold_count = 0
            
            for stock in stocks:
                status = stock.get('status', '')
                if status == 'watching':
                    watching_count += 1
                elif status == 'bought':
                    bought_count += 1
                elif status == 'sold':
                    sold_count += 1
                
                row = self.smart_table.rowCount()
                self.smart_table.insertRow(row)
                
                # 设置单元格内容
                self.smart_table.setItem(row, 0, QTableWidgetItem(stock.get('symbol', '')))
                self.smart_table.setItem(row, 1, QTableWidgetItem(stock.get('name', '')))
                self.smart_table.setItem(row, 2, QTableWidgetItem(status))
                self.smart_table.setItem(row, 3, QTableWidgetItem(stock.get('date_added', '')))
                self.smart_table.setItem(row, 4, QTableWidgetItem(str(stock.get('smart_score', ''))))
                self.smart_table.setItem(row, 5, QTableWidgetItem(str(stock.get('importance', ''))))
                
                # 处理标签
                tags = stock.get('tags', [])
                if tags:
                    tags_text = ', '.join(tags)
                else:
                    tags_text = ''
                self.smart_table.setItem(row, 6, QTableWidgetItem(tags_text))
                
                # 设置单元格颜色
                if status == 'watching':
                    self._set_row_color(self.smart_table, row, QColor(240, 240, 255))  # 浅蓝色
                elif status == 'bought':
                    self._set_row_color(self.smart_table, row, QColor(240, 255, 240))  # 浅绿色
                elif status == 'sold':
                    self._set_row_color(self.smart_table, row, QColor(255, 240, 240))  # 浅红色
            
            # 更新信息标签
            info_text = f"总股票数: {len(stocks)}只 | 观察中: {watching_count}只 | 已买入: {bought_count}只 | 已卖出: {sold_count}只 | 版本: {version} | 最后更新: {last_updated}"
            self.smart_info_label.setText(info_text)
            
        except Exception as e:
            self.smart_info_label.setText(f'加载智能复盘池失败: {str(e)}')
    
    def _set_row_color(self, table, row, color):
        """设置表格行的颜色"""
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                item.setBackground(color)
    
    def fixReviewPools(self):
        """修复复盘池"""
        try:
            self.statusBar().showMessage('正在修复复盘池...')
            
            # 导入并运行修复脚本
            import fix_stock_review_simple
            fix_stock_review_simple.fix_review_pools()
            
            # 重新加载数据
            self.loadData()
            
            QMessageBox.information(self, '成功', '复盘池修复成功！')
            self.statusBar().showMessage('复盘池修复成功')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'复盘池修复失败: {str(e)}')
            self.statusBar().showMessage('复盘池修复失败')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ReviewPoolUI()
    window.show()
    sys.exit(app.exec_()) 