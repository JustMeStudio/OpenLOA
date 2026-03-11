from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QMovie, QFont, QColor
from PySide6.QtCore import Qt

class WelcomePage(QWidget):
    def __init__(self, switch_to_choose):
        super().__init__()

        # 背景动效
        self.movie = QMovie("./assets/home/1.gif")
        self.movie.setCacheMode(QMovie.CacheAll)
        
        self.background_label = QLabel(self)
        self.background_label.setMovie(self.movie)
        self.background_label.setAlignment(Qt.AlignCenter)
        self.background_label.setScaledContents(True)
        self.movie.start()

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)

        # --- 标题部分 ---
        title = QLabel("OpenLOA")
        title.setFont(QFont("Segoe UI", 48, QFont.Bold))
        title.setStyleSheet("color: white; letter-spacing: 5px;")
        title.setAlignment(Qt.AlignCenter)

        # 霓虹灯阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(255, 127, 80, 200)) # 橙色霓虹
        title.setGraphicsEffect(shadow)

        # --- 优化后的副标题样式 ---
        subtitle = QLabel("智能体联盟 · 真正高效的智能体由你定义")
        # 1. 字体加粗，字号稍微调大
        subtitle.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        # 2. 增加半透明背景色 (rgba)，并增加圆角边衬
        # 3. 字体颜色使用纯白，并增加字母间距
        subtitle.setStyleSheet("""
            color: white; 
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 8px 20px; 
            border-radius: 15px;
            letter-spacing: 2px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)

        # 4. 给副标题也加上强力的文字投影
        sub_shadow = QGraphicsDropShadowEffect(self)
        sub_shadow.setBlurRadius(15)
        sub_shadow.setOffset(0, 0)
        sub_shadow.setColor(QColor(0, 0, 0, 255)) # 纯黑阴影底色
        subtitle.setGraphicsEffect(sub_shadow)

        # --- 核心交互按钮 ---
        # 更有仪式感的按钮
        self.action_btn = QPushButton("现在启动") 
        self.action_btn.setFixedSize(280, 60)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                  stop:0 rgba(255, 127, 80, 255), stop:1 rgba(255, 95, 48, 255));
                border-radius: 30px;
                font-size: 18px;
                font-family: 'Microsoft YaHei';
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover { 
                background-color: #ff9f70; 
                border: 2px solid white;
            }
            QPushButton:pressed { 
                background-color: #ff5f30; 
                transform: scale(0.95);
            }
        """)
        self.action_btn.clicked.connect(switch_to_choose)

        # --- 页脚信息 (DeanFan1994 & OpenLOA) ---
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(5)
        
        project_info = QLabel("PROJECT: OpenLOA v1.0.0-OpenSource")
        project_info.setFont(QFont("Consolas", 10))
        project_info.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        project_info.setAlignment(Qt.AlignCenter)

        developer_info = QLabel("Developed by DeanFan1994 @ 就我智己AI工作室")
        developer_info.setFont(QFont("Segoe UI", 10))
        developer_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-style: italic;")
        developer_info.setAlignment(Qt.AlignCenter)

        footer_layout.addWidget(project_info)
        footer_layout.addWidget(developer_info)

        # 组件组装
        layout.addStretch(3)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(2)
        layout.addWidget(self.action_btn, alignment=Qt.AlignCenter)
        layout.addStretch(3)
        layout.addLayout(footer_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(self.rect())