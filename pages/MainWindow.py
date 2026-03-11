import sys,json
from importlib import import_module
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6 import QtCore
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap

# 导入其它页面
from pages.ChooseAgentPage import ChooseAgentPage
from pages.WelcomePage import WelcomePage

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能体联盟")

        # 设置固定窗口大小，例如 800x600
        self.resize(1200, 600)

        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stack)
        #读取智能体列表
        with open ("./agents.json", "r", encoding="utf-8") as f:
            self.agents = json.load(f)

        self.welcome = WelcomePage(self.show_choose)
        self.choose = ChooseAgentPage(self.agents, self.on_agent_chosen)
        self.interaction = QWidget()  # 占位页

        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.choose)
        self.stack.addWidget(self.interaction)

    def show_choose(self):
        self.stack.setCurrentWidget(self.choose)

    def on_agent_chosen(self, agent): 
        # 动态加载对应智能体的页面
        page_module = import_module(f"pages.agents.{agent['page']}")
        PageClass = getattr(page_module, agent["page"])
        page = PageClass()
        # 替换第三页
        self.stack.removeWidget(self.interaction)
        self.interaction = page
        self.stack.addWidget(self.interaction)
        # 连接 switch_to_agent_page 信号（如果页面支持）
        if hasattr(page, "switch_to_agent_page"):
            page.switch_to_agent_page.connect(self.switch_to_choose)
        self.stack.setCurrentWidget(self.interaction)

    def switch_to_choose(self):
        # 移除当前交互页面并切换到 ChooseAgentPage
        self.stack.removeWidget(self.interaction)
        self.interaction.deleteLater()  # 释放资源
        self.interaction = QWidget()  # 创建新的占位页
        self.stack.addWidget(self.interaction)
        self.stack.setCurrentWidget(self.choose)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
