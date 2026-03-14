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
agent_model_config = load_model_config("Zed")
# 测试打印一下
if agent_model_config:
    print(f"成功加载配置，正在使用模型: {agent_model_config.get('model')}")

#-----------------------system prompt config-------------------------------------
system_prompt = (
    "你是一个仿风格写手，能像原作者的分身一般复刻他的写作风格完成写作任务\n"
    "你的工作流程：\n"
    "1.当用户发来一句话时，首先询问客户这是不是本次写作的线索\n"
    "-如果用户回答是，就调用写作工具根据该线索写作\n"
    "-如果用户回答不是，就询问客户本次写作的完整线索是什么\n"
    "2.当你完成创作后，告诉用户在右边的编辑框中查看并编辑你的创作结果，编辑完以后可以点击'保存并投喂'按钮将最终结果保存在我的数据库，方便下次创作时参考\n"
    "3.除非你收到用户指令将创作内容录入到数据库，否则任何时候不要擅自录入！"
)


#--------------------------------------------------------------------------------
async def main():
    try:
        #开场白
        if language == "en":
            qprint("Hi! I'm Zed, your personal writing assistant. I can mimic your writing style and help you with various writing tasks.\n\n"
                   "Here's how I work:\n"
                   "1. When you send me a message, I'll first ask if it's a clue for the writing task.\n"
                   "- If you say yes, I'll use it to create content based on that clue.\n"
                   "- If you say no, I'll ask you to provide the complete clue for the writing task.\n"
                   "2. Once I finish creating the content, I'll let you know to check and edit it in the right editing box. After you're done editing, you can click the 'Save and Feed' button to save the final result in my database for future reference.\n"
                   "3. Please note that I won't save any content to the database unless you explicitly instruct me to do so!")
        if language == "zh":
            qprint("无形之刃，最为致命\n\n"
                "我是<影分身-劫>，我可以持续学习并模仿你本人的写作风格，帮你写汇报\n\n"
                "如果你有以下痛点：\n"
                "1.你长期需要写日报/周报，但每次的新信息其实并不多（水一水就能过去的那种）\n"
                "2.给一般的AI写，出来的结果AI感太强，一看就是AI写的，不是你本人的风格\n\n"
                "那么，恭喜你！我是为你量身定制的：\n"
                "1.你只需要用简单的几句话，告诉我本次汇报中的重点信息\n"
                "2.我会从你以往海量的汇报中筛选出最接的内容作为参考，再结合你提供的重点信息，写出一篇和你风格非常接近的汇报\n"
                "3.你可以把最终成品再投喂给我，下次写汇报我也会参考它\n"
                "4.简而言之，我会越来越像你！"
            )

        #为本次项目创建资源目录(如果后续需要保存结果到本地)
        # time_stamp = str(int(time.time()))
        # globals.PROJECT_NAME = project_name = f"project_{time_stamp}"
        # globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
        # os.makedirs(project_path, exist_ok=True)   

        #声明本地自定义tools
        local_tool_boxes = [
            "Zed_tools",
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