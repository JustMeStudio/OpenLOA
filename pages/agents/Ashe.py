# -*- coding: utf-8 -*-
import sys, os, json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMenu,
    QTextEdit, QPushButton, QLabel, QHBoxLayout,
    QScrollArea, QSizePolicy, QSplitter
)
from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtGui import QPixmap, QKeyEvent
from PySide6.QtWebEngineWidgets import QWebEngineView
import markdown

# 读取本智能体的参数信息
with open("./agents.json", "r", encoding="utf-8") as f:
    agents_list = json.load(f)
for agent in agents_list:
    if agent["page"] == "Ashe":
        name = agent["name"]
        avatar = agent["avatar"]
        break

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
        text_label.setTextFormat(Qt.RichText)
        text_label.setText(f"<b>{name}</b><br/><span style='font-size:14px;'>{escaped}</span>")
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
    def __init__(self, parent=None, Ashe_widget=None):
        super().__init__(parent)
        self.Ashe_widget = Ashe_widget
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
            if self.Ashe_widget:
                self.Ashe_widget.send_message()
            return
        super().keyPressEvent(event)

class Ashe(QWidget):
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

        # 输入行
        self.input_field = InputField(chat_widget, self)
        self.input_field.setPlaceholderText("请输入消息，Shift+Enter 换行，Enter 发送")
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        send_btn = QPushButton("发送")
        send_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_field, 1)
        input_layout.addWidget(send_btn)
        chat_layout.addLayout(input_layout)

        # 中间：文本编辑器
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("创作结果将显示在这里...")
        self.text_editor.setAcceptRichText(False)
        self.text_editor.setStyleSheet("border: 1px solid #ccc; padding: 5px;")

        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.text_editor)
        save_btn = QPushButton("提交保存")
        save_btn.clicked.connect(self.save)
        editor_layout.addWidget(save_btn)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        # 右侧：Markdown 预览
        self.preview_widget = QWebEngineView()
        self.preview_widget.setHtml("<html><body><p>Markdown 预览将显示在这里...</p></body></html>")
        self.preview_widget.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.preview_widget)
        self.save_png_btn = QPushButton("保存为长图")
        preview_layout.addWidget(self.save_png_btn)
        self.save_png_btn.clicked.connect(self.save_long_image)        
        
        preview_widget_container = QWidget()
        preview_widget_container.setLayout(preview_layout)

        self.text_editor.textChanged.connect(self.update_markdown_preview)

        # 添加到分割器
        splitter.addWidget(chat_widget)
        splitter.addWidget(editor_widget)
        splitter.addWidget(preview_widget_container)
        splitter.setSizes([400, 400, 400])
        main_layout.addWidget(splitter)

        # 后端启动
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)
        self.process.setWorkingDirectory("./backend")
        self.process.start("python", ["-u", "Ashe.py"])
    
    def save_long_image(self):
        def do_capture():
            # 执行 JS 脚本，获取完整内容宽高
            self.preview_widget.page().runJavaScript(
                "document.documentElement.scrollWidth", 
                lambda w: after_width(w)
            )
        def after_width(w):
            full_width = w + 10  # 额外边距
            self.preview_widget.page().runJavaScript(
                "document.documentElement.scrollHeight", 
                lambda h: after_height(full_width, h)
            )
        def after_height(full_width, h):
            full_height = h
            size = self.preview_widget.page().contentsSize().toSize()
            # 如果 contentsSize 不准，则直接用 JS 获取值
            if full_width > size.width() or full_height > size.height():
                self.preview_widget.setAttribute(Qt.WA_DontShowOnScreen, True)
                self.preview_widget.resize(full_width, full_height)
            else:
                self.preview_widget.resize(size)
            # 再延迟一段时间等待渲染
            QTimer.singleShot(500, take_screenshot)
        def take_screenshot():
            # 使用 grab()，也可以改用 render(img) 的方式
            pix = self.preview_widget.grab()
            os.makedirs("./output", exist_ok=True)
            save_path = "./output/markdown_pic.jpg"
            pix.save(save_path, 'JPG', quality=90)
            self.add_message(self.avatar, self.name, f"已保存长图至 {save_path}", is_sender=False)
            # 若设置了 WA_DontShowOnScreen，可适当销毁 widget 或恢复显示
            self.preview_widget.setAttribute(Qt.WA_DontShowOnScreen, False)
        QTimer.singleShot(500, do_capture) 

    def update_markdown_preview(self):
        markdown_text = self.text_editor.toPlainText()
        try:
            html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
            full_html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 10px; max-width: 100%; }}
                        pre, code {{ background-color: #f5f5f5; padding: 5px; border-radius: 3px; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        img {{ max-width: 100%; height: auto; display: block; }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
            </html>
            """
            self.preview_widget.setHtml(full_html)
        except Exception as e:
            self.preview_widget.setHtml(f"<html><body><p>Markdown 渲染失败: {str(e)}</p></body></html>")

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
            #用txt缓存前端输入，后端从txt读入
            input_file_path = os.path.abspath("./backend/prompt.txt")
            with open (input_file_path,"w",encoding="utf-8") as f:
                f.write(text)
            self.process.write(("-read "+ input_file_path + "\n").encode("utf-8"))

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
        self.add_message("", "[系统消息]", text.rstrip(), is_sender=False)

    def on_finished(self, exitCode, exitStatus):
        self.add_message("", "<i>后端已结束，退出码：</i>", str(exitCode), is_sender=False)

    def save(self):
        if not self.current_file_path:
            os.makedirs("./backend/agents/projects/cache", exist_ok=True)
            self.current_file_path = os.path.abspath("./backend/agents/projects/cache/Ashe_output.txt")
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_editor.toPlainText())
            self.add_message(self.avatar, self.name, f"你提交的修改我已查看并保存\n", is_sender=False)
            # self.process.write(f"我已经修改了内容，并把最新修改版本保存在了{self.current_file_path}\n".encode("utf-8"))
        except Exception as e:
            self.add_message(self.avatar, self.name, f"保存文件失败: {str(e)}", is_sender=False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Ashe()
    window.resize(1200, 400)
    window.show()
    sys.exit(app.exec())