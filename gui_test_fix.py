
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# 创建应用程序
app = QApplication(sys.argv)

# 创建主窗口
window = QMainWindow()
window.setWindowTitle("GUI修复测试")
window.setGeometry(100, 100, 400, 200)

# 创建中央部件和布局
central_widget = QWidget()
layout = QVBoxLayout(central_widget)

# 添加标签
label = QLabel("如果你看到这个窗口，说明GUI显示正常！")
label.setAlignment(Qt.AlignCenter)
layout.addWidget(label)

# 添加按钮
launch_btn = QPushButton("启动股票分析系统")
layout.addWidget(launch_btn)

# 定义启动函数
def launch_main_app():
    window.close()
    import subprocess
    import sys
    subprocess.Popen([sys.executable, 'app.py'])

# 连接按钮点击事件
launch_btn.clicked.connect(launch_main_app)

window.setCentralWidget(central_widget)
window.show()

sys.exit(app.exec_())
