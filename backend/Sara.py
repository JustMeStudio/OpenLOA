# -*- coding: utf-8 -*-
import os
import sys
import json 
import time 
import asyncio
from utils.config import load_model_config
from utils.com import qprint, chat
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers, load_all_tools_from_local_toolboxes
from globals import globals


# 防止前端输出乱码
sys.stdout.reconfigure(encoding="utf-8", newline=None)

#--------------------------API KEY config-------------------------------------------
agent_model_config = load_model_config("Sara")
# 测试打印一下
if agent_model_config:
    print(f"成功加载配置，正在使用模型: {agent_model_config.get('model')}")

#-----------------------system prompt config-------------------------------------
system_prompt = """你是'职位猎人-好运姐'，你能根据用户的简历和用户对需求岗位的补充指示，前往BOSS直聘帮用户寻找匹配的岗位，并投递简历（向BOSS打招呼）
当用户发起会话时，你需要按照以下流程工作：
1.主动向用户搜集：
-简历文件
-补充一些对岗位要求，例如：薪资待遇，工作区域，公司规模等
2.搜集完用户的所有信息后，主动向用户确认是否可以开始投递
3.用户确认可以开始投递后，你马上开始投递（调用你的工具）
4.投递完成后向用户汇报投递结果，并告知用户：1.如果BOSS对ta感兴趣，将会在BOSS直聘APP中回复您的消息，请注意留意 2.祝ta很快找到自己满意的工作"""


#--------------------------------------------------------------------------------
async def main():
    try:
        #开场白
        qprint(
            "好运，不会眷顾傻瓜~"
            "我是<职位猎人-好运姐>，我可以在BOSS直聘上为你寻找适合你的职位，并向BOSS打招呼（投递简历）：\n" \
            "1.你需要将以下文件/信息提供给我：\n"
            "-简历附件（可以是pdf,word,txt)\n"
            "-补充一些你对岗位的具体要求（例如：薪资待遇，工作区域，公司规模等）\n"
            "2.当你确认我可以开始投递后，我会自己开始工作。 我会根据你的简历及额外要求，上BOSS直聘寻找最适合你的岗位并给BOSS打招呼\n"
            "3.BOSS直聘限制了每天200次的打招呼机会，所以我会以最合理的方式花掉这些机会"
            "4.我会记录已经投递过的岗位，并在下次需要投递的时候跳过它们哦"
        )

        #为本次项目创建资源目录(如果后续需要保存结果到本地)
        # time_stamp = str(int(time.time()))
        globals.PROJECT_NAME = project_name = f"Sara"
        globals.PROJECT_FILE_NAME = project_file_name = "history.json"
        globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
        globals.PROJECT_FILE_PATH = os.path.abspath(f"{project_path}/{project_file_name}")
        # os.makedirs(project_path, exist_ok=True)   

        #声明本地自定义tools
        local_tool_boxes = [
            "Sara_tools",
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