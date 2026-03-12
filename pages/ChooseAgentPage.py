import sys
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QScrollArea, QListView, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QCursor
from pages.i18n import get_current_language, get_text


class ClickableWidget(QWidget):
    clicked = Signal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ChooseAgentPage(QWidget):
    def __init__(self, agents, on_agent_selected, username="JustMeStudio"):
        super().__init__()
        self.on_agent_selected = on_agent_selected
        self.language = get_current_language()
        self.agents = agents
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # --- 顶部 Header 修改 ---
        header = QFrame()
        header.setObjectName("HeaderFrame") # 方便精确控制样式
        header.setStyleSheet("""
            QFrame#HeaderFrame {
                border: 2px solid #ff7f50;
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 10px;
            }
            QLabel {
                border: none;
                background: none;
                color: #333;
            }
        """)
        header_layout = QHBoxLayout(header)
        
        # 左侧欢迎语 - 保存引用以便后续更新
        welcome_layout = QVBoxLayout()
        self.username_label = QLabel(get_text('welcome_message', self.language))
        self.username_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        
        self.status_label = QLabel(get_text('system_status', self.language))
        self.status_label.setFont(QFont("Consolas", 9))
        self.status_label.setStyleSheet("color: #666;")
        
        welcome_layout.addWidget(self.username_label)
        welcome_layout.addWidget(self.status_label)
        header_layout.addLayout(welcome_layout, stretch=1)
        
        # --- 右侧：GitHub 标星按钮 ---
        self.star_button = QPushButton(get_text('star_button', self.language))
        self.star_button.setCursor(Qt.PointingHandCursor)
        self.star_button.setFixedWidth(220)
        self.star_button.setFixedHeight(45)
        self.star_button.setStyleSheet("""
            QPushButton {
                background-color: #24292e; /* GitHub 黑色主题 */
                color: white;
                border-radius: 22px;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff7f50; /* 悬浮切换为项目主色调 */
                border: 1px solid white;
            }
        """)
        # 链接到你的仓库
        self.star_button.clicked.connect(lambda: webbrowser.open("https://github.com/JustMeStudio/OpenLOA"))
        
        header_layout.addWidget(self.star_button, alignment=Qt.AlignRight)
        
        main_layout.addWidget(header)
        
        # --- 现有的内容布局保持不变 ---
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(130)
        self.menu_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.7);
            }
            QListWidget::item {
                padding: 15px 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #ff7f50;
                color: white;
                border-radius: 5px;
            }
        """)
        content_layout.addWidget(self.menu_list)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        self.populate_tabs(agents)
        
        # 信号连接
        self.menu_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.menu_list.setCurrentRow(0)

    def populate_tabs(self, agents):
        type_to_agents = {}
        for ag in agents:
            type_to_agents.setdefault(ag["type"], []).append(ag)

        # Predefined color rotation
        bg_colors = ["#FFFACD", "#E0FFFF", "#F0E68C", "#E6E6FA", "#FFE4E1"]

        for type_name, agent_list in type_to_agents.items():
            self.menu_list.addItem(QListWidgetItem(type_name))

            page = QWidget()
            page_layout = QVBoxLayout(page)
            scroll_area = QScrollArea(widgetResizable=True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            grid = QGridLayout()
            scroll_layout.addLayout(grid)
            scroll_layout.addStretch()
            scroll_area.setWidget(scroll_content)
            page_layout.addWidget(scroll_area)

            for idx, ag in enumerate(agent_list):
                color = bg_colors[idx % len(bg_colors)]
                frame = QFrame()
                frame.setFrameShape(QFrame.Box)
                frame.setFrameShadow(QFrame.Raised)
                frame.setLineWidth(2)
                frame.setStyleSheet(f"""
                    QFrame {{
                        border: 2px solid #0078D7;
                        border-radius: 6px;
                        background-color: {color};
                    }}
                """)

                w = ClickableWidget()
                w.clicked.connect(lambda a=ag: self.on_agent_selected(a))
                inner = QVBoxLayout(w)
                top_layout = QHBoxLayout()
                pix = QLabel()
                pix.setPixmap(QPixmap(ag['avatar']).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                top_layout.addWidget(pix, alignment=Qt.AlignLeft | Qt.AlignVCenter)

                name = QLabel(ag["nick_name"])
                name.setFont(QFont("", 11, QFont.Bold))
                desc = QLabel(ag['description'])
                desc.setWordWrap(True)
                name_layout = QVBoxLayout()
                name_layout.addWidget(name)
                name_layout.addWidget(desc)
                top_layout.addLayout(name_layout)
                inner.addLayout(top_layout)

                frame.setLayout(QVBoxLayout())
                frame.layout().addWidget(w)
                if len(agent_list) == 1:
                    grid.addWidget(frame, 0, 0, alignment=Qt.AlignLeft)
                else:
                    grid.addWidget(frame, idx // 2, idx % 2)

            self.stack.addWidget(page)

        self.menu_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.menu_list.setCurrentRow(0)

    def update_language(self, new_language):
        """更新页面语言"""
        self.language = new_language
        
        # 更新Header中的文本
        self.username_label.setText(get_text('welcome_message', new_language))
        self.status_label.setText(get_text('system_status', new_language))
        self.star_button.setText(get_text('star_button', new_language))