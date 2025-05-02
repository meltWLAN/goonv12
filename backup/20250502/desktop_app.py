"""
桌面应用入口
提供图形界面访问系统功能
"""

import sys
import os
import asyncio
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                            QTextEdit, QTableWidget, QTableWidgetItem, QStatusBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from datetime import datetime
from main import SystemManager

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("股票数据分析系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化系统管理器
        self.system = SystemManager()
        self.system_started = False
        
        # 设置中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建标签页
        self._create_tabs()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("系统就绪")
        
        # 设置定时器更新状态
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)  # 每5秒更新一次
        
        # 初始化日志显示
        self._setup_logging()

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        start_action = file_menu.addAction("启动系统")
        start_action.triggered.connect(self.start_system)
        stop_action = file_menu.addAction("停止系统")
        stop_action.triggered.connect(self.stop_system)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        refresh_action = view_menu.addAction("刷新")
        refresh_action.triggered.connect(self.refresh_data)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        config_action = tools_menu.addAction("配置")
        config_action.triggered.connect(self.show_config)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("工具栏")
        
        # 启动按钮
        start_btn = QPushButton("启动系统")
        start_btn.clicked.connect(self.start_system)
        toolbar.addWidget(start_btn)
        
        # 停止按钮
        stop_btn = QPushButton("停止系统")
        stop_btn.clicked.connect(self.stop_system)
        toolbar.addWidget(stop_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新数据")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)

    def _create_tabs(self):
        """创建标签页"""
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # 系统状态标签页
        self.status_tab = QWidget()
        self.status_layout = QVBoxLayout(self.status_tab)
        self.status_table = QTableWidget()
        self.status_layout.addWidget(self.status_table)
        self.tabs.addTab(self.status_tab, "系统状态")
        
        # 数据监控标签页
        self.monitor_tab = QWidget()
        self.monitor_layout = QVBoxLayout(self.monitor_tab)
        self.monitor_table = QTableWidget()
        self.monitor_layout.addWidget(self.monitor_table)
        self.tabs.addTab(self.monitor_tab, "数据监控")
        
        # 日志查看标签页
        self.log_tab = QWidget()
        self.log_layout = QVBoxLayout(self.log_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_layout.addWidget(self.log_text)
        self.tabs.addTab(self.log_tab, "系统日志")

    def _setup_logging(self):
        """设置日志处理"""
        class QTextEditLogger(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget
                self.widget.setReadOnly(True)
                
            def emit(self, record):
                msg = self.format(record)
                self.widget.append(msg)
        
        log_handler = QTextEditLogger(self.log_text)
        log_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

    @pyqtSlot()
    async def start_system(self):
        """启动系统"""
        if not self.system_started:
            try:
                await self.system.start()
                self.system_started = True
                self.status_bar.showMessage("系统已启动")
                logging.info("系统已启动")
            except Exception as e:
                self.status_bar.showMessage(f"系统启动失败: {str(e)}")
                logging.error(f"系统启动失败: {str(e)}")

    @pyqtSlot()
    async def stop_system(self):
        """停止系统"""
        if self.system_started:
            try:
                await self.system.shutdown()
                self.system_started = False
                self.status_bar.showMessage("系统已停止")
                logging.info("系统已停止")
            except Exception as e:
                self.status_bar.showMessage(f"系统停止失败: {str(e)}")
                logging.error(f"系统停止失败: {str(e)}")

    @pyqtSlot()
    def refresh_data(self):
        """刷新数据显示"""
        try:
            if self.system_started:
                # 更新系统状态表格
                self._update_status_table()
                # 更新监控数据表格
                self._update_monitor_table()
                self.status_bar.showMessage("数据已刷新")
            else:
                self.status_bar.showMessage("系统未启动")
        except Exception as e:
            self.status_bar.showMessage(f"刷新数据失败: {str(e)}")
            logging.error(f"刷新数据失败: {str(e)}")

    def _update_status_table(self):
        """更新状态表格"""
        if not self.system_started:
            return
            
        # 获取组件状态
        status_data = []
        
        # 数据源状态
        if self.system.components['monitor']:
            source_status = self.system.components['monitor'].get_all_source_status()
            for source, stats in source_status.items():
                status_data.append({
                    '组件': f'数据源-{source}',
                    '状态': stats['status'],
                    '错误率': f"{stats['error_rate']:.2%}",
                    '响应时间': f"{stats['avg_response_time']:.2f}ms"
                })
        
        # 缓存状态
        if self.system.components['cache']:
            cache_stats = self.system.components['cache'].get_cache_stats()
            status_data.append({
                '组件': '缓存管理器',
                '状态': 'healthy',
                '内存使用率': f"{cache_stats['memory_cache']['utilization']:.2%}",
                '缓存项数': str(cache_stats['memory_cache']['count'])
            })
        
        # 处理器状态
        if self.system.components['processor']:
            proc_stats = self.system.components['processor'].get_stats()
            status_data.append({
                '组件': '并行处理器',
                '状态': 'healthy',
                '活动任务数': str(proc_stats['active_tasks']),
                '工作线程数': str(proc_stats['thread_pool_workers'])
            })
        
        # 更新表格
        self.status_table.setRowCount(len(status_data))
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels(['组件', '状态', '指标1', '指标2'])
        
        for i, data in enumerate(status_data):
            for j, (key, value) in enumerate(data.items()):
                item = QTableWidgetItem(str(value))
                self.status_table.setItem(i, j, item)
        
        self.status_table.resizeColumnsToContents()

    def _update_monitor_table(self):
        """更新监控数据表格"""
        if not self.system_started or not self.system.components['data_provider']:
            return
            
        try:
            # 获取预加载的股票数据
            monitor_data = []
            preload_symbols = self.system.config['data_sources']['tushare']['preload_symbols']
            
            for symbol in preload_symbols:
                data = self.system.components['data_provider'].get_stock_daily(symbol)
                if not data.empty:
                    latest = data.iloc[0]
                    monitor_data.append({
                        '股票代码': symbol,
                        '最新价': f"{latest['close']:.2f}",
                        '涨跌幅': f"{latest.get('pct_chg', 0):.2%}",
                        '成交量': f"{latest.get('volume', 0)/10000:.2f}万"
                    })
            
            # 更新表格
            self.monitor_table.setRowCount(len(monitor_data))
            self.monitor_table.setColumnCount(4)
            self.monitor_table.setHorizontalHeaderLabels(
                ['股票代码', '最新价', '涨跌幅', '成交量']
            )
            
            for i, data in enumerate(monitor_data):
                for j, (key, value) in enumerate(data.items()):
                    item = QTableWidgetItem(str(value))
                    self.monitor_table.setItem(i, j, item)
            
            self.monitor_table.resizeColumnsToContents()
            
        except Exception as e:
            logging.error(f"更新监控数据失败: {str(e)}")

    def update_status(self):
        """定时更新状态"""
        if self.system_started:
            self.refresh_data()

    def show_config(self):
        """显示配置对话框"""
        # TODO: 实现配置对话框
        pass

    def show_about(self):
        """显示关于对话框"""
        # TODO: 实现关于对话框
        pass

    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.system_started:
            asyncio.create_task(self.stop_system())
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 