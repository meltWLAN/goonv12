#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析系统GUI模块
提供图形用户界面
"""

import os
import sys
import time
import json
import logging
import traceback
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QTextEdit, QFrame, QProgressBar, QMessageBox,
    QScrollArea, QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='gui.log',
    filemode='a'
)
logger = logging.getLogger('StockGUI')

class HotSectorsWidget(QWidget):
    """热门行业组件"""
    
    def __init__(self, sector_integrator=None):
        super().__init__()
        self.sector_integrator = sector_integrator
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.init_ui()
        self.is_enhanced = False
        
        # 检查是否有增强版分析器
        if sector_integrator and hasattr(sector_integrator, 'enhanced_available'):
            self.is_enhanced = sector_integrator.enhanced_available
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题区域
        title_layout = QHBoxLayout()
        self.title_label = QLabel("热门行业分析")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_layout.addWidget(self.title_label)
        
        # 添加更新时间标签
        self.time_label = QLabel("最后更新: 未更新")
        self.time_label.setAlignment(Qt.AlignRight)
        title_layout.addWidget(self.time_label)
        
        # 添加刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.manual_update)
        title_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(title_layout)
        
        # 添加数据源信息
        info_layout = QHBoxLayout()
        self.source_label = QLabel("数据源: 未知")
        info_layout.addWidget(self.source_label)
        
        # 如果是增强版，显示版本标签
        self.version_label = QLabel()
        info_layout.addWidget(self.version_label)
        
        # 填充空间
        info_layout.addStretch()
        
        # 市场状态信息
        self.market_label = QLabel("市场状态: 未知")
        info_layout.addWidget(self.market_label)
        
        layout.addLayout(info_layout)
        
        # 表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["行业", "热度", "状态", "交易信号", "分析"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # 技术分析区域
        self.add_tech_analysis_area(layout)
        
        # 启动定时更新
        self.update_timer.start(60000)  # 1分钟更新一次
        
        # 立即更新一次
        QTimer.singleShot(100, self.update_data)
    
    def add_tech_analysis_area(self, parent_layout):
        """添加技术分析区域"""
        # 顶级标题
        tech_title = QLabel("行业技术分析")
        tech_title.setFont(QFont("Arial", 12, QFont.Bold))
        parent_layout.addWidget(tech_title)
        
        # 行业选择
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("选择行业:"))
        self.sector_combo = QComboBox()
        selection_layout.addWidget(self.sector_combo)
        
        # 添加分析按钮
        self.analyze_btn = QPushButton("分析")
        self.analyze_btn.clicked.connect(self.analyze_selected_sector)
        selection_layout.addWidget(self.analyze_btn)
        
        # 添加间隔
        selection_layout.addStretch()
        
        parent_layout.addLayout(selection_layout)
        
        # 技术分析内容区域 (使用QScrollArea包装)
        self.tech_scroll = QScrollArea()
        self.tech_scroll.setWidgetResizable(True)
        self.tech_scroll.setFrameShape(QFrame.NoFrame)
        
        # 创建内容容器
        self.tech_container = QWidget()
        self.tech_layout = QVBoxLayout(self.tech_container)
        
        # 技术评分和趋势
        self.score_label = QLabel("技术评分: 未知")
        self.score_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.tech_layout.addWidget(self.score_label)
        
        self.trend_label = QLabel("趋势: 未知")
        self.tech_layout.addWidget(self.trend_label)
        
        # 技术指标组
        indicators_group = QGroupBox("技术指标")
        indicators_layout = QVBoxLayout()
        self.macd_label = QLabel("MACD: 未知")
        self.kdj_label = QLabel("KDJ: 未知") 
        self.rsi_label = QLabel("RSI: 未知")
        self.ma_label = QLabel("均线: 未知")
        self.boll_label = QLabel("布林带: 未知")
        
        indicators_layout.addWidget(self.macd_label)
        indicators_layout.addWidget(self.kdj_label)
        indicators_layout.addWidget(self.rsi_label)
        indicators_layout.addWidget(self.ma_label)
        indicators_layout.addWidget(self.boll_label)
        indicators_group.setLayout(indicators_layout)
        self.tech_layout.addWidget(indicators_group)
        
        # 交易信号组
        signal_group = QGroupBox("交易信号")
        signal_layout = QVBoxLayout()
        self.signal_label = QLabel("信号: 未知")
        self.action_label = QLabel("建议: 未知")
        self.desc_label = QLabel("说明: 未知")
        
        signal_layout.addWidget(self.signal_label)
        signal_layout.addWidget(self.action_label)
        signal_layout.addWidget(self.desc_label)
        signal_group.setLayout(signal_layout)
        self.tech_layout.addWidget(signal_group)
        
        # 设置滚动区域的部件
        self.tech_scroll.setWidget(self.tech_container)
        parent_layout.addWidget(self.tech_scroll)
    
    def analyze_selected_sector(self):
        """分析选中的行业"""
        if not self.sector_integrator:
            self.show_message("错误", "行业分析器不可用")
            return
        
        sector_name = self.sector_combo.currentText()
        if not sector_name:
            return
        
        try:
            # 获取行业技术分析
            result = self.sector_integrator.get_sector_technical_analysis(sector_name)
            
            if result['status'] != 'success':
                self.show_message("分析失败", result.get('message', '未知错误'))
                return
            
            # 更新技术分析显示
            self.update_tech_analysis_ui(result['data'])
            
        except Exception as e:
            logger.error(f"行业分析失败: {e}")
            self.show_message("错误", f"行业分析失败: {str(e)}")
    
    def update_tech_analysis_ui(self, data):
        """更新技术分析界面"""
        # 更新技术评分
        self.score_label.setText(f"技术评分: {data.get('tech_score', 0)}/100")
        
        # 更新趋势
        trend = data.get('trend_analysis', {})
        if trend:
            trend_text = (f"趋势: {trend.get('trend', '未知')} "
                          f"(强度: {trend.get('strength', 0)})\n"
                          f"支撑位: {trend.get('support', 0)} | "
                          f"阻力位: {trend.get('resistance', 0)}\n"
                          f"{trend.get('analysis', '')}")
            self.trend_label.setText(trend_text)
        
        # 更新技术指标
        indicators = data.get('indicators', {})
        if indicators:
            if 'macd' in indicators:
                self.macd_label.setText(f"MACD: {indicators['macd'].get('signal', '未知')}")
            if 'kdj' in indicators:
                self.kdj_label.setText(f"KDJ: {indicators['kdj'].get('signal', '未知')}")
            if 'rsi' in indicators:
                self.rsi_label.setText(f"RSI: {indicators['rsi'].get('signal', '未知')}")
            if 'ma' in indicators:
                self.ma_label.setText(f"均线: {indicators['ma'].get('signal', '未知')}")
            if 'boll' in indicators:
                self.boll_label.setText(f"布林带: {indicators['boll'].get('signal', '未知')}")
        
        # 更新交易信号
        signal = data.get('trade_signal', {})
        if signal:
            self.signal_label.setText(f"信号: {signal.get('signal', '未知')}")
            self.action_label.setText(f"建议: {signal.get('action', '无')}")
            self.desc_label.setText(f"说明: {signal.get('description', '无')}")
    
    def show_message(self, title, message):
        """显示消息对话框"""
        QMessageBox.information(self, title, message)
    
    def manual_update(self):
        """手动更新数据"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("更新中...")
        self.update_data()
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")
    
    def update_data(self):
        """更新数据"""
        if not self.sector_integrator:
            self.time_label.setText("最后更新: 分析器不可用")
            return
        
        try:
            # 获取统一格式的行业分析
            result = self.sector_integrator.get_unified_analysis()
            
            if result['status'] != 'success':
                logger.error(f"获取行业数据失败: {result.get('message')}")
                self.time_label.setText(f"最后更新: 失败 ({time.strftime('%H:%M:%S')})")
                return
            
            # 更新时间标签
            update_time = result['data'].get('update_time', time.strftime('%Y-%m-%d %H:%M:%S'))
            self.time_label.setText(f"最后更新: {update_time}")
            
            # 更新数据源标签
            data_source = result['data'].get('source', '未知')
            self.source_label.setText(f"数据源: {data_source}")
            
            # 更新版本标签
            analyzer_version = result['data'].get('analyzer_version', '')
            if analyzer_version == 'enhanced':
                self.version_label.setText("版本: 增强版")
            else:
                self.version_label.setText("")
            
            # 更新市场状态
            market_trend = result['data'].get('market_trend', 'neutral')
            market_change = result['data'].get('market_chg_pct', 0.0)
            market_display = "震荡"
            if market_trend == 'strong_bull':
                market_display = "强势上涨"
            elif market_trend == 'bull':
                market_display = "上涨"
            elif market_trend == 'strong_bear':
                market_display = "强势下跌"
            elif market_trend == 'bear':
                market_display = "下跌"
            
            self.market_label.setText(f"市场状态: {market_display} ({market_change:+.2f}%)")
            
            # 更新表格
            hot_sectors = result['data'].get('hot_sectors', [])
            self.table.setRowCount(len(hot_sectors))
            
            # 清空行业选择框并重新填充
            self.sector_combo.clear()
            
            for i, sector in enumerate(hot_sectors):
                # 添加到行业选择框
                self.sector_combo.addItem(sector['name'])
                
                # 填充表格
                self.table.setItem(i, 0, QTableWidgetItem(sector['name']))
                
                # 热度项
                hot_score = sector.get('hot_score', 0)
                hot_item = QTableWidgetItem(f"{hot_score:.1f}")
                # 根据热度设置颜色
                if hot_score >= 70:
                    hot_item.setBackground(QColor(255, 200, 200))  # 红色 (热)
                elif hot_score >= 50:
                    hot_item.setBackground(QColor(255, 230, 200))  # 橙色 (偏热)
                elif hot_score <= 30:
                    hot_item.setBackground(QColor(200, 200, 255))  # 蓝色 (冷)
                hot_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 1, hot_item)
                
                # 状态项
                status_item = QTableWidgetItem(sector.get('industry_status', '未知'))
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 2, status_item)
                
                # 交易信号
                signal_item = QTableWidgetItem(sector.get('trade_signal', '未知'))
                signal_item.setTextAlignment(Qt.AlignCenter)
                # 根据信号设置颜色
                signal = sector.get('trade_signal', '')
                if signal in ['买入', '强烈买入']:
                    signal_item.setBackground(QColor(200, 255, 200))  # 绿色 (买入)
                elif signal in ['卖出', '强烈卖出']:
                    signal_item.setBackground(QColor(255, 200, 200))  # 红色 (卖出)
                self.table.setItem(i, 3, signal_item)
                
                # 分析
                self.table.setItem(i, 4, QTableWidgetItem(sector.get('analysis', '')))
            
            # 调整表格列宽
            self.table.resizeColumnsToContents()
            
            # 如果有技术分析数据，更新技术分析区域
            if 'technical_analysis' in result['data']:
                self.update_tech_analysis_ui(result['data']['technical_analysis'])
                
                # 选择第一个行业
                if self.sector_combo.count() > 0:
                    self.sector_combo.setCurrentIndex(0)
            
        except Exception as e:
            logger.error(f"更新热门行业数据失败: {e}")
            logger.error(traceback.format_exc())
            self.time_label.setText(f"最后更新: 错误 ({time.strftime('%H:%M:%S')})")

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, sector_integrator=None):
        super().__init__()
        self.sector_integrator = sector_integrator
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("股票分析系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        tabs = QTabWidget()
        
        # 添加热门行业标签页
        hot_sectors_widget = HotSectorsWidget(self.sector_integrator)
        tabs.addTab(hot_sectors_widget, "热门行业分析")
        
        # 添加其他标签页
        tabs.addTab(QWidget(), "个股分析")
        tabs.addTab(QWidget(), "自选股")
        tabs.addTab(QWidget(), "系统设置")
        
        main_layout.addWidget(tabs)
        
        # 状态栏
        self.statusBar().showMessage("系统就绪")
        
        # 检查是否有增强版的集成器
        has_enhanced = False
        if self.sector_integrator and hasattr(self.sector_integrator, 'enhanced_available'):
            has_enhanced = self.sector_integrator.enhanced_available
        
        if has_enhanced:
            self.statusBar().showMessage("系统就绪（增强版行业分析器已启动）")
        else:
            self.statusBar().showMessage("系统就绪（使用简化版行业分析器）")
        
        # 显示窗口
        self.show()

def launch_gui(sector_integrator=None):
    """启动GUI函数"""
    try:
        app = QApplication(sys.argv)
        window = MainWindow(sector_integrator)
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"启动GUI失败: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # 如果直接运行此文件，尝试创建行业分析器集成器
    try:
        from integrate_sector_analyzer import SectorAnalyzerIntegrator
        integrator = SectorAnalyzerIntegrator()
        launch_gui(integrator)
    except ImportError:
        # 如果无法导入，则启动没有集成器的GUI
        launch_gui(None)
    except Exception as e:
        logger.error(f"创建集成器失败: {e}")
        launch_gui(None) 