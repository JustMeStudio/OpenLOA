import os
import re
import sys
import shutil
import webbrowser
import aiofiles
import subprocess
import time
from datetime import datetime
from playwright.async_api import async_playwright
from globals import globals
from utils.com import request_LLM_api, qprint
from utils.config import load_tool_config

cv_generator_model = load_tool_config("Graves_cv_generator")

#----------------------------------------------------------------------------------------
# generate html cv based on user description and photo, save the html file to local and return the path to front end for further processing (like preview, download, etc.)
async def generate_cv(self_description: str, photo_path: str = None, cv_style: str = "简约风"):
    copied_photo_path = None
    #另存图片到项目目录下的temps文件夹
    if photo_path:
        copied_photo_path = copy_to_project_folder(photo_path, globals.PROJECT_PATH)
    # Construct the prompt
    if copied_photo_path:
        prompt = f"我的个人简介：\n\n{self_description}\n\n我的证件照路径：{copied_photo_path}\n\n请根据以上信息帮我写一份简历，简历风格为{cv_style}。"
    else:
        prompt = f"我的个人简介：\n\n{self_description}\n\n请根据以上信息帮我写一份简历，简历风格为{cv_style}。"
    system_prompt = """
请根据用户提供的个人简介信息和证件照路径（如有），生成一份符合求职标准的 HTML 格式简历。具体要求如下：
1.证件照处理：
-如果用户未提供证件照路径，则生成不含照片的简历。
-如果用户提供了证件照路径，请将照片插入简历中，并与个人信息区域采用左右并排布局。
-使用 HTML 和内联 CSS 控制证件照尺寸，确保其显示比例协调、大小适中（建议高度在 120px–160px 之间），避免过大或过小影响整体美观。
2.排版与设计：
-简历样式风格和布局按照用户的要求进行设计（如简约风、现代风、创意风等），但必须保证内容清晰、结构合理，适合直接用于求职投递。
-使用清晰的标题层级、合理的留白和对齐方式，确保内容结构分明。
-适合A4纸张打印，建议使用常见的字体（如 Arial、Helvetica、Times New Roman 等）和适当的字体大小（正文建议 10–12pt，标题建议 14–16pt）。
-优先使用语义化 HTML 标签（如 、、–、 等）提升可读性与兼容性。
3.输出格式：
-仅输出纯净的 HTML 代码，不包含任何额外说明、注释或代码块标识（如不要包含 html 或 ``` 等 Markdown 语法）。
-所有样式应通过内联 CSS 实现，确保单文件即可完整呈现，无需外部依赖。
-请严格按照上述要求生成最终的 HTML 简历内容。
"""
    html_content = request_LLM_api(cv_generator_model, prompt, system_prompt)
    html_content = clean_leading_markdown(html_content)
    save_path = globals.PROJECT_FILE_PATH
    # Ensure the save directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    # Save html content
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    # 返回给前端做特殊处理（如预览、下载等）
    qprint(f"<file>{save_path}")
    # 用浏览器打开save_path
    webbrowser.open(f"file://{save_path}")
    return {"result": "success", "html_save_path": save_path}

def copy_to_project_folder(src_path, project_path):
    if not os.path.isfile(src_path):
        raise FileNotFoundError(f"Source file {src_path} does not exist.")
    base_name = os.path.basename(src_path)
    name, ext = os.path.splitext(base_name)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    new_filename = f"{timestamp}_{name}{ext}"
    dest_path = os.path.join(project_path, new_filename)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy(src_path, dest_path)
    return f"./{new_filename}"

def clean_leading_markdown(text):
    """
    清理文档中第一次出现 ```html 及其之前的所有内容。
    如果没找到 ```html，则返回原字符串或根据需求处理。
    """
    # 匹配 ```html 或 ```HTML，以及之后可能紧跟的换行符
    # re.I 表示忽略大小写，re.S 表示点号匹配包括换行符在内的所有字符
    pattern = r'.*?```html\s*'
    # sub 函数将匹配到的部分替换为空字符串，count=1 确保只替换第一次出现的
    cleaned_text = re.sub(pattern, '', text, count=1, flags=re.DOTALL | re.IGNORECASE)
    # 可选：如果结尾还有 ```，也可以一并清理掉
    cleaned_text = cleaned_text.split('```')[0].strip()
    return cleaned_text


# edit existing html cv based on user request, save the new html file to local and return the path to front end for further processing (like preview, download, etc.)
async def edit_cv(old_html_path: str, edit_request: str):
    """
    根据用户的修改要求，对现有的 HTML 简历进行内容或样式的调整。
    """
    if not os.path.exists(old_html_path):
        return {"result": "error", "message": f"未找到原简历文件：{old_html_path}"}
    # 1. 异步读取旧 HTML 内容
    async with aiofiles.open(old_html_path, mode='r', encoding='utf-8') as f:
        old_html_content = await f.read()
    # 2. 构建 Prompt
    prompt = f"这是我现有的 HTML 简历内容：\n\n{old_html_content}\n\n我的修改要求如下：\n{edit_request}\n\n请根据要求修改并返回完整的 HTML。"
    system_prompt = """
你是一位专业的简历优化专家。请根据用户提供的旧版 HTML 简历和修改要求，生成更新后的 HTML。
要求：
1. 保持或优化原有的 CSS 布局，确保简历美观。
2. 仅输出纯净的 HTML 代码，严禁包含 ```html 或任何 Markdown 标识符。
3. 确保所有修改准确无误，不要遗漏原简历中的重要信息（除非用户要求删除）。
4. 所有的样式必须依然保持为内联 CSS。
"""
    # 3. 调用 LLM (沿用你之前的 API 调用方式)
    new_html_content = request_LLM_api(cv_generator_model, prompt, system_prompt)
    new_html_content = clean_leading_markdown(new_html_content)
    # 4. 保存修改后的文件 (保存在同目录下，可以覆盖或加后缀)
    # 这里建议加一个后缀区分，或者直接覆盖 old_html_path
    save_path = get_timestamped_path(old_html_path)
    async with aiofiles.open(save_path, mode='w', encoding='utf-8') as f:
        await f.write(new_html_content)
    # 5. 返回结果
    qprint(f"<file>{save_path}")
    # 用浏览器打开save_path
    webbrowser.open(f"file://{save_path}")
    return {"result": "success", "updated_html_path": save_path}

def get_timestamped_path(old_path):
    # 拆分 路径+文件名 和 后缀
    base, ext = os.path.splitext(old_path)
    # 生成时间戳字符串，例如 20240520_143005
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{timestamp}{ext}"


# convert html to pdf using headless browser, ensure to keep background color and images, and set margin to 0
async def html_to_pdf(html_file: str):
    """
    将 HTML 文件转换为 PDF，路径固定在 HTML 文件同目录下，文件名相同。
    """
    # 1. 强制计算同目录下的 PDF 路径
    html_abs_path = os.path.abspath(html_file)
    if not os.path.exists(html_abs_path):
        return {"result": "error", "message": f"文件 {html_file} 不存在"}
    base, _ = os.path.splitext(html_abs_path)
    output_pdf = f"{base}.pdf"  # 路径固定：同名同目录
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception as e:
            if "playwright install" in str(e).lower():
                qprint("检测到未安装 Chromium 内核，正在启动自动安装...")
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
                browser = await p.chromium.launch()
            else:
                raise e
        page = await browser.new_page()
        file_url = f"file://{html_abs_path}"
        # 等待网络空闲，确保内联图片加载完成
        await page.goto(file_url, wait_until="networkidle", timeout=60000)
        await page.pdf(
            path=output_pdf,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            display_header_footer=False,
            prefer_css_page_size=True
        )
        await browser.close()
        qprint(f"PDF 已成功生成至同级目录: {output_pdf}")
        #打开pdf文件
        webbrowser.open(f"file://{output_pdf}")
        return {"result": "success", "pdf_save_path": output_pdf}


#------------------------------------------------------------------------------------------------------#

tool_registry = {
    "generate_cv": generate_cv,
    "edit_cv": edit_cv,
    "html_to_pdf": html_to_pdf
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_cv",
            "description": "根据个人简介和证件照路径生成一份html格式的简历",
            "parameters": {
                "type": "object",
                "properties": {
                    "self_description": {
                        "type": "string",
                        "description": "用户的个人简介,越详细越好"
                    },
                    "photo_path": {
                        "type": "string",
                        "description": "用户的证件照相路径（支持本地文件路径或网络url）",
                        "default": None
                    },
                    "cv_style": {
                        "type": "string",
                        "description": "简历风格, 如简约风、现代风、创意风等，可以自由描述",
                        "default": "简约风"
                    }
                },
                "required": ["self_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_cv",
            "description": "基于已有的 HTML 简历文件，根据用户的反馈（如修改工作描述、调整颜色、增加技能等）进行内容编辑，并另存为一个新版本的 HTML 文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_html_path": {
                        "type": "string",
                        "description": "需要修改的旧简历 HTML 文件的本地存储路径。"
                    },
                    "edit_request": {
                        "type": "string",
                        "description": "用户具体的修改指令，例如：'把自我评价改得更专业一点'、'增加一段在阿里的实习经历'、'将整体色调改为淡蓝色'。"
                    }
                },
                "required": ["old_html_path", "edit_request"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "html_to_pdf",
            "description": "将指定的 HTML 简历文件转换为 PDF 格式。生成的 PDF 将自动保存在与原 HTML 文件相同的目录下，文件名也保持一致。",
            "parameters": {
                "type": "object",
                "properties": {
                    "html_file": {
                        "type": "string",
                        "description": "需要转换的本地 HTML 简历文件路径。"
                    }
                },
                "required": ["html_file"]
            }
        }
    }
]