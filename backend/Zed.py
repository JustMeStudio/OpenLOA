# -*- coding: utf-8 -*-
import os
import sys
import json 
import time 
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
            # qprint(f"✅ 成功注册来自MCP_Server的工具：{name}")
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
        qprint("影分身-劫：我正在思考......")
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
            qprint("影分身-劫：思考出故障了，Error:", e)
        return response.choices[0].message if response else None
    #对话逻辑
    messages = [{"role": "system", "content": system_prompt}]
    # qprint("============隐藏命令列表 ============\n",
    #         "\"-clear\" 清除上下文\n",
    #         "\"-read <file_path>\" 读取外部文本作为输入\n",
    #     )
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
                    # qprint(f"影分身-劫：我需要使用工具{tool_name}，参数{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    # qprint("影分身-劫：工具使用结果：\n", result)
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
                qprint(f"影分身-劫：{message.content}\n")
                break

#独立与Zed对话的主函数
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
        #为本次项目创建资源目录
        time_stamp = str(int(time.time()))
        globals.PROJECT_NAME = project_name = f"project_{time_stamp}"
        globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
        globals.SUBMIT_PATH = submit_path = os.path.abspath(f"{project_path}/submit") 
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(submit_path, exist_ok=True)    
        #模型设置
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
            "你是劫（Zed），一个仿风格写手，能像原作者的分身一般复刻他的写作风格完成写作任务\n"
            "你的工作流程：\n"
            "1.当用户发来一句话时，首先询问客户这是不是本次写作的线索\n"
            "-如果用户回答是，就调用写作工具根据该线索写作\n"
            "-如果用户回答不是，就询问客户本次写作的完整线索是什么\n"
            "2.当你完成创作后，告诉用户在右边的编辑框中查看并编辑你的创作结果，编辑完以后可以点击'保存并投喂'按钮将最终结果保存在我的数据库，方便下次创作时参考\n"
            "3.除非你收到用户指令将创作内容录入到数据库，否则任何时候不要擅自录入！"
        )
        #声明本地部署MCP Server + SSE远端MCP Server
        mcp_servers = [
        ]
        #声明本地自定义tools
        local_toolboxes = [
            "Zed_tools",
        ]
        #加载所有MCP工具
        # qprint("影分身-劫：【无形之刃，最为致命】我正在血泉购买出门装......")
        mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
        local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
        mcp_tools.extend(local_mcp_tools)
        mcp_registry.update(local_mcp_registry)
        # qprint("影分身-劫：我已加入战场!")
        #开始对话
        try:
            await chat(model, system_prompt, mcp_tools, mcp_registry)
        finally:
            qprint("影分身-劫：正在尝试结束会话进程......")
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("影分身-劫：会话进程已结束......")
    except Exception as e:
        qprint(f"后端启动失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())