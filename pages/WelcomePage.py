from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect, QHBoxLayout, QComboBox
from PySide6.QtGui import QMovie, QFont, QColor
from PySide6.QtCore import Qt
from pages.i18n import get_current_language, set_language, get_text

class WelcomePage(QWidget):
    def __init__(self, switch_to_choose, choose_agent_page=None):
        super().__init__()
        
        # 保存ChooseAgentPage的引用，以便在语言改变时更新它
        self.choose_agent_page = choose_agent_page
        
        # 获取当前语言
        self.current_language = get_current_language()

        # 背景动效
        self.movie = QMovie("./assets/home/2.gif")
        self.movie.setCacheMode(QMovie.CacheAll)
        
        self.background_label = QLabel(self)
        self.background_label.setMovie(self.movie)
        self.background_label.setAlignment(Qt.AlignCenter)
        self.background_label.setScaledContents(True)
        self.movie.start()

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)

        # --- 顶部语言选择 ---
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        lang_label = QLabel(get_text('language', self.current_language))
        lang_label.setFont(QFont("Segoe UI", 10))
        lang_label.setStyleSheet("color: white;")
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("中文", "zh")
        # 设置当前选项
        current_index = self.lang_combo.findData(self.current_language)
        if current_index >= 0:
            self.lang_combo.setCurrentIndex(current_index)
        self.lang_combo.setFixedWidth(100)
        self.lang_combo.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: rgba(255, 127, 80, 200);
                border: 1px solid white;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.lang_combo.currentIndexChanged.connect(lambda: self.on_language_changed(self.lang_combo.currentData()))
        
        top_bar.addWidget(lang_label)
        top_bar.addWidget(self.lang_combo)
        layout.addLayout(top_bar)

        # --- 标题部分 ---
        title = QLabel(get_text('title', self.current_language))
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
        subtitle = QLabel(get_text('subtitle', self.current_language))
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
        subtitle.setWordWrap(True)

        # 4. 给副标题也加上强力的文字投影
        sub_shadow = QGraphicsDropShadowEffect(self)
        sub_shadow.setBlurRadius(15)
        sub_shadow.setOffset(0, 0)
        sub_shadow.setColor(QColor(0, 0, 0, 255)) # 纯黑阴影底色
        subtitle.setGraphicsEffect(sub_shadow)

        # --- 核心交互按钮 ---
        # 更有仪式感的按钮
        self.action_btn = QPushButton(get_text('start_btn', self.current_language)) 
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
            }
        """)
        self.action_btn.clicked.connect(switch_to_choose)

        # --- 页脚信息 (JustMeStudio & OpenLOA) ---
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(5)
        
        project_info = QLabel(get_text('project_info', self.current_language))
        project_info.setFont(QFont("Consolas", 10))
        project_info.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        project_info.setAlignment(Qt.AlignCenter)

        developer_info = QLabel(get_text('developer_info', self.current_language))
        developer_info.setFont(QFont("Segoe UI", 10))
        developer_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-style: italic;")
        developer_info.setAlignment(Qt.AlignCenter)

        footer_layout.addWidget(project_info)
        footer_layout.addWidget(developer_info)

        # 保存引用以便更新
        self.title_label = title
        self.subtitle_label = subtitle
        self.project_info_label = project_info
        self.developer_info_label = developer_info

        # 组件组装
        layout.addStretch(3)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(2)
        layout.addWidget(self.action_btn, alignment=Qt.AlignCenter)
        layout.addStretch(3)
        layout.addLayout(footer_layout)

    def on_language_changed(self, language):
        """语言改变时的回调"""
        self.current_language = language
        set_language(language)
        
        # 更新所有UI文本
        self.title_label.setText(get_text('title', language))
        self.subtitle_label.setText(get_text('subtitle', language))
        self.action_btn.setText(get_text('start_btn', language))
        self.project_info_label.setText(get_text('project_info', language))
        self.developer_info_label.setText(get_text('developer_info', language))
        
        # 同时更新ChooseAgentPage的语言
        if self.choose_agent_page is not None:
            self.choose_agent_page.update_language(language)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(self.rect())