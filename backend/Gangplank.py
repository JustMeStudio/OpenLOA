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
agent_model_config = load_model_config("Gangplank")
# 测试打印一下
if agent_model_config:
    print(f"Current model: {agent_model_config.get('model')}")

#-----------------------system prompt config-------------------------------------
system_prompt = """你是普朗克，可以根据用户正在招聘的具体岗位要求，为简历进行多维度的评审
你的工作流程：
1.用户需要将pdf或word格式的简历发送给你（支持批量操作）
2.你必须从用户获取明确具体的岗位要求，否则无法开始评审
3.当1和2都完成后，开始评审
4.将存有结果的excel表格的本地路径返回给用户"""
#--------------------------------------------------------------------------------
async def main():
    try:
        # self-introduction
        if language == "en":
            qprint("Hi! I'm Gangplank, your personal resume evaluation assistant. I can score resumes based on the specific job requirements you are recruiting for.\n\n1. Please send me the resumes in PDF or Word format (batch operation supported).\n2. You must provide me with clear and specific job requirements; otherwise, I won't be able to start the evaluation.\n3. Once I have both the resumes and the job requirements, I'll begin the evaluation process.\n4. After the evaluation is complete, I'll return the local path of the Excel file containing the results to you!")
        if language == "zh":
            print("我是普朗克，可以根据你的岗位需求对简历批量打分！\n1.请将需要评审的简历发送给我（支持pdf或word格式，批量操作）\n2.请明确告诉我你的岗位要求是什么，没有明确的岗位要求我无法进行评审\n3.当我同时收到1和2后，我会开始评审\n4.评审完成后，我会将存有结果的excel表格的本地路径返回给你！")

        #为本次项目创建资源目录(如果后续需要保存结果到本地)
        # time_stamp = str(int(time.time()))
        globals.PROJECT_NAME = project_name = f"Gangplank"
        globals.PROJECT_FILE_NAME = project_file_name = "rating_result.csv"
        globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
        globals.PROJECT_FILE_PATH = os.path.abspath(f"{project_path}/{project_file_name}")

        #声明本地自定义tools
        local_tool_boxes = [
            "Gangplank_tools",
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
        qprint(f"🛠️  Tools I've got:\n{tools_names}")

        qprint("🚀 I'm ready!")
        #开始对话
        try:
            await chat(agent_model_config, system_prompt, tools, tools_registry)
        finally:
            qprint("⏳ Trying to close MCP sessions...")
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("✅ MCP sessions closed.")
    except Exception as e:
        qprint(f"❌ Error occurred: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())