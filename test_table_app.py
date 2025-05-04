#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

class TestTableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试表格显示")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["股票代码", "股票名称", "价格", "评分", "来源"])
        
        layout.addWidget(self.table)
        
        # 填充测试数据
        self.fill_test_data()
    
    def fill_test_data(self):
        print("开始填充测试数据...")
        
        # 测试数据
        test_data = [
            ("000001", "平安银行", "20.50", "95.0", "测试来源"),
            ("600036", "招商银行", "35.80", "92.0", "测试来源"),
            ("601318", "中国平安", "48.25", "90.0", "测试来源"),
            ("000858", "五粮液", "155.30", "88.0", "测试来源"),
            ("600519", "贵州茅台", "1800.00", "85.0", "测试来源")
        ]
        
        # 清空表格
        self.table.setRowCount(0)
        print(f"表格行数已设置为0")
        
        # 添加数据
        for i, (code, name, price, score, source) in enumerate(test_data):
            print(f"添加行 {i}: {code} {name}")
            self.table.insertRow(i)
            
            self.table.setItem(i, 0, QTableWidgetItem(code))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(price))
            self.table.setItem(i, 3, QTableWidgetItem(score))
            self.table.setItem(i, 4, QTableWidgetItem(source))
        
        print(f"已添加 {len(test_data)} 行数据")

def main():
    app = QApplication(sys.argv)
    window = TestTableApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
