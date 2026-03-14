# -*- coding: utf-8 -*-
import os
import sys
import json 
import time 
import asyncio
from utils.com import qprint, chat
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers, load_all_tools_from_local_toolboxes
from utils.config import load_model_config, load_user_settings
from globals import globals

# in case of encoding issues in the terminal
sys.stdout.reconfigure(encoding="utf-8", newline=None)

#-------------------------user settings config--------------------------------------
user_settings = load_user_settings()
language = user_settings.get("language", "en")

#--------------------------API KEY config-------------------------------------------
agent_model_config = load_model_config("Graves")
# 测试打印一下
if agent_model_config:
    print(f"Current model: {agent_model_config.get('model')}")

#-----------------------system prompt config-------------------------------------
system_prompt = """# 角色设定

你是一位专业的简历生成助手。你的核心任务是帮助用户高效、美观地创建个人简历。

## 工作流程

### 1. 信息收集
- 请用户尽可能提供**完整详实的个人资料**，包括：基本信息、教育背景、工作经历、项目经验、技能特长、证书奖项等。
- **样式风格确认**：在生成前，请主动询问用户需要的简历风格（如：**经典商务、互联网极简、学术严谨、创意彩色**等），以确保 HTML 排版符合用户预期。
- 若用户提供的信息不完整或模糊，请**主动、友好地追问**，确保内容充实且具有竞争力。

### 2. 证件照提醒
- 如果用户**未主动上传证件照**，请温馨提醒：
  > “为了提升简历的专业度和视觉效果，建议您上传一张标准证件照。我可以将其自动嵌入到简历中。”

### 3. 简历生成
- 在确认信息完整及风格偏好后，调用 `generate_cv` 工具开始生成简历html文件。

## 沟通原则
- 保持**专业、耐心、细致**的语气。
- 始终以用户为中心，致力于打造一份**令人印象深刻、高度个性化的高质量简历**。"""
#--------------------------------------------------------------------------------
async def main():
    try:
        # self-introduction
        if language == "en":
            qprint("Hi! I'm Graves, your personal resume assistant. I can create a professional and visually appealing resume for you.\n\n1. Please provide me with detailed information about yourself, including your basic info, education, work experience, projects, skills, certifications, etc.\n2. Let me know your preferred resume style (e.g., classic business, minimalist tech, academic, creative colorful) so I can tailor the layout to your liking.\n3. If you haven't uploaded a profile picture yet, I recommend doing so to make your resume look more polished and professional. I can automatically embed it into the resume for you!\n4. Once I have all the necessary information and style preferences, I'll generate a high-quality personalized resume for you!")
        if language == "zh":
            print("我是格雷福斯，我可以为你制作简历！\n1.向我描述一下你的基本信息，越详细越好（包括教育经历、工作经历、项目经验、技能特长等）\n2.告诉我你喜欢的简历风格（比如：经典商务、互联网极简、学术严谨、创意彩色等）\n3.最好提供给我一张你的证件照（本地完整路径或网络url），这样可以让你的简历看起来更专业哦！\n4.当你准备好后，我会帮你生成一份高质量的个性化简历！")

        #为本次项目创建资源目录(如果后续需要保存结果到本地)
        # time_stamp = str(int(time.time()))
        globals.PROJECT_NAME = project_name = f"Graves"
        globals.PROJECT_FILE_NAME = project_file_name = "resume.html"
        globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
        globals.PROJECT_FILE_PATH = os.path.abspath(f"{project_path}/{project_file_name}")

        #声明本地自定义tools
        local_tool_boxes = [
            "Graves_tools",
        ]
        local_tools, local_tools_registry = load_all_tools_from_local_toolboxes(local_tool_boxes)
        #声明本地部署MCP Server + SSE远端MCP Server
        mcp_servers = [
            # 以下为示例写法
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", "./Twitch_workspace"]),   #文件系统控制（npx包）
            # MCPToolSession("uvx", ["--index-url","https://pypi.tuna.tsinghua.edu.cn/simple","mcp-pandoc"]),    #标记文本格式互转 (uvx包)    
            # MCPToolSession("npx", ["-y", "./local_servers/12306-mcp"]),   #火车票查询（本地包)
            # MCPToolSession(sse_url="https://mcp-youxuan.baidu.com/mcp/sse?key=<your api key>"),   #百度优选MCP(SSE链接) 
        ]
        mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers) 
        #合并工具箱  
        tools = local_tools + mcp_tools
        tools_registry = local_tools_registry | mcp_registry
        #列举所有工具
        tools_names = "\n".join(tools_registry.keys())
        qprint(f"Tools i've got：\n{tools_names}")

        qprint("I'me ready!")
        #开始对话
        try:
            await chat(agent_model_config, system_prompt, tools, tools_registry)
        finally:
            qprint("Trying to close MCP sessions......")
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("MCP sessions closed......")
    except Exception as e:
        qprint(f"Error occurred: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())