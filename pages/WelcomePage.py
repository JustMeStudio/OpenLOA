from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect, QLineEdit, QTabWidget, QHBoxLayout, QFormLayout, QMessageBox
from PySide6.QtGui import QMovie, QFont, QColor
from PySide6.QtCore import Qt

#登录请求
def login():
    return {"status": "succeed", "prompt": "登录成功"}

class WelcomePage(QWidget):
    def __init__(self, switch_to_choose):
        super().__init__()

        self.movie = QMovie("./assets/home/2.gif")
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)

        self.background_label = QLabel(self)
        self.background_label.setMovie(self.movie)
        self.background_label.setAlignment(Qt.AlignCenter)
        self.background_label.setScaledContents(True)
        self.background_label.setGeometry(self.rect())
        self.movie.start()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("🎉 欢迎来到 《智能体联盟》")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(5, 5)
        shadow.setColor(QColor(0, 0, 0, 200))
        title.setGraphicsEffect(shadow)

        subtitle = QLabel("即刻登录，进入智能峡谷")
        subtitle.setFont(QFont("Segoe UI", 14, QFont.Bold))
        subtitle.setStyleSheet("color: white;")
        subtitle.setAlignment(Qt.AlignCenter)
        sub_shadow = QGraphicsDropShadowEffect(self)
        sub_shadow.setBlurRadius(8)
        sub_shadow.setOffset(3, 3)
        sub_shadow.setColor(QColor(0, 0, 0, 200))
        subtitle.setGraphicsEffect(sub_shadow)

        watermark = QLabel("就我智己AI工作室")
        watermark.setFont(QFont("Segoe UI", 10))
        watermark.setStyleSheet("color: white; opacity: 0.7;")
        watermark.setAlignment(Qt.AlignCenter)

        self.tab_widget = QTabWidget()
        self.tab_widget.setFixedWidth(400)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ffffff;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            QTabBar::tab {
                background: #ff7f50;
                color: white;
                padding: 10px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #ff9f70;
            }
        """)

        # 登录 Tab
        login_tab = QWidget()
        self.login_layout = QFormLayout()
        self.login_layout.setSpacing(15)

        self.login_phone = QLineEdit()
        self.login_phone.setPlaceholderText("请输入手机号")
        self.login_phone.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("请输入密码")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")

        self.login_code = QLineEdit()
        self.login_code.setPlaceholderText("请输入验证码")
        self.login_code.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")

        self.send_code_btn = QPushButton("发送")
        self.send_code_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff7f50;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #ff9f70; }
            QPushButton:pressed { background-color: #ff5f30; }
        """)

        self.code_layout = QHBoxLayout()
        self.code_layout.addWidget(self.login_code)
        self.code_layout.addWidget(self.send_code_btn)

        # Create a container widget for the input field (password or code)
        self.input_container = QWidget()
        self.input_layout = QVBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        self.input_layout.addWidget(self.login_password)  # Start with password field

        self.input_label = QLabel("密码:")
        self.toggle_link = QLabel('<a href="#" style="color: #ff7f50; text-decoration: underline;">短信验证码登录</a>')
        self.toggle_link.setAlignment(Qt.AlignRight)
        self.toggle_link.setTextFormat(Qt.RichText)
        self.toggle_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.toggle_link.linkActivated.connect(self.toggle_login_mode)

        self.is_password_mode = True
        self.login_layout.addRow("手机号:", self.login_phone)
        self.login_layout.addRow(self.input_label, self.input_container)
        self.login_layout.addRow("", self.toggle_link)
        login_tab.setLayout(self.login_layout)

        # 注册 Tab
        register_tab = QWidget()
        register_layout = QFormLayout()
        register_layout.setSpacing(15)

        self.register_phone = QLineEdit()
        self.register_phone.setPlaceholderText("请输入手机号")
        self.register_phone.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")

        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("请输入密码")
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")

        self.register_code = QLineEdit()
        self.register_code.setPlaceholderText("请输入验证码")
        self.register_code.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")

        register_code_btn = QPushButton("发送验证码")
        register_code_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff7f50;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #ff9f70; }
            QPushButton:pressed { background-color: #ff5f30; }
        """)

        register_code_layout = QHBoxLayout()
        register_code_layout.addWidget(self.register_code)
        register_code_layout.addWidget(register_code_btn)

        register_layout.addRow("手机号:", self.register_phone)
        register_layout.addRow("密码:", self.register_password)
        register_layout.addRow("验证码:", register_code_layout)
        register_tab.setLayout(register_layout)

        self.tab_widget.addTab(login_tab, "登录")
        self.tab_widget.addTab(register_tab, "注册")

        self.action_btn = QPushButton("登录")
        self.action_btn.setFixedSize(200, 50)
        self.action_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #ff7f50;
                border-radius: 25px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #ff9f70; }
            QPushButton:pressed { background-color: #ff5f30; }
        """)
        self.action_btn.clicked.connect(lambda: self.handle_login(switch_to_choose))

        # Connect tab change signal to update button text
        self.tab_widget.currentChanged.connect(self.update_button_text)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.tab_widget, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.action_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(watermark)

    def update_button_text(self, index):
        if index == 1:  # Register tab index
            self.action_btn.setText("注册并登录")
        else:  # Login tab index
            self.action_btn.setText("登录")

    def handle_login(self, switch_to_choose):
        result = login()
        if result["status"] == "succeed":
            switch_to_choose()
        else:
            QMessageBox.warning(self, "登录失败", result["prompt"])

    def toggle_login_mode(self):
        # Clear the input layout safely
        while self.input_layout.count():
            item = self.input_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)  # Remove widget without deleting
            elif item.layout():
                item.layout().setParent(None)  # Remove layout without deleting

        if self.is_password_mode:
            # Switch to code mode
            self.input_layout.addLayout(self.code_layout)
            self.input_label.setText("验证码:")
            self.toggle_link.setText('<a href="#" style="color: #ff7f50; text-decoration: underline;">密码登录</a>')
            self.is_password_mode = False
        else:
            # Switch to password mode
            self.input_layout.addWidget(self.login_password)
            self.input_label.setText("密码:")
            self.toggle_link.setText('<a href="#" style="color: #ff7f50; text-decoration: underline;">短信验证码登录</a>')
            self.is_password_mode = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(self.rect())