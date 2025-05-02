#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("PyQt5显示测试")
    window.setGeometry(100, 100, 400, 200)
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    label = QLabel("如果你能看到这个窗口，PyQt5显示功能正常工作！")
    layout.addWidget(label)
    
    window.setCentralWidget(central_widget)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 