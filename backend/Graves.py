# -*- coding: utf-8 -*-
import os
import sys
import json 
import time 
import asyncio
from utils.com import qprint, chat
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers, load_all_tools_from_local_toolboxes
from utils.config import load_model_config
from globals import globals

# 防止前端输出乱码
sys.stdout.reconfigure(encoding="utf-8", newline=None)

#--------------------------API KEY config-------------------------------------------
agent_model_config = load_model_config("Graves")
# 测试打印一下
if agent_model_config:
    print(f"成功加载配置，正在使用模型: {agent_model_config.get('model')}")

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
        #开场白
        qprint("我是墨菲特，我可以帮你制作简历！\n告诉我你的")

        #为本次项目创建资源目录(如果后续需要保存结果到本地)
        # time_stamp = str(int(time.time()))
        globals.PROJECT_NAME = project_name = f"Graves"
        globals.PROJECT_FILE_NAME = project_file_name = "简历.html"
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
        qprint(f"已拥有的工具：\n{tools_names}")

        qprint("我已加入战场!")
        #开始对话
        try:
            await chat(agent_model_config, system_prompt, tools, tools_registry)
        finally:
            qprint("正在尝试结束会话进程......")
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("会话进程已结束......")
    except Exception as e:
        qprint(f"后端启动失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())