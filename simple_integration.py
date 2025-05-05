#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级行业分析简易集成脚本
将高级行业分析模块与现有股票系统集成
"""

import os
import sys
import time
import logging
import traceback
import shutil

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='advanced_sector_integration.log',
    filemode='a'
)
logger = logging.getLogger('SimpleIntegration')

def backup_file(filename):
    """备份文件"""
    try:
        backup_name = f"{filename}.{int(time.time())}.bak"
        shutil.copy2(filename, backup_name)
        print(f"已备份文件: {backup_name}")
        return True
    except Exception as e:
        print(f"备份文件失败: {e}")
        return False

def modify_main_window_class(content):
    """修改MainWindow类"""
    # 修改构造函数，保存行业分析器实例
    updated_content = content.replace(
        "    def __init__(self, sector_integrator=None):\n"
        "        super().__init__()\n"
        "        self.setWindowTitle('股票分析系统')\n"
        "        self.setGeometry(100, 100, 1200, 800)\n"
        "        self.init_ui()",
        
        "    def __init__(self, sector_integrator=None):\n"
        "        super().__init__()\n"
        "        self.setWindowTitle('股票分析系统')\n"
        "        self.setGeometry(100, 100, 1200, 800)\n"
        "        # 保存行业分析器实例\n"
        "        self.sector_integrator = sector_integrator\n"
        "        self.init_ui()"
    )
    
    # 在init_ui方法中，修改选项卡部分，添加热门行业选项卡
    updated_content = updated_content.replace(
        "        # 添加智能推荐选项卡\n"
        "        self.tabs.addTab(QWidget(), '智能推荐')\n"
        "\n"
        "        # 删除热门行业选项卡\n"
        "\n"
        "        main_layout.addWidget(self.tabs)",
        
        "        # 添加智能推荐选项卡\n"
        "        self.tabs.addTab(QWidget(), '智能推荐')\n"
        "\n"
        "        # 添加热门行业选项卡\n"
        "        hot_sectors_tab = QWidget()\n"
        "        # 如果有行业分析器，则设置热门行业选项卡\n"
        "        if self.sector_integrator is not None:\n"
        "            self.setup_hot_sectors_tab(hot_sectors_tab)\n"
        "        self.tabs.addTab(hot_sectors_tab, '热门行业')\n"
        "\n"
        "        main_layout.addWidget(self.tabs)"
    )
    
    return updated_content

def add_sector_methods(content):
    """添加行业分析相关方法"""
    # 在statusBar().showMessage('就绪')之后添加热门行业相关方法
    sector_methods = """
    def setup_hot_sectors_tab(self, tab):
        '''设置热门行业选项卡'''
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
        from PyQt5.QtCore import Qt, QTimer
        from PyQt5.QtGui import QFont, QColor
        
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
        '''刷新热门行业数据'''
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtCore import QTimer
        
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
        '''加载热门行业数据'''
        from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
        from PyQt5.QtCore import Qt, QTimer
        from PyQt5.QtGui import QColor
        import traceback
        
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
            print(f"加载热门行业数据出错: {str(e)}")
            traceback.print_exc()
        
        finally:
            # 完成进度
            self.hot_sectors_progress.setValue(100)
            # 延迟隐藏进度条
            QTimer.singleShot(1000, lambda: self.hot_sectors_progress.setVisible(False))
    """
    
    updated_content = content.replace(
        "        # 设置状态栏\n"
        "        self.statusBar().showMessage('就绪')",
        
        "        # 设置状态栏\n"
        "        self.statusBar().showMessage('就绪')" + sector_methods
    )
    
    return updated_content

def modify_launch_code(content):
    """修改启动代码"""
    # 修改launch_gui函数，使用传入的sector_integrator
    launch_code = """def launch_gui(sector_integrator=None):
    '''启动GUI
    
    Args:
        sector_integrator: 行业分析器集成实例(可选)
    '''
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
    
    # 替换launch_gui函数及main块
    updated_content = content.replace(
        """def launch_gui(sector_integrator=None):
    '''启动GUI
    
    Args:
        sector_integrator: 行业分析器集成实例(可选)
    '''
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
        launch_gui(None)""", 
        
        launch_code
    )
    
    return updated_content

def add_import_statement(content):
    """添加导入语句"""
    # 在现有导入语句后面添加高级行业分析集成器的导入
    import_statement = """
# 导入高级行业分析集成器
try:
    from advanced_sector_integration import AdvancedSectorIntegrator
except ImportError:
    logger.warning("无法导入高级行业分析集成器")"""
    
    updated_content = content.replace(
        "from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon",
        "from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon" + import_statement
    )
    
    return updated_content

def main():
    """主程序"""
    print("\n====== 集成高级行业分析模块 ======\n")
    
    # 检查文件
    if not os.path.exists('stock_analysis_gui.py'):
        print("错误: 找不到stock_analysis_gui.py文件")
        return False
    
    # 读取原文件
    try:
        with open('stock_analysis_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False
    
    # 备份原文件
    if not backup_file('stock_analysis_gui.py'):
        return False
    
    # 检查是否已经集成
    if 'from advanced_sector_integration import AdvancedSectorIntegrator' in content:
        print("高级行业分析模块已集成到GUI")
        return True
    
    # 添加导入语句
    print("添加导入语句...")
    content = add_import_statement(content)
    
    # 修改MainWindow类
    print("修改MainWindow类...")
    content = modify_main_window_class(content)
    
    # 添加行业分析相关方法
    print("添加行业分析相关方法...")
    content = add_sector_methods(content)
    
    # 修改启动代码
    print("修改启动代码...")
    content = modify_launch_code(content)
    
    # 写入修改后的文件
    try:
        with open('stock_analysis_gui.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("成功修改 stock_analysis_gui.py")
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False
    
    print("\n集成完成！")
    print("现在可以通过以下命令启动带有高级行业分析功能的GUI:")
    print("python stock_analysis_gui.py")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"集成过程出错: {e}")
        logger.error(traceback.format_exc())
        print(f"错误: {e}") 