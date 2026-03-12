# -*- coding: utf-8 -*-
import os
import sys
import json 
import time 
import asyncio
from utils.com import qprint, chat
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers
from utils.config import load_model_config
from globals import globals
# self-defined tools import
from tools import Zed_tools

# 防止前端输出乱码
sys.stdout.reconfigure(encoding="utf-8", newline=None)

#--------------------------API KEY config-------------------------------------------
agent_model_config = load_model_config("Zed_agent_model_config")
# 测试打印一下
if agent_model_config:
    print(f"成功加载配置，正在使用模型: {agent_model_config.get('model')}")

#-----------------------system prompt config-------------------------------------
system_prompt = (
    "你是劫（Zed），一个仿风格写手，能像原作者的分身一般复刻他的写作风格完成写作任务\n"
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
        local_tools, local_tools_registry = Zed_tools.tools, Zed_tools.tool_registry
        #声明本地部署MCP Server + SSE远端MCP Server
        mcp_servers = [
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