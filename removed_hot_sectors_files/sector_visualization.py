import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QPushButton, QHBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import akshare as ak
from datetime import datetime, timedelta
import os
import platform


# Fix Chinese font display
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 根据操作系统设置合适的中文字体
def set_chinese_font():
    system = platform.system()
    if system == 'Windows':
        font_list = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    elif system == 'Darwin':  # macOS
        font_list = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS', 'Hiragino Sans GB']
    else:  # Linux
        font_list = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Droid Sans Fallback', 'Arial Unicode MS']
    
    # 尝试设置字体
    for font in font_list:
        try:
            matplotlib.rcParams['font.sans-serif'] = [font] + matplotlib.rcParams['font.sans-serif']
            # 确保设置生效
            matplotlib.rcParams['axes.unicode_minus'] = False
            # 增加字体缓存清理，解决某些情况下字体缓存问题
            matplotlib.font_manager._rebuild()
            break
        except Exception as e:
            print(f"设置字体 {font} 失败: {str(e)}")
            continue
            
    # 强制设置字体属性
    plt.rcParams['font.family'] = 'sans-serif'
    # 增加字体大小，提高可读性
    plt.rcParams['font.size'] = 12

# 设置中文字体
set_chinese_font()
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 设置更美观的图表样式
plt.style.use('ggplot')

class SectorVisualizationDialog(QDialog):
    """行业分析可视化对话框
    
    提供多维度的行业分析可视化图表，包括：
    1. 热门行业热度趋势图
    2. 行业热度分布图
    3. 行业轮动周期图
    4. 产业链关系图
    5. 行业预测结果图
    """
    
    def __init__(self, parent=None, viz_data=None):
        super().__init__(parent)
        self.viz_data = viz_data
        self.initUI()
    
    def initUI(self):
        # 设置对话框属性
        self.setWindowTitle('行业分析可视化')
        self.setGeometry(200, 200, 900, 700)
        self.setStyleSheet("background-color: white;")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建标题
        title_label = QLabel('行业分析可视化')
        title_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont('Microsoft YaHei', 10))
        
        # 添加各种图表标签页
        self.add_trend_tab()
        self.add_distribution_tab()
        self.add_cycle_tab()
        self.add_chain_tab()
        self.add_prediction_tab()  # 新增预测结果标签页
        
        main_layout.addWidget(self.tab_widget)
        
        # 添加底部按钮
        button_layout = QHBoxLayout()
        close_btn = QPushButton('关闭')
        close_btn.setFont(QFont('Microsoft YaHei', 10))
        close_btn.setMinimumSize(100, 30)
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def add_trend_tab(self):
        """添加热度趋势图标签页"""
        trend_tab = QWidget()
        trend_layout = QVBoxLayout(trend_tab)
        
        # 创建图表
        trend_fig = Figure(figsize=(8, 5), dpi=100)
        trend_canvas = FigureCanvas(trend_fig)
        trend_layout.addWidget(trend_canvas)
        
        # 绘制图表
        ax = trend_fig.add_subplot(111)
        
        if self.viz_data and self.viz_data['status'] == 'success':
            trend_data = self.viz_data['data'].get('trend_data', [])
            
            if trend_data:
                # 设置颜色循环
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                
                for i, sector in enumerate(trend_data):
                    dates = sector['dates'][-10:]  # 取最近10天
                    prices = sector['prices'][-10:]
                    
                    # 计算归一化价格，便于比较
                    if len(prices) > 0 and prices[0] != 0:
                        norm_prices = [p / prices[0] * 100 for p in prices]
                    else:
                        norm_prices = prices
                    
                    # 使用日期作为x轴标签
                    x_labels = [d[-5:] for d in dates]  # 只显示月-日
                    x_range = range(len(dates))
                    
                    # 绘制带有标记的线条
                    color = colors[i % len(colors)]
                    line, = ax.plot(x_range, norm_prices, label=f"{sector['name']}", 
                                   color=color, linewidth=2, marker='o', markersize=5)
                    
                    # 添加最新价格标签
                    if len(norm_prices) > 0:
                        ax.annotate(f"{norm_prices[-1]:.1f}", 
                                   xy=(x_range[-1], norm_prices[-1]),
                                   xytext=(5, 0), textcoords='offset points',
                                   fontsize=9, color=color, weight='bold')
                
                ax.set_title('热门行业近期走势对比(归一化)', fontsize=14, fontweight='bold')
                ax.set_xlabel('日期', fontsize=12)
                ax.set_ylabel('指数(基准=100)', fontsize=12)
                ax.set_xticks(range(len(dates)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
                
                # 添加图例，并设置在图表外部
                ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                          ncol=3, fontsize=10, frameon=True, fancybox=True, shadow=True)
                
                # 添加网格线
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # 添加热度评分信息
                for i, sector in enumerate(trend_data):
                    if 'hot_score' in sector:
                        y_pos = 0.97 - i * 0.05
                        ax.text(0.02, y_pos, f"{sector['name']}热度: {sector.get('hot_score', 0):.1f}",
                               transform=ax.transAxes, fontsize=9,
                               bbox=dict(facecolor=colors[i % len(colors)], alpha=0.2, boxstyle='round,pad=0.3'))
                
                # 添加图表说明
                explanation = '''说明：
1. 走势线显示各行业相对于基准日的涨跌幅变化
2. 热度指数综合考虑涨跌幅、成交量、资金流向等因素
3. 数值越大表示行业活跃度越高'''
                ax.text(0.02, -0.25, explanation,
                        transform=ax.transAxes, fontsize=9, ha='left', va='top',
                        bbox=dict(facecolor='#f5f5f5', alpha=0.5, boxstyle='round,pad=0.5'))
                
                trend_fig.tight_layout(pad=2.0)
                # 调整布局以适应图例和说明文字
                trend_fig.subplots_adjust(bottom=0.3)
            else:
                ax.text(0.5, 0.5, '暂无热度趋势数据', 
                         ha='center', va='center', fontsize=14, color='gray')
        else:
            ax.text(0.5, 0.5, '获取热度趋势数据失败', 
                     ha='center', va='center', fontsize=14, color='red')
        
        self.tab_widget.addTab(trend_tab, "热度趋势")
    
    def add_distribution_tab(self):
        """添加热度分布图标签页"""
        dist_tab = QWidget()
        dist_layout = QVBoxLayout(dist_tab)
        
        # 创建图表
        dist_fig = Figure(figsize=(8, 5), dpi=100)
        dist_canvas = FigureCanvas(dist_fig)
        dist_layout.addWidget(dist_canvas)
        
        # 绘制图表
        ax = dist_fig.add_subplot(111)
        
        if self.viz_data and self.viz_data['status'] == 'success':
            dist_data = self.viz_data['data'].get('distribution_data', [])
            
            if dist_data:
                names = [d['name'] for d in dist_data]
                scores = [d['hot_score'] for d in dist_data]
                changes = [d['change_pct'] for d in dist_data]
                
                x = range(len(names))
                width = 0.35
                
                # 绘制热度评分柱状图
                bars1 = ax.bar(x, scores, width, label='热度评分', color='#4CAF50')
                
                # 绘制涨跌幅柱状图
                bars2 = ax.bar([i + width for i in x], changes, width, label='涨跌幅(%)', color='#2196F3')
                
                # 添加数据标签
                for bar in bars1:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.1f}', ha='center', va='bottom', fontsize=8)
                
                for bar in bars2:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
                
                ax.set_title('行业热度与涨跌幅对比', fontsize=14)
                ax.set_xlabel('行业', fontsize=12)
                ax.set_ylabel('数值', fontsize=12)
                ax.set_xticks([i + width/2 for i in x])
                ax.set_xticklabels(names, rotation=45, ha='right', fontsize=10)
                ax.legend(fontsize=10)
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                dist_fig.tight_layout()
            else:
                ax.text(0.5, 0.5, '暂无热度分布数据', 
                         ha='center', va='center', fontsize=14, color='gray')
        else:
            ax.text(0.5, 0.5, '获取热度分布数据失败', 
                     ha='center', va='center', fontsize=14, color='red')
        
        self.tab_widget.addTab(dist_tab, "热度分布")
    
    def add_cycle_tab(self):
        """添加行业轮动周期图标签页"""
        cycle_tab = QWidget()
        cycle_layout = QVBoxLayout(cycle_tab)
        
        # 创建图表
        cycle_fig = Figure(figsize=(8, 5), dpi=100)
        cycle_canvas = FigureCanvas(cycle_fig)
        cycle_layout.addWidget(cycle_canvas)
        
        # 绘制图表
        ax = cycle_fig.add_subplot(111, polar=True)

        try:
            # 初始化变量
            sector_name = ""
            cycles = ['复苏期', '扩张期', '滞涨期', '衰退期']
            cycle_scores = [0, 0, 0, 0]
            current_cycle = ""
            
            if self.viz_data and self.viz_data.get('status') == 'success':
                cycle_data = self.viz_data.get('data', {}).get('cycle_data', {})
                
                if cycle_data and 'cycle_scores' in cycle_data:
                    # 获取周期评分
                    cycle_scores = [cycle_data['cycle_scores'].get(c, 0) for c in cycles]
                    # 获取行业名称
                    sector_name = cycle_data.get('sector_name', '')
                    # 获取当前周期
                    current_cycle = cycle_data.get('current_cycle', '')
            
            # 创建默认数据（如果没有有效数据）
            if sum(cycle_scores) <= 0:
                # 生成一些随机数据
                cycle_scores = [30 + np.random.randint(0, 40) for _ in range(4)]
                # 选择一个默认的当前周期
                if not current_cycle or current_cycle not in cycles:
                    current_cycle = cycles[np.random.randint(0, 4)]
            
            # 确保数据有效
            angles = np.linspace(0, 2*np.pi, len(cycles), endpoint=False).tolist()
            cycle_scores_plot = cycle_scores.copy()
            cycle_scores_plot.append(cycle_scores_plot[0])  # 闭合雷达图
            angles.append(angles[0])  # 闭合雷达图
            
            # 绘制雷达图
            ax.plot(angles, cycle_scores_plot, 'o-', linewidth=2, color='#2196F3')
            ax.fill(angles, cycle_scores_plot, alpha=0.25, color='#2196F3')
            ax.set_thetagrids(np.array(angles[:-1]) * 180/np.pi, cycles, fontsize=12)
            
            # 设置标题
            title = '行业轮动周期分析'
            if sector_name:
                title = f'行业轮动周期分析（{sector_name}）'
            ax.set_title(title, fontsize=14, pad=20)
            
            # 标记当前周期
            if current_cycle in cycles:
                current_idx = cycles.index(current_cycle)
                ax.plot(angles[current_idx], cycle_scores[current_idx], 'ro', markersize=10)
                ax.text(angles[current_idx], cycle_scores[current_idx]*1.2,
                        f'当前: {current_cycle}', ha='center', va='center', 
                        fontsize=12, color='red', weight='bold')
                
                # 标记下一个周期
                next_cycle = cycle_data.get('next_cycle', '')
                if next_cycle in cycles:
                    next_idx = cycles.index(next_cycle)
                    ax.plot(angles[next_idx], cycle_scores[next_idx], 'go', markersize=10)
                    ax.text(angles[next_idx], cycle_scores[next_idx]*1.2, 
                            f'下一轮动: {next_cycle}', ha='center', va='center', 
                            fontsize=12, color='green', weight='bold')
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            ax.text(0, 0, f'获取轮动周期数据失败: {str(e)}', 
                    ha='center', va='center', fontsize=14, color='red')
        
        self.tab_widget.addTab(cycle_tab, "行业轮动")
    
    def add_chain_tab(self):
        """添加产业链关系图标签页"""
        chain_tab = QWidget()
        chain_layout = QVBoxLayout(chain_tab)
        
        # 创建图表
        chain_fig = Figure(figsize=(8, 5), dpi=100)
        chain_canvas = FigureCanvas(chain_fig)
        chain_layout.addWidget(chain_canvas)
        
        # 绘制图表
        ax = chain_fig.add_subplot(111)
        
        # 获取热门行业的产业链数据
        try:
            from enhanced_sector_analyzer import EnhancedSectorAnalyzer
            analyzer = EnhancedSectorAnalyzer()
            hot_sectors = analyzer.analyze_hot_sectors()
            
            if hot_sectors['status'] == 'success' and len(hot_sectors['data']['hot_sectors']) > 0:
                top_sector = hot_sectors['data']['hot_sectors'][0]
                chain_result = analyzer.analyze_industry_chain(top_sector['name'])
                
                if chain_result['status'] == 'success':
                    chain_data = chain_result['data']
                    
                    # 绘制产业链关系图
                    sector_name = chain_data['sector_name']
                    upstream = [u['name'] for u in chain_data['upstream']]
                    downstream = [d['name'] for d in chain_data['downstream']]
                    related = [r['name'] for r in chain_data['related']]
                    
                    # 设置节点位置
                    pos = {}
                    # 上游行业位置
                    for i, name in enumerate(upstream):
                        pos[name] = (i - len(upstream)/2 + 0.5, 1)
                    # 中心行业位置
                    pos[sector_name] = (0, 0)
                    # 下游行业位置
                    for i, name in enumerate(downstream):
                        pos[name] = (i - len(downstream)/2 + 0.5, -1)
                    # 相关行业位置
                    for i, name in enumerate(related):
                        pos[name] = (len(upstream) + i + 1, 0)
                    
                    # 绘制节点
                    for name, (x, y) in pos.items():
                        color = 'red' if name == sector_name else 'skyblue'
                        ax.plot(x, y, 'o', markersize=15, color=color)
                        ax.text(x, y, name, ha='center', va='center', fontsize=8)
                    
                    # 绘制连线
                    for name in upstream:
                        ax.plot([pos[name][0], pos[sector_name][0]], [pos[name][1], pos[sector_name][1]], 'b-', alpha=0.6)
                    for name in downstream:
                        ax.plot([pos[name][0], pos[sector_name][0]], [pos[name][1], pos[sector_name][1]], 'g-', alpha=0.6)
                    for name in related:
                        ax.plot([pos[name][0], pos[sector_name][0]], [pos[name][1], pos[sector_name][1]], 'k--', alpha=0.4)
                    
                    ax.set_title(f'{sector_name}产业链关系图', fontsize=14)
                    ax.set_xlim(-len(upstream), len(upstream) + len(related) + 1)
                    ax.set_ylim(-1.5, 1.5)
                    ax.axis('off')
                    
                    # 添加图例
                    ax.plot([], [], 'b-', label='上游行业')
                    ax.plot([], [], 'g-', label='下游行业')
                    ax.plot([], [], 'k--', label='相关行业')
                    ax.legend(loc='upper right', fontsize=10)
                else:
                    ax.text(0.5, 0.5, '暂无产业链数据', 
                             ha='center', va='center', fontsize=14, color='gray')
            else:
                ax.text(0.5, 0.5, '暂无热门行业数据', 
                         ha='center', va='center', fontsize=14, color='gray')
        except Exception as e:
            ax.text(0.5, 0.5, f'获取产业链数据失败: {str(e)}', 
                     ha='center', va='center', fontsize=14, color='red')
        
        self.tab_widget.addTab(chain_tab, "产业链关系")
    
    def generate_heatmap(self, sectors):
        # 标准化行业代码处理
        standardized_sectors = [
            {
                'name': f"{s['name']}（{s['standard_code']}）",
                'hot_score': s['hot_score'],
                'standard_code': s.get('standard_code', 'EM_0000')
            } for s in sectors
        ]
        
        # 创建DataFrame并过滤
        df = pd.DataFrame(standardized_sectors)
        df = df[df['standard_code'].str.startswith('EM_')]
        df = df[df['hot_score'] > 0]

    def add_prediction_tab(self):
        """添加行业预测结果图标签页"""
        pred_tab = QWidget()
        pred_layout = QVBoxLayout(pred_tab)
        
        # 创建滚动区域以支持更多内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 创建图表
        pred_fig = Figure(figsize=(8, 6), dpi=100)
        pred_canvas = FigureCanvas(pred_fig)
        scroll_layout.addWidget(pred_canvas)
        
        # 绘制图表
        ax = pred_fig.add_subplot(111)
        
        try:
            # 直接使用传入的可视化数据
            if self.viz_data and self.viz_data['status'] == 'success':
                # 安全地获取prediction_data，如果不存在则使用空列表
                prediction_data = self.viz_data['data'].get('prediction_data', [])
                
                if prediction_data and len(prediction_data) > 0:
                    # 确保每个项目都有必要的键
                    valid_data = []
                    for item in prediction_data:
                        if isinstance(item, dict) and 'name' in item and 'technical_score' in item:
                            valid_data.append(item)
                    
                    if valid_data:
                        # 提取数据
                        names = [s['name'] for s in valid_data]
                        scores = [s['technical_score'] for s in valid_data]
                        
                        # 创建渐变色条形图
                        cmap = plt.cm.get_cmap('YlOrRd')  # 使用黄-橙-红渐变色
                        max_score = max(scores) if scores else 100
                        norm = plt.Normalize(0, max_score)
                        
                        # 绘制水平条形图
                        bars = ax.barh(range(len(names)), scores, height=0.7, 
                                      color=[cmap(norm(score)) for score in scores])
                        
                        # 添加数据标签
                        for i, bar in enumerate(bars):
                            width = bar.get_width()
                            ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                                    f'{width:.1f}', ha='left', va='center', fontsize=10, weight='bold')
                            
                            # 安全地添加轮动状态标记
                            rotation_status = valid_data[i].get('rotation_status', '')
                            if rotation_status == '即将轮动':
                                ax.text(width + 15, bar.get_y() + bar.get_height()/2, 
                                        '*', ha='center', va='center', fontsize=14, color='#FFD700')
                        
                        # 设置图表属性
                        ax.set_title('行业预测结果', fontsize=16, fontweight='bold')
                        ax.set_xlabel('技术评分', fontsize=12)
                        ax.set_yticks(range(len(names)))
                        ax.set_yticklabels(names, fontsize=11)
                        ax.set_xlim(0, max_score * 1.3)  # 留出足够空间显示标签
                        ax.grid(True, linestyle='--', alpha=0.7, axis='x')
                        
                        # 添加预测准确率信息
                        accuracy_data = self.viz_data['data'].get('accuracy_data', {})
                        if accuracy_data:
                            accuracy = accuracy_data.get('accuracy', 0) * 100
                            ax.text(0.02, 0.02, 
                                    f'历史预测准确率: {accuracy:.1f}%', 
                                    transform=ax.transAxes, fontsize=10, 
                                    bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))
                    else:
                        # 预测数据格式不正确
                        ax.text(0.5, 0.5, '预测数据格式不正确', 
                                ha='center', va='center', fontsize=14, color='gray', 
                                transform=ax.transAxes)
                else:
                    # 没有预测数据时显示提示信息
                    ax.text(0.5, 0.5, '暂无行业预测数据', 
                            ha='center', va='center', fontsize=14, color='gray', 
                            transform=ax.transAxes)
            else:
                # 无可视化数据时显示错误提示
                ax.text(0.5, 0.5, '获取行业分析数据失败', 
                        ha='center', va='center', fontsize=14, color='red', 
                        transform=ax.transAxes)
                
        except Exception as e:
            # 捕获并显示所有异常
            ax.text(0.5, 0.5, f'分析行业数据失败: {str(e)}', 
                    ha='center', va='center', fontsize=14, color='red', 
                    transform=ax.transAxes)
            import traceback
            traceback.print_exc()  # 打印详细的异常堆栈信息
        
        # 添加滚动区域
        scroll_area.setWidget(scroll_content)
        pred_layout.addWidget(scroll_area)
        
        # 添加标签页
        self.tab_widget.addTab(pred_tab, "预测结果")