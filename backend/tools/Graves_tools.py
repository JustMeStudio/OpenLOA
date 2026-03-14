import os
import re
import json
import shutil
import asyncio
from globals import globals
from utils.com import request_LLM_api, qprint
from utils.config import load_tool_config

Graves_tools_config = load_tool_config("Graves_cv_generator")

#----------------------------------------------------------------------------------------

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
-优先使用语义化 HTML 标签（如 、、–、 等）提升可读性与兼容性。

3.输出格式：
-仅输出纯净的 HTML 代码，不包含任何额外说明、注释或代码块标识（如不要包含 html 或 ``` 等 Markdown 语法）。
-所有样式应通过内联 CSS 实现，确保单文件即可完整呈现，无需外部依赖。
-请严格按照上述要求生成最终的 HTML 简历内容。
"""

    html_content = request_LLM_api(Graves_tools_config, prompt, system_prompt)

    html_content = clean_leading_markdown(html_content)

    save_path = globals.PROJECT_FILE_PATH
    
    # Ensure the save directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Save html content
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 返回给前端做特殊处理（如预览、下载等）
    qprint(f"<file>{save_path}")

    return {"result": "success", "html_save_path": save_path}


def copy_to_project_folder(src_path, project_path):
    if not os.path.isfile(src_path):
        raise FileNotFoundError(f"Source file {src_path} does not exist.")
    filename = os.path.basename(src_path)
    dest_path = os.path.join(project_path, filename)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy(src_path, dest_path)
    #新图片与最终html文件在同一目录下，返回相对路径
    return f"./{filename}"

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
#------------------------------------------------------------------------------------------------------#

tool_registry = {
    "generate_cv":generate_cv,
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
                        "description": "简历风格, 如简约风、现代风、创意风等",
                        "default": "简约风"
                    }
                },
                "required": ["self_description"]
            }
        }
    }
]