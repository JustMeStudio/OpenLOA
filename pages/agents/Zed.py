import sys, os, json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMenu,
    QTextEdit, QPushButton, QLabel, QHBoxLayout,
    QScrollArea, QSizePolicy, QSplitter
)
from PySide6.QtCore import QProcess, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QKeyEvent

# Signal to notify parent to switch back to agent selection page
class Zed(QWidget):
    switch_to_agent_page = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能峡谷 - 聊天与编辑器")
        # 读取本智能体的参数信息
        with open("./configs/agents.json", "r", encoding="utf-8") as f:
            agents_list = json.load(f)
        for agent in agents_list:
            if agent["name"] == "Zed":
                self.name = agent["nick_name"]
                self.avatar = agent["avatar"]
        self.user_avatar = "./assets/avatar/蛮子.jpg"
        self.current_file_path = None

        # 主布局：左右分割
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：聊天界面
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        # 顶部布局：退出按钮
        top_layout = QHBoxLayout()
        exit_btn = QPushButton("返回大厅")
        exit_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        exit_btn.clicked.connect(self.exit_to_agent_page)
        top_layout.addWidget(exit_btn)
        top_layout.addStretch()  # Push button to the left
        chat_layout.addLayout(top_layout)

        # 聊天区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()
        self.chat_layout.setSpacing(5)
        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)

        # 输入行：按钮 + 输入框
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        self.input_field = InputField(chat_widget, self)
        self.input_field.setPlaceholderText("请输入消息，Shift+Enter 换行，Enter 发送")
        send_btn = QPushButton("发送")
        send_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_field, 1)
        input_layout.addWidget(send_btn)
        chat_layout.addLayout(input_layout)

        # 右侧：文本编辑器
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("文件内容将显示在这里...")
        self.text_editor.setAcceptRichText(False)
        self.text_editor.setStyleSheet("border: 1px solid #ccc; padding: 5px;")

        # 添加保存按钮
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.text_editor)
        save_btn = QPushButton("保存并投喂")
        save_btn.clicked.connect(self.save_and_feed)
        editor_layout.addWidget(save_btn)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        # 添加到分割器
        splitter.addWidget(chat_widget)
        splitter.addWidget(editor_widget)
        splitter.setSizes([800, 600])
        main_layout.addWidget(splitter)

        # 后端启动逻辑
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)
        self.process.setWorkingDirectory("./backend")
        self.process.start("python", ["-u", "Zed.py"])

    def add_message(self, avatar_path, name, message, is_sender=False):
        bubble = ChatBubble(avatar_path, name, message, is_sender)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum())

    def send_message(self):
        text = self.input_field.toPlainText()
        if text:
            self.add_message(self.user_avatar, "召唤师", text, is_sender=True)
            self.input_field.clear()
            self.input_field.setFixedHeight(50)
            input_file_path = os.path.abspath("./backend/prompt.txt")
            with open(input_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.process.write(("-read " + input_file_path + "\n").encode("utf-8"))

    def on_stdout(self):
        raw = bytes(self.process.readAllStandardOutput())
        try:
            text = raw.decode('utf-8').strip()
        except Exception:
            text = raw.decode('mbcs', errors='replace').strip()
        
        if text:
            if os.path.isfile(text):
                self.current_file_path = text
                try:
                    with open(text, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    self.text_editor.setPlainText(file_content)
                except Exception as e:
                    self.add_message(self.avatar, self.name, f"浏览创作结果失败: {str(e)}", is_sender=False)
            else:
                self.add_message(self.avatar, self.name, text.rstrip(), is_sender=False)

    def on_stderr(self):
        raw = bytes(self.process.readAllStandardError())
        try:
            text = raw.decode('utf-8')
        except Exception:
            text = raw.decode('mbcs', errors='replace')
        # self.add_message("", "[系统消息]", text.rstrip(), is_sender=False)

    def on_finished(self, exitCode, exitStatus):
        self.add_message("", "<i>后端已结束，退出码：</i>", str(exitCode), is_sender=False)

    def save_and_feed(self):
        if not self.current_file_path:
            os.makedirs("./backend/projects/cache", exist_ok=True)
            self.current_file_path = os.path.abspath("./backend/projects/cache/Zed_output.txt")
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_editor.toPlainText())
            self.add_message(self.user_avatar, "召唤师", f"我已经把最终版本保存在了{self.current_file_path}，请将它录入数据库\n", is_sender=True)
            self.process.write(f"我已经把最终版本保存在了{self.current_file_path}，请将它录入数据库\n".encode("utf-8"))
        except Exception as e:
            self.add_message(self.avatar, self.name, f"保存文件失败: {str(e)}", is_sender=False)

    def exit_to_agent_page(self):
        self.process.terminate()
        self.process.waitForFinished(1000)  # Wait up to 1 second for graceful termination
        if self.process.state() == QProcess.Running:
            self.process.kill()  # Force kill if not terminated
        self.switch_to_agent_page.emit()

class ChatBubble(QWidget):
    def __init__(self, avatar_path, name, message, is_sender=False):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        avatar_label = QLabel()
        if avatar_path:
            pix = QPixmap(avatar_path)
            if not pix.isNull():
                avatar_pix = pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                avatar_label.setPixmap(avatar_pix)
        avatar_label.setFixedSize(40, 40)
        avatar_label.setStyleSheet("border-radius: 20px;")
        text_label = QLabel()
        escaped = (message.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br/>"))
        text_html = f"<b>{name}</b><br/><span style='font-size:14px;'>{escaped}</span>"
        text_label.setTextFormat(Qt.RichText)
        text_label.setText(text_html)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"""
            QLabel {{
                background-color: {"#DCF8C6" if is_sender else "#FFFFFF"};
                border-radius: 10px;
                padding: 6px 10px;
                max-width: 400px;
            }}
        """)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_label.setContextMenuPolicy(Qt.CustomContextMenu)
        def show_context_menu(pos):
            if text_label.hasSelectedText():
                menu = QMenu(text_label)
                copy_action = menu.addAction("复制")
                action = menu.exec_(text_label.mapToGlobal(pos))
                if action == copy_action:
                    clipboard = QApplication.clipboard()
                    clipboard.setText(text_label.selectedText())
        text_label.customContextMenuRequested.connect(show_context_menu)
        if is_sender:
            layout.addStretch()
            layout.addWidget(text_label)
            layout.addWidget(avatar_label)
        else:
            layout.addWidget(avatar_label)
            layout.addWidget(text_label)
            layout.addStretch()

class InputField(QTextEdit):
    def __init__(self, parent=None, zed_widget=None):
        super().__init__(parent)
        self.zed_widget = zed_widget
        self.setAcceptRichText(False)
        self.setFixedHeight(50)
        self.textChanged.connect(self.adjustHeight)

    def adjustHeight(self):
        doc = self.document()
        doc_height = doc.size().height()
        margin = self.frameWidth() * 2 + doc.documentMargin() * 2
        new_h = int(doc_height + margin + 8)
        max_h = 150
        new_h = min(max(new_h, 50), max_h)
        if new_h != self.height():
            self.setFixedHeight(new_h)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            if self.zed_widget:
                self.zed_widget.send_message()
            return
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Zed()
    window.resize(800, 400)
    window.show()
    sys.exit(app.exec())