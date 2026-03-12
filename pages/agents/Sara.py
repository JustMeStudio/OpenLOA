import sys, os, json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMenu,
    QTextEdit, QPushButton, QLabel, QHBoxLayout,
    QScrollArea, QSizePolicy, QSplitter, QFileDialog
)
from PySide6.QtCore import QProcess, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QKeyEvent

# 读取本智能体的参数信息
with open("./configs/agents.json", "r", encoding="utf-8") as f:
    agents_list = json.load(f)
for agent in agents_list:
    if agent["name"] == "Sara":
        name = agent["nick_name"]
        avatar = agent["avatar"]

class ChatBubble(QWidget):
    def __init__(self, avatar_path, name, message, is_sender=False):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        # 头像显示部分
        avatar_label = QLabel()
        if avatar_path:
            pix = QPixmap(avatar_path)
            if not pix.isNull():
                avatar_pix = pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                avatar_label.setPixmap(avatar_pix)
        avatar_label.setFixedSize(40, 40)
        avatar_label.setStyleSheet("border-radius: 20px;")
        # 气泡框内的文本样式
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
        # 启用文本选择
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # 启用右键菜单
        text_label.setContextMenuPolicy(Qt.CustomContextMenu)
        def show_context_menu(pos):
            # 检查是否有选中文本
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
    def __init__(self, parent=None, sara_widget=None):
        super().__init__(parent)
        self.sara_widget = sara_widget
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
            if self.sara_widget:
                self.sara_widget.send_message()
            return
        super().keyPressEvent(event)

class Sara(QWidget):
    switch_to_agent_page = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能峡谷 - 聊天与编辑器")
        self.name = name
        self.avatar = avatar
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
        top_layout.addStretch()  # 推到左侧
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

        # 输入行：附件按钮 + 输入框 + 发送按钮
        self.input_field = InputField(chat_widget, self)
        self.input_field.setPlaceholderText("请输入消息，Shift+Enter 换行，Enter 发送")
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        
        # 添加附件按钮
        attach_btn = QPushButton("选择简历")
        attach_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        attach_btn.setFixedSize(60, 60)
        attach_btn.clicked.connect(self.select_attachment)
        input_layout.addWidget(attach_btn)
        
        input_layout.addWidget(self.input_field, 1)
        send_btn = QPushButton("发送")
        send_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        chat_layout.addLayout(input_layout)

        # 右侧：文本编辑器
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("已投递过的职位将会显示在这里...")
        self.text_editor.setAcceptRichText(False)
        self.text_editor.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        self.text_editor.setReadOnly(True)

        # 添加清空记录按钮
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.text_editor)
        clear_btn = QPushButton("清空投递记录")
        clear_btn.clicked.connect(self.clear_records)
        editor_layout.addWidget(clear_btn)

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
        self.process.start("python", ["-u", "Sara.py"])

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
            # 用txt缓存前端输入，后端从txt读入
            input_file_path = os.path.abspath("./backend/prompt.txt")
            with open(input_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.process.write(("-read " + input_file_path + "\n").encode("utf-8"))

    def select_attachment(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择附件", "", "All Files (*);;PDF Files (*.pdf);;Text Files (*.txt)"
        )
        if file_path:
            self.add_message(self.user_avatar, "召唤师", f"我已成功选择简历，简历文件存放在：{file_path}", is_sender=True)
            self.process.write((f"attachment:{file_path}\n").encode("utf-8"))

    def on_stdout(self):
        raw = bytes(self.process.readAllStandardOutput())
        try:
            text = raw.decode('utf-8').strip()
        except Exception:
            text = raw.decode('mbcs', errors='replace').strip()
        if text:
            if os.path.isfile(text):
                self.current_file_path = text
                self._display_file_content(text)
            else:
                self.add_message(self.avatar, self.name, text.rstrip(), is_sender=False)

    def _display_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            self._render_json_content(file_content)
        except Exception as e:
            self.add_message(self.avatar, self.name, f"读取文件失败: {str(e)}", is_sender=False)

    def _render_json_content(self, file_content):
        try:
            data = json.loads(file_content)
            if isinstance(data, list) and data:
                html = self._generate_html_table(data)
                self.text_editor.setHtml(html)
            else:
                self.text_editor.setPlainText(file_content)
        except json.JSONDecodeError as e:
            self.add_message(self.avatar, self.name, f"解析JSON失败: {str(e)}", is_sender=False)
            self.text_editor.setPlainText(file_content)
        except Exception as e:
            self.add_message(self.avatar, self.name, f"浏览投递结果失败: {str(e)}", is_sender=False)

    def _generate_html_table(self, data):
        headers = list(data[0].keys())
        html = '<table border="1" style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background-color: #f2f2f2;">'
        for header in headers:
            html += f'<th style="padding: 8px; text-align: left;">{header}</th>'
        html += '</tr>'
        for item in data:
            html += '<tr>'
            for header in headers:
                value = item.get(header, '')
                value = (str(value).replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('\n', '<br/>'))
                html += f'<td style="padding: 8px;">{value}</td>'
            html += '</tr>'
        html += '</table>'
        return html

    def on_stderr(self):
        raw = bytes(self.process.readAllStandardError())
        try:
            text = raw.decode('utf-8')
        except Exception:
            text = raw.decode('mbcs', errors='replace')
        # self.add_message("", "[系统消息]", text.rstrip(), is_sender=False)

    def on_finished(self, exitCode, exitStatus):
        self.add_message("", "<i>后端已结束，退出码：</i>", str(exitCode), is_sender=False)

    def clear_records(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                self.text_editor.setPlainText("[]")
                self.add_message(self.avatar, self.name, f"已清空投递记录", is_sender=False)
            except Exception as e:
                self.add_message(self.avatar, self.name, f"清空文件失败: {str(e)}", is_sender=False)
        else:
            self.add_message(self.avatar, self.name, "没有可清空的文件路径", is_sender=False)

    def exit_to_agent_page(self):
        print("Sara: 尝试终止后端进程")
        self.process.terminate()
        self.process.waitForFinished(1000)  # 等待最多1秒以优雅终止
        if self.process.state() == QProcess.Running:
            print("Sara: 进程未终止，强制杀死")
            self.process.kill()
        else:
            print("Sara: 后端进程已成功终止")
        print("Sara: 发出 switch_to_agent_page 信号")
        self.switch_to_agent_page.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Sara()
    window.resize(800, 400)
    window.show()
    sys.exit(app.exec())