#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能股票推荐系统 GUI 界面
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QTabWidget,
    QGroupBox, QFormLayout, QDialog, QDialogButtonBox, QMessageBox,
    QHeaderView, QSplitter, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, QDate
from PyQt5.QtGui import QColor, QDesktopServices, QFont, QIcon

# 导入推荐系统
from smart_recommendation_system import (
    get_recommendation_system, 
    create_recommendation,
    StockRecommendation
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='smart_recommendation_ui.log'
)
logger = logging.getLogger('SmartRecommendationUI')

class AddRecommendationDialog(QDialog):
    """添加推荐对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加推荐")
        self.resize(500, 600)
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.source_combo = QComboBox()
        self.source_combo.addItems(["技术分析", "基本面分析", "AI预测", "专家推荐", "量化分析", "其他"])
        
        basic_layout.addRow("股票代码:", self.code_input)
        basic_layout.addRow("股票名称:", self.name_input)
        basic_layout.addRow("推荐来源:", self.source_combo)
        
        basic_group.setLayout(basic_layout)
        
        # 价格信息
        price_group = QGroupBox("价格信息")
        price_layout = QFormLayout()
        
        self.entry_spin = QDoubleSpinBox()
        self.entry_spin.setRange(0.01, 10000.0)
        self.entry_spin.setDecimals(2)
        self.entry_spin.setSingleStep(0.1)
        
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(0.01, 10000.0)
        self.target_spin.setDecimals(2)
        self.target_spin.setSingleStep(0.1)
        
        self.stop_spin = QDoubleSpinBox()
        self.stop_spin.setRange(0.01, 10000.0)
        self.stop_spin.setDecimals(2)
        self.stop_spin.setSingleStep(0.1)
        
        self.score_spin = QSpinBox()
        self.score_spin.setRange(1, 100)
        self.score_spin.setValue(75)
        
        price_layout.addRow("建议买入价:", self.entry_spin)
        price_layout.addRow("目标价格:", self.target_spin)
        price_layout.addRow("止损价格:", self.stop_spin)
        price_layout.addRow("推荐评分:", self.score_spin)
        
        price_group.setLayout(price_layout)
        
        # 标签和理由
        tags_group = QGroupBox("标签和理由")
        tags_layout = QVBoxLayout()
        
        tags_layout.addWidget(QLabel("标签 (用逗号分隔):"))
        self.tags_input = QLineEdit()
        tags_layout.addWidget(self.tags_input)
        
        tags_layout.addWidget(QLabel("推荐理由:"))
        self.reason_text = QTextEdit()
        tags_layout.addWidget(self.reason_text)
        
        tags_group.setLayout(tags_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 添加到主布局
        layout.addWidget(basic_group)
        layout.addWidget(price_group)
        layout.addWidget(tags_group)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_recommendation_data(self):
        """获取对话框中的推荐数据"""
        stock_code = self.code_input.text().strip()
        stock_name = self.name_input.text().strip()
        entry_price = self.entry_spin.value()
        target_price = self.target_spin.value()
        stop_loss = self.stop_spin.value()
        score = self.score_spin.value()
        source = self.source_combo.currentText()
        reason = self.reason_text.toPlainText().strip()
        tags = [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        
        # 验证必填字段
        if not stock_code or not stock_name or not reason:
            return None
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'entry_price': entry_price,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'score': score,
            'source': source,
            'reason': reason,
            'tags': tags
        }

class SmartRecommendationWidget(QWidget):
    """智能推荐系统界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recommendation_system = get_recommendation_system()
        self.setup_ui()
        self.load_recommendations()
    
    def setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("智能股票推荐系统")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        
        main_layout.addWidget(title_label)
        
        # 选项卡
        tab_widget = QTabWidget()
        
        # 活跃推荐选项卡
        active_tab = QWidget()
        active_layout = QVBoxLayout()
        
        # 按钮行
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加推荐")
        self.add_btn.clicked.connect(self.add_recommendation)
        
        self.refresh_btn = QPushButton("刷新数据")
        self.refresh_btn.clicked.connect(self.load_recommendations)
        
        self.generate_report_btn = QPushButton("生成报告")
        self.generate_report_btn.clicked.connect(self.generate_report)
        
        self.clean_btn = QPushButton("清理过期")
        self.clean_btn.clicked.connect(self.clean_recommendations)
        
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.generate_report_btn)
        buttons_layout.addWidget(self.clean_btn)
        
        active_layout.addLayout(buttons_layout)
        
        # 筛选行
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("排序:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["评分", "收益率", "添加日期"])
        self.sort_combo.currentIndexChanged.connect(self.load_recommendations)
        filter_layout.addWidget(self.sort_combo)
        
        filter_layout.addWidget(QLabel("标签:"))
        self.tag_combo = QComboBox()
        self.tag_combo.addItem("全部")
        self.tag_combo.currentIndexChanged.connect(self.load_recommendations)
        filter_layout.addWidget(self.tag_combo)
        
        filter_layout.addWidget(QLabel("状态:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部", "活跃", "已达目标", "已止损"])
        self.status_combo.currentIndexChanged.connect(self.load_recommendations)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.load_recommendations)
        filter_layout.addWidget(self.search_input)
        
        active_layout.addLayout(filter_layout)
        
        # 推荐表格
        self.recommendations_table = QTableWidget(0, 9)
        self.recommendations_table.setHorizontalHeaderLabels([
            "股票代码", "股票名称", "推荐日期", "评分", "建议买入价", 
            "目标价格", "止损价格", "当前收益率", "操作"
        ])
        self.recommendations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        active_layout.addWidget(self.recommendations_table)
        
        active_tab.setLayout(active_layout)
        
        # 历史记录选项卡
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        # 历史表格
        self.history_table = QTableWidget(0, 8)
        self.history_table.setHorizontalHeaderLabels([
            "股票代码", "股票名称", "推荐日期", "删除日期", "最终收益率", 
            "原因", "评分", "推荐来源"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        history_layout.addWidget(self.history_table)
        history_tab.setLayout(history_layout)
        
        # 统计选项卡
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        
        self.stats_group = QGroupBox("系统概况")
        stats_form = QFormLayout()
        
        self.total_recs_label = QLabel("0")
        self.avg_score_label = QLabel("0.00")
        self.avg_return_label = QLabel("0.00%")
        self.success_rate_label = QLabel("0.00%")
        
        stats_form.addRow("当前活跃推荐:", self.total_recs_label)
        stats_form.addRow("平均推荐评分:", self.avg_score_label)
        stats_form.addRow("平均当前收益率:", self.avg_return_label)
        stats_form.addRow("历史成功率:", self.success_rate_label)
        
        self.stats_group.setLayout(stats_form)
        stats_layout.addWidget(self.stats_group)
        
        # 添加图表位置
        self.chart_placeholder = QLabel("图表区域")
        self.chart_placeholder.setAlignment(Qt.AlignCenter)
        self.chart_placeholder.setMinimumHeight(300)
        self.chart_placeholder.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        stats_layout.addWidget(self.chart_placeholder)
        stats_tab.setLayout(stats_layout)
        
        # 添加选项卡
        tab_widget.addTab(active_tab, "活跃推荐")
        tab_widget.addTab(history_tab, "历史记录")
        tab_widget.addTab(stats_tab, "统计分析")
        
        main_layout.addWidget(tab_widget)
        
        self.setLayout(main_layout)
    
    def load_recommendations(self):
        """加载推荐到表格"""
        # 获取所有推荐
        recommendations = self.recommendation_system.get_all_recommendations()
        
        # 应用过滤和排序
        filtered_recs = self.filter_recommendations(list(recommendations.values()))
        
        # 清空表格
        self.recommendations_table.setRowCount(0)
        
        # 填充表格
        for i, rec in enumerate(filtered_recs):
            self.recommendations_table.insertRow(i)
            
            self.recommendations_table.setItem(i, 0, QTableWidgetItem(rec.stock_code))
            self.recommendations_table.setItem(i, 1, QTableWidgetItem(rec.stock_name))
            self.recommendations_table.setItem(i, 2, QTableWidgetItem(rec.recommendation_date.strftime('%Y-%m-%d')))
            self.recommendations_table.setItem(i, 3, QTableWidgetItem(f"{rec.score:.2f}"))
            self.recommendations_table.setItem(i, 4, QTableWidgetItem(f"{rec.entry_price:.2f}"))
            self.recommendations_table.setItem(i, 5, QTableWidgetItem(f"{rec.target_price:.2f}"))
            self.recommendations_table.setItem(i, 6, QTableWidgetItem(f"{rec.stop_loss:.2f}"))
            
            # 当前收益率
            current_return = rec.performance_metrics.get('current_return', 0)
            return_item = QTableWidgetItem(f"{current_return:.2f}%")
            if current_return > 0:
                return_item.setForeground(QColor('green'))
            elif current_return < 0:
                return_item.setForeground(QColor('red'))
            self.recommendations_table.setItem(i, 7, return_item)
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            view_btn = QPushButton("查看")
            view_btn.setProperty("stock_code", rec.stock_code)
            view_btn.clicked.connect(lambda checked, code=rec.stock_code: self.view_recommendation(code))
            
            remove_btn = QPushButton("删除")
            remove_btn.setProperty("stock_code", rec.stock_code)
            remove_btn.clicked.connect(lambda checked, code=rec.stock_code: self.remove_recommendation(code))
            
            action_layout.addWidget(view_btn)
            action_layout.addWidget(remove_btn)
            action_widget.setLayout(action_layout)
            
            self.recommendations_table.setCellWidget(i, 8, action_widget)
        
        # 加载历史记录
        self.load_history()
        
        # 更新统计信息
        self.update_statistics()
        
        # 更新标签过滤器选项
        self.update_tag_filter()
    
    def filter_recommendations(self, recommendations):
        """过滤和排序推荐"""
        filtered = recommendations.copy()
        
        # 应用搜索过滤
        search_text = self.search_input.text().lower()
        if search_text:
            filtered = [
                rec for rec in filtered
                if search_text in rec.stock_code.lower() or search_text in rec.stock_name.lower()
            ]
        
        # 应用标签过滤
        selected_tag = self.tag_combo.currentText()
        if selected_tag != "全部":
            filtered = [rec for rec in filtered if selected_tag in rec.tags]
        
        # 应用状态过滤
        selected_status = self.status_combo.currentText()
        if selected_status == "活跃":
            filtered = [rec for rec in filtered if rec.status == "active"]
        elif selected_status == "已达目标":
            filtered = [
                rec for rec in filtered 
                if rec.performance_metrics.get('target_reached', False)
            ]
        elif selected_status == "已止损":
            filtered = [
                rec for rec in filtered 
                if rec.performance_metrics.get('stop_loss_triggered', False)
            ]
        
        # 应用排序
        sort_option = self.sort_combo.currentText()
        if sort_option == "评分":
            filtered.sort(key=lambda x: x.score, reverse=True)
        elif sort_option == "收益率":
            filtered.sort(
                key=lambda x: x.performance_metrics.get('current_return', 0), 
                reverse=True
            )
        elif sort_option == "添加日期":
            filtered.sort(key=lambda x: x.recommendation_date, reverse=True)
        
        return filtered
    
    def load_history(self):
        """加载历史记录"""
        history = self.recommendation_system.recommendation_history
        
        # 清空表格
        self.history_table.setRowCount(0)
        
        # 填充表格
        for i, rec in enumerate(history):
            self.history_table.insertRow(i)
            
            self.history_table.setItem(i, 0, QTableWidgetItem(rec['stock_code']))
            self.history_table.setItem(i, 1, QTableWidgetItem(rec['stock_name']))
            self.history_table.setItem(i, 2, QTableWidgetItem(rec['recommendation_date'][0:10]))
            self.history_table.setItem(i, 3, QTableWidgetItem(rec.get('removal_date', '')[0:10]))
            
            # 最终收益率
            final_return = rec.get('performance_metrics', {}).get('current_return', 0)
            return_item = QTableWidgetItem(f"{final_return:.2f}%")
            if final_return > 0:
                return_item.setForeground(QColor('green'))
            elif final_return < 0:
                return_item.setForeground(QColor('red'))
            self.history_table.setItem(i, 4, return_item)
            
            self.history_table.setItem(i, 5, QTableWidgetItem(rec.get('removal_reason', '')))
            self.history_table.setItem(i, 6, QTableWidgetItem(f"{rec['score']:.2f}"))
            self.history_table.setItem(i, 7, QTableWidgetItem(rec['source']))
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.recommendation_system.get_performance_stats()
        
        self.total_recs_label.setText(str(stats['total_active_recommendations']))
        self.avg_score_label.setText(f"{stats['avg_score']:.2f}")
        
        avg_return = stats['avg_return']
        self.avg_return_label.setText(f"{avg_return:.2f}%")
        if avg_return > 0:
            self.avg_return_label.setStyleSheet("color: green;")
        elif avg_return < 0:
            self.avg_return_label.setStyleSheet("color: red;")
        else:
            self.avg_return_label.setStyleSheet("")
        
        self.success_rate_label.setText(f"{stats['success_rate']:.2f}%")
    
    def update_tag_filter(self):
        """更新标签过滤器选项"""
        current_selection = self.tag_combo.currentText()
        
        # 获取所有标签
        all_tags = set()
        for rec in self.recommendation_system.get_all_recommendations().values():
            all_tags.update(rec.tags)
        
        # 使用blockSignals更安全地暂停信号
        self.tag_combo.blockSignals(True)
        
        # 清除并重新填充
        self.tag_combo.clear()
        self.tag_combo.addItem("全部")
        self.tag_combo.addItems(sorted(all_tags))
        
        # 恢复选择
        index = self.tag_combo.findText(current_selection)
        if index >= 0:
            self.tag_combo.setCurrentIndex(index)
            
        # 恢复信号连接
        self.tag_combo.blockSignals(False)
    
    def add_recommendation(self):
        """打开添加推荐对话框"""
        dialog = AddRecommendationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_recommendation_data()
            if data:
                # 创建推荐对象
                recommendation = create_recommendation(**data)
                
                # 添加到系统
                if self.recommendation_system.add_recommendation(recommendation):
                    QMessageBox.information(self, "成功", "成功添加推荐")
                    self.load_recommendations()
                else:
                    QMessageBox.warning(self, "警告", "已存在评分更高的相同推荐")
            else:
                QMessageBox.warning(self, "错误", "请填写所有必要信息")
    
    def view_recommendation(self, stock_code):
        """查看推荐详情"""
        recommendation = self.recommendation_system.get_recommendation(stock_code)
        
        if not recommendation:
            QMessageBox.warning(self, "错误", f"找不到推荐: {stock_code}")
            return
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"推荐详情: {recommendation.stock_name} ({recommendation.stock_code})")
        
        details = (
            f"股票名称: {recommendation.stock_name}\n"
            f"股票代码: {recommendation.stock_code}\n\n"
            f"推荐日期: {recommendation.recommendation_date.strftime('%Y-%m-%d')}\n"
            f"推荐来源: {recommendation.source}\n"
            f"推荐评分: {recommendation.score:.2f}\n\n"
            f"建议买入价: {recommendation.entry_price:.2f}\n"
            f"目标价格: {recommendation.target_price:.2f}\n"
            f"止损价格: {recommendation.stop_loss:.2f}\n"
            f"当前收益率: {recommendation.performance_metrics.get('current_return', 0):.2f}%\n"
            f"收益比: {recommendation.risk_reward_ratio:.2f}\n\n"
            f"标签: {', '.join(recommendation.tags)}\n\n"
            f"推荐理由:\n{recommendation.reason}"
        )
        
        msg.setText(details)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def remove_recommendation(self, stock_code):
        """删除推荐"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除推荐 {stock_code} 吗?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            reason, ok = QInputDialog.getText(
                self, "删除原因", 
                "请输入删除原因:",
                QLineEdit.Normal,
                "手动删除"
            )
            
            if ok:
                if self.recommendation_system.remove_recommendation(stock_code, reason):
                    QMessageBox.information(self, "成功", f"已删除推荐: {stock_code}")
                    self.load_recommendations()
                else:
                    QMessageBox.warning(self, "错误", f"删除失败: {stock_code}")
    
    def clean_recommendations(self):
        """清理过期推荐"""
        days, ok = QInputDialog.getInt(
            self, "清理过期", 
            "删除超过多少天的推荐:",
            30, 1, 365, 1
        )
        
        if ok:
            count = self.recommendation_system.clean_recommendations(days)
            QMessageBox.information(self, "成功", f"清理了 {count} 个过期推荐")
            self.load_recommendations()
    
    def generate_report(self):
        """生成推荐报告"""
        report_path = self.recommendation_system.generate_recommendation_report()
        
        reply = QMessageBox.question(
            self, "报告生成成功", 
            f"报告已保存到: {report_path}\n\n是否现在查看?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(report_path))

def show_recommendation_ui():
    """显示智能推荐系统UI"""
    # 如果已经存在一个应用实例，使用它
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建窗口
    window = QMainWindow()
    window.setWindowTitle("智能股票推荐系统")
    window.resize(900, 700)
    
    # 设置中心控件
    recommendation_widget = SmartRecommendationWidget()
    window.setCentralWidget(recommendation_widget)
    
    # 显示窗口
    window.show()
    
    # 如果是独立运行，则执行应用
    if not QApplication.instance():
        sys.exit(app.exec_())
    
    return window

if __name__ == "__main__":
    show_recommendation_ui() 