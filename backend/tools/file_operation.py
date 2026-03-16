import os
import asyncio
import pandas as pd
import fitz  # PyMuPDF
from docx import Document
from backend.utils.com import qprint


# read document file content, support txt, md, csv, pdf, docx, xlsx, xls
async def read_document(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在。")
    ext = os.path.splitext(file_path)[1].lower()
    # 将阻塞的 IO 操作放入线程池中执行，避免卡死异步循环
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _read_content, file_path, ext)

def _read_content(file_path, ext):
    """核心读取逻辑"""
    try:
        # 1. 文本类 (txt, md, csv)
        if ext in ['.txt', '.md']:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            return df.to_string()
        # 2. PDF 类
        elif ext == '.pdf':
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        # 3. Word 类 (.docx)
        elif ext == '.docx':
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        # 4. Excel 类 (.xlsx, .xls)
        elif ext in ['.xlsx', '.xls']:
            # 读取所有 sheet 并合并
            dict_df = pd.read_excel(file_path, sheet_name=None)
            combined_text = ""
            for sheet_name, df in dict_df.items():
                combined_text += f"Sheet: {sheet_name}\n{df.to_string()}\n\n"
            return combined_text
        else:
            return f"不支持的文件格式: {ext}"
    except Exception as e:
        return f"读取文件 {file_path} 时出错: {str(e)}"
    

# list directory files tool
async def list_files_in_directory(directory: str):
    """工具函数：列出指定目录下的所有文件，返回文件名列表"""
    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        return {"result": "succeed", "files": files}
    except Exception as e:
        qprint(f"⚠️ 列目录失败 ({directory}): {e}")
        return {"result": "failed", "failure": str(e)}
#--------------------------------------------------------------------------------
tool_registry = {
    "read_document": read_document,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "read and extract text content from document files: txt, md, csv, pdf, docx, xlsx, xls。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "local path, e.g., 'data/report.pdf' or 'C:/docs/notes.txt'."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files_in_directory",
            "description": "列出指定目录下的所有文件，返回文件名列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出文件的目录路径"
                    }
                },
                "required": ["directory"]
            }
        }
    }
]