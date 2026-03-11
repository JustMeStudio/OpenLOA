# -*- coding: utf-8 -*-
import os
import json
import time
import sys
import asyncio
import contextlib
import importlib
from openai import OpenAI
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters
from mcp.client.sse import sse_client
from agent_utils.utils import qprint
from globals import globals

sys.stdout.reconfigure(encoding="utf-8", newline=None)


class MCPToolSession:
    def __init__(self, command=None, args=None, env=None, sse_url=None):
        self.command = command
        self.args = args
        self.env = env
        self.sse_url = sse_url
        self.session = None
        self.read = None
        self.write = None
        self.client = None
    async def start(self):
        if self.sse_url:
            self.client = sse_client(self.sse_url)
        else:
            self.client = stdio_client(StdioServerParameters(command=self.command, args=self.args, env=self.env))
        self.read, self.write = await self.client.__aenter__()
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        await self.session.initialize()
    async def list_tools(self):
        tools_resp = await self.session.list_tools()
        return tools_resp.tools
    async def call_tool(self, tool_name, input_args):
        return await self.session.call_tool(tool_name, input_args)
    async def close(self):
        with contextlib.suppress(Exception):
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self.client:
                await self.client.__aexit__(None, None, None)

async def load_all_tools_from_MCP_servers(mcp_servers=[]):
    tool_registry = {}
    tools = []
    mcp_sessions = []
    for mcp in mcp_servers:
        await mcp.start()
        mcp_sessions.append(mcp)
        # qprint(f"--------------------正在获取来自{mcp.args}的工具-----------------------------")
        for tool in await mcp.list_tools():
            name = tool.name
            session = mcp.session

            async def tool_func_wrapper(session=session, name=name):
                async def tool_func(**kwargs):
                    return await session.call_tool(name, kwargs)
                return tool_func

            tool_func = await tool_func_wrapper()
            tool_registry[name] = tool_func
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
            # qprint(f"成功注册来自MCP_Server的工具：{name}")
    return tools, tool_registry, mcp_sessions

def load_all_tools_from_local_toolboxes(local_toolboxes=[]):
    mcp_tools,mcp_registry = [],{}
    for toolbox in local_toolboxes:
        # qprint(f"--------------------正在获取来自本地自定义{toolbox}的工具-----------------------------")
        if os.path.exists(f'./local_tools/{toolbox}.py'):
            module_path = f"local_tools.{toolbox}"
        elif os.path.exists(f'./{toolbox}.py'):
            module_path = f"{toolbox}"
        else:
            continue
        tools_module = importlib.import_module(module_path)   # 动态导入模块
        mcp_registry.update(tools_module.tool_registry)
        mcp_tools.extend(tools_module.tools)
        # qprint("成功注册本地自定义工具：", [tool["function"]["name"] for tool in mcp_tools])
    return mcp_tools,mcp_registry

async def chat(model, system_prompt: str = "", tools=[], tool_registry={}):
    client = OpenAI(api_key=model["api_key"], base_url=model["base_url"])
    #发送消息方法定义
    async def send_messages(messages):
        qprint("寒冰写手-艾希：我正在思考......")
        try:
            response = client.chat.completions.create(
                model=model["model"],
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature= 1.0
            )
        except Exception as e:
            response = None
            qprint("寒冰写手-艾希：思考出问题了，Error:", e)
        return response.choices[0].message if response else None
    #对话逻辑
    messages = [{"role": "system", "content": system_prompt}]
    # qprint("============🔧 隐藏命令列表 ============\n",
    #         "\"-clear\" 清除上下文\n",
    #         "\"-read <file_path>\" 读取外部文本作为输入\n",
    #         )
    qprint("下面轮到你说话了，召唤师")
    while True:
        #强制utf-8接收输入内容
        user_input = sys.stdin.buffer.readline().decode('utf-8').strip()
        # -read 触发第三方文本文件输入      
        if user_input.startswith("-read "):
            file_path = user_input.split(maxsplit=1)[1]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                user_input = text.strip()
                # qprint(f"从{file_path}读取到内容作为会话输入：\n",text)
            except FileNotFoundError:
                qprint(f"Error: 文件 '{file_path}' 未找到")
            except IOError as e:
                qprint(f"Error: 无法读取 '{file_path}': {e}")
        # -clear 触发清空上下文
        if user_input == "-clear":
            messages = [{"role": "system", "content": system_prompt}]
            qprint("-----------------------------已成功清除上下文----------------------------------------\n\n")
            continue
        # -exit 退出会话
        if user_input == "-exit":
            break
        messages.append({"role": "user", "content": user_input})
        while True:
            message = await send_messages(messages)
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    # qprint(f"\n寒冰写手-艾希：模型请求调用工具{tool_name}，参数{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    # qprint("寒冰写手-艾希：工具调用结果：\n", result)
                    try:
                        content = json.dumps(result)
                    except TypeError:
                        if hasattr(result, "model_dump"):
                            content = json.dumps(result.model_dump())
                        elif hasattr(result, "dict"):
                            content = json.dumps(result.dict())
                        else:
                            content = json.dumps(str(result))  
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [tool_call.model_dump()]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content
                    })
            else:
                qprint(f"寒冰写手-艾希 工作汇报：{message.content}\n")
                break

#工具化的图奇，供外部Agent用自然语言来调用Ashe工作
async def Ashe_teamwork(user_prompt:str="") -> str :
    workspace_path = globals.ASHE_WORKSPACE_PATH = f"{globals.PROJECT_PATH}/Ashe_workspace"
    submit_path = globals.ASHE_SUBMIT_PATH = f"{workspace_path}/submit"
    os.makedirs(workspace_path, exist_ok=True)
    os.makedirs(submit_path, exist_ok=True) 
    model = {
        # "base_url": "https://api.deepseek.com",
        # "model": "deepseek-chat",
        # # "model": "deepseek-reasoner",
        # "api_key": "sk-76c10143bb404f6a81ac472b99f0d688"
        "api_key":"sk-121a8f5dd9f24398a51351a0b8e3e7d3",
        "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model":"qwen-plus"
    }
    system_prompt = (
        "你是艾希，是一名职业写手，能基于给定的图片/文本资源按用户的要求进行文档创作。\n"
    )
    #声明本地部署MCP Server + SSE远端MCP Server
    mcp_servers = [
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", "."]),   #文件系统控制
    ]
    #声明本地自定义tools
    local_toolboxes = [
        "Ashe_tools"
    ]
    #创建OPEN AI客户端实例
    client = OpenAI(api_key=model["api_key"], base_url=model["base_url"])
    #加载所有MCP工具
    qprint("寒冰写手-艾希：正在血泉购买出门装......")
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
    local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
    mcp_tools.extend(local_mcp_tools)
    mcp_registry.update(local_mcp_registry)
    qprint("寒冰写手-艾希：已加入战场!")
    #发送消息方法定义
    async def send_messages(messages):
        qprint("寒冰写手-艾希：正在等待大模型响应......")
        try:
            response = client.chat.completions.create(
                model=model["model"],
                messages=messages,
                tools=mcp_tools,
                tool_choice="auto",
                temperature= 1.0
            )
        except Exception as e:
            response = None
            qprint("寒冰写手-艾希：大模型服务器返回Error:", e)
        return response.choices[0].message if response else None
    #对话逻辑
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    try:
        while True:
            message = await send_messages(messages)
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    qprint(f"寒冰写手-艾希：大模型请求调用工具：{tool_name} 参数：{tool_args}")
                    result = await mcp_registry[tool_name](**tool_args)
                    qprint("寒冰写手-艾希：工具调用结果：\n", result)
                    try:
                        content = json.dumps(result)
                    except TypeError:
                        if hasattr(result, "model_dump"):
                            content = json.dumps(result.model_dump())
                        elif hasattr(result, "dict"):
                            content = json.dumps(result.dict())
                        else:
                            content = json.dumps(str(result))  
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [tool_call.model_dump()]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content
                    })
            else:
                qprint(f"寒冰写手-艾希 工作汇报：{message.content}\n")
                return message.content
    finally:
        qprint("寒冰写手-艾希：正在尝试结束内部会话进程......")
        for mcp in mcp_sessions:
            await mcp.close()
        qprint("寒冰写手-艾希：内部会话进程已结束......")

# 工具图奇注册表，供外部Agent用自然语言来调用Ashe工作
tool_registry = {
    "Ashe_teamwork":Ashe_teamwork,
}

# 工具图奇注册详情，供外部Agent用自然语言来调用Ashe工作
tools = [
    {
        "type": "function",
        "function": {
            "name": "Ashe_teamwork",
            "description": "艾希（Ashe）是一名职业写手，能基于给定的图片/文本资源按用户的要求进行文档创作。\n",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_prompt": {
                        "type": "string",
                        "description": ("艾希需要帮你完成的任务（自然语言描述）\n"
                                        "1.给出资料文件夹的具体合法路径以便艾希作为创作参考\n"
                                        "2.给出创作要求，包括:\n"
                                        "-创作主题\n"
                                        "-创作风格\n"
                                        "-创作内容长度\n"
                                        "3.如果有其他要求也可以提出"
                                        )
                    }
                },
                "required": ["user_prompt"]
            }
        }
    }  
]



#独立与Ashe对话的主函数
async def main():
    #为本次项目创建资源目录
    time_stamp = str(int(time.time()))
    globals.PROJECT_NAME = project_name = f"project_{time_stamp}"
    globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
    os.makedirs(project_path, exist_ok=True)
    workspace_path = globals.ASHE_WORKSPACE_PATH = f"{globals.PROJECT_PATH}/Ashe_workspace"
    submit_path = globals.ASHE_SUBMIT_PATH = f"{workspace_path}/submit"
    os.makedirs(workspace_path, exist_ok=True)
    os.makedirs(submit_path, exist_ok=True) 
    #模型设置
    model = {
        # "base_url": "https://api.deepseek.com",
        # "model": "deepseek-chat",
        # # "model": "deepseek-reasoner",
        # "api_key": "sk-76c10143bb404f6a81ac472b99f0d688"

        # "api_key":"sk-121a8f5dd9f24398a51351a0b8e3e7d3",  #私
        "api_key":"sk-fbe14e00e5b544c792039d72b250e0fa",
        "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model":"qwen-plus-2025-01-25"
    }
    system_prompt = (
        "你是艾希，是一名职业写手，擅长根据用户要求输出高质量的文档作品\n"
        "你的创作应按照如下流程进行：\n"
        "1.如果用户提供或者提及了某些资料文件，你**必须**先使用load_external_materials读取相应资料文件！非常重要！\n"
        "2.根据读取到的用户资料，判断是否需要额外的图文资料补充。如果你需要额外的图文，调用图奇帮忙搜集资料，它返回的资料会自动存储在RAM里\n"
        "3.最后，调用creat_markdown_content_and_save开始创作\n"
    )
    #声明本地部署MCP Server + SSE远端MCP Server
    mcp_servers = [
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", ".", "~/Desktop"]),   #文件系统控制
            # MCPToolSession("npx", ["-y", "@executeautomation/playwright-mcp-server"]),    #浏览器自动化  
            # MCPToolSession("uvx", ["--index-url","https://pypi.tuna.tsinghua.edu.cn/simple","mcp-pandoc"]),    #标记文本格式互转                    
            # MCPToolSession("npx", ["@apify/mcp-server-rag-web-browser"], {"APIFY_TOKEN": "apify_api_ZGrscn4a5AV6hv3ndmaPiI46tTU0cC0K5sMF"}),   #RAG检索
            # MCPToolSession("npx", ["-y", "./local_servers/12306-mcp"]),   #火车票查询
            # MCPToolSession(sse_url="https://mcp-youxuan.baidu.com/mcp/sse?key=77316c70596936436750557644675075b6ba0e9ffca7ff32164725bc84fd9a53"),   #百度优选MCP(SSE)
    ]
    #声明本地自定义tools
    local_toolboxes = [
        "Ashe_tools",
        "Twitch",
    ]
    #加载所有MCP工具
    qprint("寒冰写手-艾希：【世间万物，皆系于一箭之上】正在血泉购买出门装......")
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
    local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
    mcp_tools.extend(local_mcp_tools)
    mcp_registry.update(local_mcp_registry)
    qprint("寒冰写手-艾希：已加入战场!")
    #开始对话
    try:
        await chat(model, system_prompt, mcp_tools, mcp_registry)
    finally:
        qprint("收拾东西，准备开溜......")
        for mcp in mcp_sessions:
            await mcp.close()
        qprint("溜了溜了，溜溜球......")


if __name__ == "__main__":
    asyncio.run(main())