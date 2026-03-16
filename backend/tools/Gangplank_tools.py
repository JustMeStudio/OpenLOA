import os
import asyncio
import json
import fitz  # PyMuPDF
from docx import Document
import pandas as pd
from typing import List
from globals import globals
from utils.com import request_LLM_api, qprint
from utils.config import load_tool_config

# 加载配置
cv_rating_model = load_tool_config("Gangplank_cv_rator")

# --- 1. 评分标准 System Prompt 配置 ---
CV_RATOR_SYSTEM_PROMPT = """你是一个专业的简历筛选助手。请严格按照以下标准和格式对简历进行深度评估。

## 1. 评分维度与权重
- d1教育背景(10%): 学历层次、院校背景、专业相关性。
- d2专业技能(15%): 技能契合度、深度与广度、硬性证书。
- d3工作经验(15%): 年限、职能匹配度、相关大厂/项目背景。
- d4项目经历(10%): 复杂度、职责重要性、技术落地成果。
- d5岗位匹配度(15%): 简历关键词与JD重合度、核心能力覆盖。
- d6行业经验(10%): 行业深耕年限、标杆企业经历。
- d7综合能力(10%): 软技能（沟通、协作、领导力）、问题解决能力。
- d8成果与荣誉(5%): 业绩指标、奖项证书、专利论文。
- d9语言与证书(5%): 外语水平、专业资格认证。
- d10简历质量(5%): 结构排版、逻辑表达、针对性优化。

## 2. 强制输出约束
- 必须返回纯净的 JSON 对象，不包含任何 Markdown 代码块标签（如 ```json）。
- 每个维度（d1-d10）必须包含“得分”和“原因”两个字段。
- 综合得分 = Σ(维度得分 × 权重)。

## 3. 严格字段定义 (按此顺序排列)
{
  "姓名": "字符串",
  "性别": "字符串",
  "年龄": "数字或字符串",
  "电话": "字符串",
  "邮箱": "字符串",
  "d1教育背景得分": 数字, "d1评分原因": "字符串",
  "d2专业技能得分": 数字, "d2评分原因": "字符串",
  "d3工作经验得分": 数字, "d3评分原因": "字符串",
  "d4项目经历得分": 数字, "d4评分原因": "字符串",
  "d5岗位匹配度得分": 数字, "d5评分原因": "字符串",
  "d6行业经验得分": 数字, "d6评分原因": "字符串",
  "d7综合能力得分": 数字, "d7评分原因": "字符串",
  "d8成果与荣誉得分": 数字, "d8评分原因": "字符串",
  "d9语言与证书得分": 数字, "d9评分原因": "字符串",
  "d10简历质量得分": 数字, "d10评分原因": "字符串",
  "综合得分": 数字,
  "综合评价": "字符串"
}"""

# --- 2. 文件读取逻辑 ---
def read_cv_content(cv_file_path: str) -> str:
    ext = os.path.splitext(cv_file_path)[1].lower()
    try:
        if ext == '.pdf':
            with fitz.open(cv_file_path) as doc:
                return "".join(page.get_text() for page in doc).strip()
        elif ext in ['.docx', '.doc']:
            doc = Document(cv_file_path)
            return "\n".join(p.text for p in doc.paragraphs).strip()
        else:
            with open(cv_file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        qprint(f"❌ 读取文件失败 {cv_file_path}: {e}")
        return ""

# --- 3. 单份简历评分逻辑（异步） ---
async def rate_single_cv_async(cv_path: str, job_desc: str, requirements: str = None) -> dict:
    content = read_cv_content(cv_path)
    if not content:
        return {"姓名": "解析失败", "源文件名": os.path.basename(cv_path)}
    user_prompt = f"【岗位需求】\n{job_desc}\n\n"
    if requirements:
        user_prompt += f"【额外评分要求】\n{requirements}\n\n"
    user_prompt += f"【简历内容】\n{content}"
    # 调用 API，强制 JSON 格式
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, 
        lambda: request_LLM_api(
            cv_rating_model, 
            user_prompt, 
            CV_RATOR_SYSTEM_PROMPT, 
            response_format={"type": "json_object"}
        )
    )
    try:
        data = json.loads(response)
        data["源文件名"] = os.path.basename(cv_path)  # 方便核对原始文件
        return data
    except Exception as e:
        qprint(f"⚠️ JSON解析失败 ({cv_path}): {e}")
        return {"姓名": "评分异常", "源文件名": os.path.basename(cv_path), "原始响应": response}


# ---cv bulk rator tool interface ---
async def bulk_rate_cv(cv_file_paths: List[str], job_description: str, rating_requirements: str = None) -> dict:
    """批量评分多个简历文件，最终返回一个 Excel 表格"""
    try:
        # 并发执行评分任务
        qprint(f"🚀 开始并发处理 {len(cv_file_paths)} 份简历...")
        tasks = [rate_single_cv_async(p, job_description, rating_requirements) for p in cv_file_paths]
        results = await asyncio.gather(*tasks)
        # 直接转换为 DataFrame
        df = pd.DataFrame(results)
        # 整理列顺序：将"源文件名"和"姓名"放在最前面，提升用户体验
        cols = df.columns.tolist()
        if "源文件名" in cols:
            cols.insert(0, cols.pop(cols.index("源文件名")))
        df = df[cols]
        # 保存 Excel
        xlsx_path = globals.PROJECT_FILE_PATH
        if not xlsx_path.lower().endswith('.xlsx'):
            xlsx_path = os.path.splitext(xlsx_path)[0] + ".xlsx"
        os.makedirs(os.path.dirname(xlsx_path), exist_ok=True)
        # 使用 ExcelWriter 可以进行更高级的格式设置（可选）
        df.to_excel(xlsx_path, index=False, engine='openpyxl')
        qprint(f"✅ 评分完成，导出至: {xlsx_path}")
        qprint(f"<file>{xlsx_path}")
        # open the file after saving
        os.startfile(xlsx_path)
        return {"result": "succeed", "xlsx_save_path": xlsx_path, "count": len(results)}
    except Exception as e:
        qprint(f"🔥 批量任务异常: {str(e)}")
        return {"result": "failed", "failure": str(e)}

#--- list files in directory ---
async def list_files_in_directory(directory: str):
    """工具函数：列出指定目录下的所有文件，返回文件名列表"""
    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        return {"result": "succeed", "files": files}
    except Exception as e:
        qprint(f"⚠️ 列目录失败 ({directory}): {e}")
        return {"result": "failed", "failure": str(e)}

#---------------------------------------------------tools----------------------------------------------------------------
tool_registry = {
    "bulk_rate_cv": bulk_rate_cv,
    "list_files_in_directory": list_files_in_directory,
}
tools =[
    {
        "type": "function",
        "function": {
            "name": "bulk_rate_cv",
            "description": "批量评分多个简历文件，根据给定的岗位描述和评分要求生成评分结果，并将结果保存为XLSX表格文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cv_file_paths": {
                        "type": "array",
                        "description": "包含多个简历文件路径的列表（支持PDF，Word，txt等大多数格式，例如['cv1.pdf', 'cv2.docx']）",
                        "items": {
                            "type": "string"
                        }
                    },
                    "job_description": {
                        "type": "string",
                        "description": "岗位描述，用于评估简历与岗位的匹配度"
                    }
                },
                "required": ["cv_file_paths", "job_description"]
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