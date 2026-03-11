import re
import os
import json
import shutil
import time
from pathlib import Path
from typing import Optional
from openai import OpenAI
from agent_utils.utils import qprint
from globals import globals


#图像提交MLLM识别内容
def image_understanding(image_path:str)->str:
    return "unknown"

def create_image_metadata(materials_folder_path:str):
    metadata =[]
    # 支持的图片后缀
    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
    # 使用 pathlib 遍历目录下所有符合后缀的图片文件
    base = Path(materials_folder_path)
    for img_path in base.iterdir():
        # 忽略非文件或不是图片扩展
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in IMAGE_EXTS:
            continue
        img_str_path = str(img_path)
        try:
            # 调用 image_understanding 获取内容
            content = image_understanding(img_str_path)
        except Exception as e:
            # 若识别失败，可记录异常信息或跳过
            content = f"ERROR: {e}"
        metadata.append({
            "file_type" : "image",
            "file_path": img_str_path,
            "content": content,
        })
    return metadata

def create_text_metadata(folder_path: str):
    base = Path(folder_path)
    files = sorted(base.iterdir())
    metadata = []
    for f in files:
        if not f.is_file():
            continue
        suffix = f.suffix.lower()
        info = {"local_file_path": str(f.resolve())}
        try:
            if suffix in [".txt", ".md"]:
                info["file_type"] = "text"
                info["content"] = f.read_text(encoding="utf-8")
            elif suffix == ".json":
                info["file_type"] = "json"
                info["content"] = json.loads(f.read_text(encoding="utf-8"))
            else:
                continue
        except Exception as e:
            info["error"] = str(e)
        metadata.append(info)
    return metadata

def generate_metadata(materials_folder_path:str, metadata_file_name:str):
    base = Path(materials_folder_path)
    if not base.exists() or not base.is_dir():
        raise ValueError(f"{materials_folder_path!r} 不是有效的目录")    
    metadata_path = f"{materials_folder_path}/{metadata_file_name}"
    text_metadata = create_text_metadata(materials_folder_path)
    image_metadata = create_image_metadata(materials_folder_path)
    metadata = []
    metadata.extend(text_metadata)
    metadata.extend(image_metadata)
    try:
        #先读取参考资料到全局变量
        globals.ASHE_EXTERNAL_MATERIALS = metadata
        #保存json到文件夹里作记录
        with open(metadata_path, 'w', encoding='utf-8') as outfile:
            json.dump(metadata, outfile, ensure_ascii=False, indent=2)
        return {"result":"succeed", "saved_path":metadata_path, "content":json.dumps(metadata, ensure_ascii=False)}
    except Exception as e:
        return {"result":"failed", "failure": str(e)}

#根据用户提供的资料文件路径列表，将文件统一抄送至艾希工作目录下的materials文件夹
def save_provided_files_to_material_folder(file_paths_list:list[str]):
    base_dir = globals.ASHE_MATERIAL_PATH = f"{globals.ASHE_WORKSPACE_PATH}/materials/{time.strftime('%Y%m%d_%H%M%S')}" 
    os.makedirs(base_dir, exist_ok=True)
    for src in file_paths_list:
        if not os.path.exists(src):
            qprint(f"源不存在，跳过：{src}")
            continue
        name = os.path.basename(src.rstrip(os.sep))
        dst = os.path.join(base_dir, name)
        try:
            if os.path.isdir(src):
                # 如果目标已存在且为目录，可允许合并覆盖
                shutil.copytree(src, dst, dirs_exist_ok=True)
                qprint(f"复制目录：{src} -> {dst}")
            else:
                # 文件或符号链接等，使用 copy2 保留 metadata
                shutil.copy2(src, dst)
                # qprint(f"复制文件/链接：{src} -> {dst}")
        except shutil.SameFileError:
            qprint(f"源目标相同，跳过：{src}")
        except PermissionError:
            qprint(f"权限错误，无法复制：{src}")
        except Exception as e:
            qprint(f"复制失败：{src}，错误：{e}")
    return {"result": "succeed", "materials_save_path": base_dir}

#一次读取文件夹里全部文件的内容信息
async def load_external_materials(file_paths_list:list[str]):
    copy_result = save_provided_files_to_material_folder(file_paths_list)
    if copy_result["result"] != "succeed":
        return {"result":"failed to copy files provided by user to Ashe workspace"}
    materials_folder_path = copy_result["materials_save_path"]
    external_materials_metadata_file_name = "external_materials.json"
    result = generate_metadata(materials_folder_path, external_materials_metadata_file_name)
    if result["result"] == "failed":
        return {"result":"failed to create metadata for resources", "failure": result["failure"]}
    return {"result":"successfully loaded agent-provided materials to RAM", "content":result["content"]}

#----------------------------------------------------------------------------------#

def get_latest_version(submit_path: str):
    names = [fn for fn in os.listdir(submit_path)
             if fn.startswith("output_") and fn.endswith(".md")]
    versions = []
    for fn in names:
        try:
            num = int(fn[len("output_"):-len(".md")])
            versions.append((num, fn))
        except ValueError:
            continue
    versions.sort()
    if versions:
        return versions[-1][0], versions[-1][1]
    return None, None

def request_LLM_api(prompt:str, system_prompt:str):
    #发送创作请求
    model_config ={
        # "base_url": "https://api.deepseek.com",
        # "model": "deepseek-chat",
        # # "model": "deepseek-reasoner",
        # "api_key": "sk-76c10143bb404f6a81ac472b99f0d688"

        # "api_key":"sk-121a8f5dd9f24398a51351a0b8e3e7d3", #私
        "api_key":"sk-fbe14e00e5b544c792039d72b250e0fa", 
        "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model":"qwen-plus-2025-07-14"
    }
    messages = [{"role": "system", "content":system_prompt}]
    messages.append({"role": "user", "content": prompt})
    client = OpenAI(api_key= model_config["api_key"], base_url= model_config["base_url"],)
    #正常识别流程
    for i in range(3):
        try:
            qprint("正在创作内容......")
            completion = client.chat.completions.create(
                model= model_config["model"],
                messages= messages,
            )
            content = completion.choices[0].message.content
            return content
        except Exception as e:
            qprint (f"创作过程到网络问题，第{i+1}次重试中......", str(e))
    qprint("很遗憾，由于网络原因没能完成创作")
    return None

#创作markdown内容，并保存在submit文件夹下（自动获取上一版本内容做参考,同时参考materials/external_material.json）
async def creat_markdown_content_and_save(requirements:str):
    submit_path = globals.ASHE_SUBMIT_PATH
    # 获取最近版本内容
    last_version_number, last_version_filename = get_latest_version(submit_path)
    last_version_content: Optional[str] = None
    if last_version_filename:
        with open(os.path.join(submit_path, last_version_filename), "r", encoding="utf-8") as f:
            last_version_content = f.read()
    # 计算当前版本文件名
    next_version_number = (last_version_number + 1) if last_version_number else 1
    current_fn = f"output_{next_version_number}.md"
    # 读取外部补充资料
    external_material_content: Optional[str] = None
    if globals.ASHE_EXTERNAL_MATERIALS:
        external_material_content = json.dumps(globals.ASHE_EXTERNAL_MATERIALS)
    #读取RAM中图奇抓取的信息
    materials_from_agents: Optional[str] = None
    if globals.TWITCH_SUBMIT_METADATA:
        materials_from_agents = json.dumps(globals.TWITCH_SUBMIT_METADATA)
    #构造创作请求
    prompt = "为我进行markdown文档创作，要求如下：\n" + requirements + "\n\n"
    if last_version_content:
        prompt = prompt + "你前一次创作的版本内容是：\n" + last_version_content + "\n\n"
    if external_material_content:
        prompt = prompt + "用户补充资料如下：\n" + external_material_content + "\n\n"
    if materials_from_agents:
        prompt = prompt + "网络爬虫智能体抓取到补充资料如下：\n" + materials_from_agents + "\n\n"
    #系统提示词
    system_prompt = ("你是职业写手，能根据客户的要求返回一份完美的markdown格式图文内容\n"
                     "注意:\n"
                     "1.返回纯净的markdown文本，开头不要添加```markdown\n"
                     "2.文本中插入的图片内容要和上下文有较强关联性，避免图文无关\n"
                     "3.图片尽量插入好看的，不带有广告或水印的，像素不需要太高，以横图为主，400*300比较合适"
                     "4.如果用户提出基于前一次创作来的内容来创作，你只能修改用户要求中提到的内容，禁止修改任何用户要求中没有提到的内容！"
                     "-示例：用户提出让你基于现有版本修改'口味虾'的图片，你仅仅替换'口味虾'的图片链接就好了，不能改动任何文字内容或其它图片"
    )
    content = request_LLM_api(prompt, system_prompt)
    #清空RAM里的来自用户的和来自图奇的全部参考资料
    globals.TWITCH_SUBMIT_METADATA = []
    globals.ASHE_EXTERNAL_MATERIALS = []
    #将content保存到指定目录，并且返回result和保存路径
    if content: 
        save_path = f"{globals.ASHE_SUBMIT_PATH}/{current_fn}"
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
        qprint(save_path)
        return {"result":"succeed", "newest_version_save_path":save_path}
    else:
        return {"result":"failed", "failure":"failed to create content......"}         


tool_registry = {
    "load_external_materials": load_external_materials,
    "creat_markdown_content_and_save": creat_markdown_content_and_save,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "load_external_materials",
            "description": "读取外部提供的资料文件到RAM里，待后面创作时使用\n",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths_list": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "传入一个由合法文件路径组成的列表"
                    }
                },
                "required": ["file_paths_list"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "creat_markdown_content_and_save",
            "description": "根据用户要求创作markdown内容并保存.md文件至本地（会自动参考RAM中已读取的所有外部资料和上一次的创作内容）",
            "parameters": {
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": ("创作要求（用自然语言描述），可包含创作主题，风格，是否插入图片，字数长度等\n"
                                        "**特别注意：我不能根据传入文件路径读取文件内容！请提前用load_external_materials读取内容到RAM!**"
                                        )
                    },
                },
                "required": ["requirements"]
            }
        }
    },    
]