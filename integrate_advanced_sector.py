#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级行业分析集成脚本
将高级行业分析模块与现有系统集成
"""

import os
import sys
import logging
import traceback
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QSplitter, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='advanced_sector_integration.log',
    filemode='a'
)
logger = logging.getLogger('IntegrateAdvancedSector')

def integrate_with_stock_gui():
    """与stock_analysis_gui.py集成"""
    try:
        logger.info("开始与GUI集成")
        
        # 检查stock_analysis_gui.py是否存在
        if not os.path.exists('stock_analysis_gui.py'):
            logger.error("找不到stock_analysis_gui.py文件")
            print("错误: 找不到stock_analysis_gui.py文件")
            return False
        
        # 读取原文件内容
        with open('stock_analysis_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已集成
        if 'from advanced_sector_integration import AdvancedSectorIntegrator' in content:
            logger.info("高级行业分析模块已集成到GUI")
            print("高级行业分析模块已集成到GUI")
            return True
        
        # 创建修改后的内容
        
        # 导入语句
        import_str = """import os
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

# 导入高级行业分析集成器
try:
    from advanced_sector_integration import AdvancedSectorIntegrator
except ImportError:
    logger.warning("无法导入高级行业分析集成器")"""
        
        # 替换导入部分
        content = content.replace("""import os
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
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon""", import_str)
        
        # 修改MainWindow类，添加行业分析器和热门行业选项卡
        main_window_init = """    def __init__(self, sector_integrator=None):
        super().__init__()
        self.setWindowTitle('股票分析系统')
        self.setGeometry(100, 100, 1200, 800)
        
        # 保存行业分析器实例
        self.sector_integrator = sector_integrator
        
        self.init_ui()"""
        
        content = content.replace("""    def __init__(self, sector_integrator=None):
        super().__init__()
        self.setWindowTitle('股票分析系统')
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()""", main_window_init)
        
        # 添加热门行业选项卡
        tabs_section = """        # 添加智能推荐选项卡
        self.tabs.addTab(QWidget(), '智能推荐')
        
        # 添加热门行业选项卡
        hot_sectors_tab = QWidget()
        self.setup_hot_sectors_tab(hot_sectors_tab)
        self.tabs.addTab(hot_sectors_tab, '热门行业')
        
        main_layout.addWidget(self.tabs)"""
        
        content = content.replace("""        # 添加智能推荐选项卡
        self.tabs.addTab(QWidget(), '智能推荐')
        
        # 删除热门行业选项卡
        
        main_layout.addWidget(self.tabs)""", tabs_section)
        
        # 添加热门行业选项卡设置方法
        status_bar_section = """        # 设置状态栏
        self.statusBar().showMessage('就绪')
        
    def setup_hot_sectors_tab(self, tab):
        '''设置热门行业选项卡'''
        layout = QVBoxLayout(tab)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel('热门行业分析')
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        control_layout.addWidget(title_label)
        
        # 添加刷新按钮
        refresh_button = QPushButton('刷新数据')
        refresh_button.clicked.connect(self.refresh_hot_sectors)
        control_layout.addWidget(refresh_button)
        
        # 添加到布局
        control_layout.addStretch(1)
        layout.addLayout(control_layout)
        
        # 创建热门行业表格
        self.hot_sectors_table = QTableWidget()
        self.hot_sectors_table.setColumnCount(5)
        self.hot_sectors_table.setHorizontalHeaderLabels(['行业名称', '热度得分', '变动幅度', '成交量', '分析结论'])
        
        # 设置表格属性
        self.hot_sectors_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.hot_sectors_table.verticalHeader().setVisible(False)
        self.hot_sectors_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.hot_sectors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.hot_sectors_table.setStyleSheet("QTableWidget{gridline-color: #d3d3d3;}")
        
        layout.addWidget(self.hot_sectors_table)
        
        # 添加状态栏
        status_layout = QHBoxLayout()
        self.hot_sectors_status = QLabel('请点击刷新按钮获取最新热门行业数据')
        status_layout.addWidget(self.hot_sectors_status)
        
        # 添加进度条
        self.hot_sectors_progress = QProgressBar()
        self.hot_sectors_progress.setRange(0, 100)
        self.hot_sectors_progress.setValue(0)
        self.hot_sectors_progress.setVisible(False)
        status_layout.addWidget(self.hot_sectors_progress)
        
        layout.addLayout(status_layout)
        
        # 初始加载数据
        QTimer.singleShot(1000, self.refresh_hot_sectors)
    
    def refresh_hot_sectors(self):
        """刷新热门行业数据"""
        # 检查是否有集成器
        if self.sector_integrator is None:
            QMessageBox.warning(self, '警告', '未配置行业分析器，请检查配置')
            return
        
        # 更新界面状态
        self.hot_sectors_status.setText("正在加载热门行业数据...")
        self.hot_sectors_progress.setVisible(True)
        self.hot_sectors_progress.setValue(10)
        
        # 防止UI卡顿，使用计时器延迟执行
        QTimer.singleShot(100, self._load_hot_sectors_data)
    
    def _load_hot_sectors_data(self):
        """加载热门行业数据"""
        try:
            # 更新进度
            self.hot_sectors_progress.setValue(30)
            
            # 获取热门行业数据
            result = self.sector_integrator.get_hot_sectors()
            
            # 更新进度
            self.hot_sectors_progress.setValue(70)
            
            if result['status'] == 'success':
                # 获取热门行业列表
                hot_sectors = result['data'].get('hot_sectors', [])
                
                # 更新表格
                self.hot_sectors_table.setRowCount(len(hot_sectors))
                
                for i, sector in enumerate(hot_sectors):
                    # 行业名称
                    name_item = QTableWidgetItem(sector.get('name', ''))
                    self.hot_sectors_table.setItem(i, 0, name_item)
                    
                    # 热度得分
                    score = sector.get('hot_score', 0)
                    score_item = QTableWidgetItem(f"{score:.2f}")
                    score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.hot_sectors_table.setItem(i, 1, score_item)
                    
                    # 变动幅度
                    change = sector.get('change_pct', 0)
                    change_item = QTableWidgetItem(f"{change:.2f}%")
                    change_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if change > 0:
                        change_item.setForeground(QColor('red'))
                    elif change < 0:
                        change_item.setForeground(QColor('green'))
                    self.hot_sectors_table.setItem(i, 2, change_item)
                    
                    # 成交量
                    volume = sector.get('volume', 0)
                    volume_item = QTableWidgetItem(f"{volume:.2f}亿")
                    volume_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.hot_sectors_table.setItem(i, 3, volume_item)
                    
                    # 分析结论
                    reason = sector.get('analysis_reason', '')
                    if not sector.get('is_real_data', True):
                        reason += " (使用模拟数据，仅供参考)"
                    reason_item = QTableWidgetItem(reason)
                    self.hot_sectors_table.setItem(i, 4, reason_item)
                
                # 更新状态
                last_update = result['data'].get('analysis_time', '未知')
                north_flow = result['data'].get('north_flow', 0)
                self.hot_sectors_status.setText(
                    f"最后更新: {last_update} | 北向资金: {north_flow:.2f}亿元 | "
                    f"数据来源: {result['data'].get('source', '高级行业分析器')}"
                )
            else:
                # 显示错误
                self.hot_sectors_status.setText(f"加载失败: {result.get('message', '未知错误')}")
                QMessageBox.warning(self, '警告', f"获取热门行业数据失败: {result.get('message', '未知错误')}")
        
        except Exception as e:
            self.hot_sectors_status.setText(f"加载失败: {str(e)}")
            logger.error(f"加载热门行业数据出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # 完成进度
            self.hot_sectors_progress.setValue(100)
            # 延迟隐藏进度条
            QTimer.singleShot(1000, lambda: self.hot_sectors_progress.setVisible(False))"""
        
        content = content.replace("""        # 设置状态栏
        self.statusBar().showMessage('就绪')""", status_bar_section)
        
        # 修改启动代码
        launch_section = """def launch_gui(sector_integrator=None):
    """启动GUI
    
    Args:
        sector_integrator: 行业分析器集成实例(可选)
    """
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont()
    font.setFamily('Arial')
    font.setPointSize(10)
    app.setFont(font)
    
    # 创建并显示主窗口
    main_window = MainWindow(sector_integrator=sector_integrator)
    main_window.show()
    
    # 启动应用程序事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    # 如果直接运行此文件，尝试创建高级行业分析器集成器
    try:
        from advanced_sector_integration import AdvancedSectorIntegrator
        integrator = AdvancedSectorIntegrator()
        launch_gui(integrator)
    except ImportError:
        # 尝试导入原始集成器
        try:
            from integrate_sector_analyzer import SectorAnalyzerIntegrator
            integrator = SectorAnalyzerIntegrator()
            launch_gui(integrator)
        except ImportError:
            # 如果无法导入，则启动没有集成器的GUI
            logger.warning("无法导入任何行业分析器集成器")
            launch_gui(None)
    except Exception as e:
        logger.error(f"创建集成器失败: {e}")
        launch_gui(None)"""
        
        content = content.replace("""def launch_gui(sector_integrator=None):
    """启动GUI
    
    Args:
        sector_integrator: 行业分析器集成实例(可选)
    """
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont()
    font.setFamily('Arial')
    font.setPointSize(10)
    app.setFont(font)
    
    # 创建并显示主窗口
    main_window = MainWindow(sector_integrator=None)
    main_window.show()
    
    # 启动应用程序事件循环
    sys.exit(app.exec_())

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
        launch_gui(None)""", launch_section)
        
        # 备份原文件
        backup_file = f"stock_analysis_gui.py.{int(time.time())}.bak"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.read_original = content
        logger.info(f"已备份原文件到 {backup_file}")
        
        # 写入修改后的内容
        with open('stock_analysis_gui.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功更新stock_analysis_gui.py，添加了高级行业分析模块集成")
        print("成功集成高级行业分析模块到GUI")
        return True
        
    except Exception as e:
        logger.error(f"集成到GUI时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"集成失败: {str(e)}")
        return False

def create_test_script():
    """创建测试脚本"""
    try:
        test_file = 'test_advanced_sector.py'
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

\"\"\"
高级行业分析测试脚本
\"\"\"

import sys
import logging
from PyQt5.QtWidgets import QApplication

# 设置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestAdvancedSector')

def test_standalone():
    \"\"\"测试独立行业分析器\"\"\"
    from advanced_sector_analyzer import AdvancedSectorAnalyzer
    
    analyzer = AdvancedSectorAnalyzer()
    result = analyzer.analyze_hot_sectors()
    
    if result['status'] == 'success':
        hot_sectors = result['data']['hot_sectors']
        print(f"\\n热门行业排名:")
        for i, sector in enumerate(hot_sectors, 1):
            print(f"{i}. {sector['name']} (热度: {sector['hot_score']:.2f}) - {sector.get('analysis_reason', '')}")
    else:
        print(f"\\n获取热门行业失败: {result.get('message', '未知错误')}")

def test_integration():
    \"\"\"测试与GUI的集成\"\"\"
    from advanced_sector_integration import AdvancedSectorIntegrator
    from stock_analysis_gui import launch_gui
    
    integrator = AdvancedSectorIntegrator()
    
    # 启动GUI
    app = QApplication(sys.argv)
    launch_gui(integrator)
    sys.exit(app.exec_())

if __name__ == "__main__":
    print("======= 高级行业分析测试 =======")
    print("1. 测试独立行业分析器")
    print("2. 测试与GUI集成")
    
    choice = input("请选择测试类型 [1/2]: ")
    
    if choice == '2':
        test_integration()
    else:
        test_standalone()
""")
        
        logger.info(f"成功创建测试脚本 {test_file}")
        print(f"成功创建测试脚本 {test_file}")
        return True
    
    except Exception as e:
        logger.error(f"创建测试脚本失败: {str(e)}")
        print(f"创建测试脚本失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n====== 开始集成高级行业分析模块 ======\n")
    
    # 与GUI集成
    integrate_with_stock_gui()
    
    # 创建测试脚本
    create_test_script()
    
    print("\n====== 集成完成 ======")
    print("\n你可以通过以下方式测试集成效果:")
    print("1. 运行 'python test_advanced_sector.py'")
    print("2. 直接运行 'python stock_analysis_gui.py'")
    print("\n热门行业分析模块已添加到GUI的'热门行业'选项卡中")

if __name__ == "__main__":
    import time
    main() 