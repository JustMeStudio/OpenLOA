import sys
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QScrollArea, QListView, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QCursor


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
    def __init__(self, agents, on_agent_selected, username="窗外的、麻雀", balance=9999.99):
        super().__init__()
        self.on_agent_selected = on_agent_selected
        
        # Main layout with header
        main_layout = QVBoxLayout(self)
        
        # Header for user information
        header = QFrame()
        header.setFrameShape(QFrame.Box)
        header.setFrameShadow(QFrame.Raised)
        header.setLineWidth(2)
        header.setStyleSheet("""
            QFrame {
                border: 2px solid #0078D7;
                border-radius: 6px;
                background-color: #E6E6FA;
                padding: 10px;
            }
            QLabel {
                border: none;
                background: none;
            }
        """)
        header_layout = QHBoxLayout(header)
        
        # Username label
        username_label = QLabel(f"欢迎来到智能峡谷，亲爱的召唤师:   {username}")
        username_label.setFont(QFont("", 11, QFont.Bold))
        header_layout.addWidget(username_label, alignment=Qt.AlignLeft)
        
        # Right side layout for balance and buttons
        right_layout = QVBoxLayout()
        
        # Balance label
        balance_label = QLabel(f"余额: ￥{balance:.2f}")
        balance_label.setFont(QFont("", 11, QFont.Bold))
        right_layout.addWidget(balance_label, alignment=Qt.AlignRight)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        recharge_button = QPushButton("充值")
        share_button = QPushButton("分享领余额")
        
        # Button styling
        recharge_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #005BA1;
            }
        """)
        share_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #005BA1;
            }
        """)
        
        # Button click handlers
        recharge_button.clicked.connect(lambda: print("充值"))
        share_button.clicked.connect(lambda: print("分享领余额"))
        
        buttons_layout.addWidget(recharge_button)
        buttons_layout.addWidget(share_button)
        right_layout.addLayout(buttons_layout)
        
        header_layout.addLayout(right_layout)
        
        main_layout.addWidget(header)
        
        # Existing content layout
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(120)
        self.menu_list.setViewMode(QListView.ListMode)
        self.menu_list.setSpacing(5)
        content_layout.addWidget(self.menu_list)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        self.populate_tabs(agents)

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

                name = QLabel(ag['name'])
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