import re
import os
import json


# 本包用于以下MCP Server的返回内容清理
# MCPToolSession("npx", ["@apify/mcp-server-rag-web-browser"], {"APIFY_TOKEN": "apify_api_ZGrscn4a5AV6hv3ndmaPiI46tTU0cC0K5sMF"})

def clean_text(content):
    content = re.sub(r'!\[\]\((.*?)\)', '', content)
    content = re.sub(r'\[\]\((.*?)\)', '', content)
    pattern = re.compile(r'(?<!\!)\[(.*?)\]\(.*?\)') 
    content = pattern.sub('', content)
    content = content.replace(" ", "")
    content = content.replace("*", "")
    content = re.sub(r'(?:\\\\n){3,}', r'\\\\n\\\\n', content)
    content = content.replace(r"\\\\","")
    # 1. 匹配所有 ![描述](链接)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    # 2. 构造 image_content_list
    image_content_list = [
        {"type": "image", "content": desc, "url": url}
        for desc, url in matches
    ]
    print(image_content_list)
    # 3. 删除原文中的图片标签
    content = re.sub(pattern, '', content)
    content_objects = json.loads(content)
    content_objects["content"].extend(image_content_list)
    content=json.dumps(content_objects, ensure_ascii=False, indent=2)
    return content

def append_json_content(content: str, save_path: str):
    try:
        new_obj = json.loads(content)
    except json.JSONDecodeError as e:
        return {"result": "failed", "failure": f"内容不是合法 JSON 字符串: {e}"}
    data = []
    if os.path.exists(save_path):
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                return {"result": "failed", "failure": "已有文件内容不是 JSON 列表"}
        except (json.JSONDecodeError, OSError) as e:
            return {"result": "failed", "failure": f"读取已有文件失败: {e}"}
    data.append(new_obj)
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        return {"result": "failed", "failure": f"写入文件失败: {e}"}
    return {"result": "succeed saved search result to local file", "local_save_path": save_path}