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
from utils.com import qprint
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
        qprint("职位猎人-好运姐：我正在思考......")
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
            qprint("职位猎人-好运姐：思考出故障了，Error:", e)
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
        # print("后端收到：",user_input)
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
            qprint("已成功清除上下文\n\n")
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
                    # qprint(f"职位猎人-好运姐：我需要使用工具{tool_name}，参数{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    # qprint("职位猎人-好运姐：工具使用结果：\n", result)
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
                qprint(f"职位猎人-好运姐：{message.content}\n")
                break

#独立与Zed对话的主函数
async def main():
    try:
        #开场白
        qprint("好运，不会眷顾傻瓜~"
               "我是<职位猎人-好运姐>，我可以在BOSS直聘上为你寻找适合你的职位，并向BOSS打招呼（投递简历）：\n" \
               "1.你需要将以下文件/信息提供给我：\n"
               "-简历附件（可以是pdf,word,txt)\n"
               "-补充一些你对岗位的具体要求（例如：薪资待遇，工作区域，公司规模等）\n"
               "2.当你确认我可以开始投递后，我会自己开始工作。 我会根据你的简历及额外要求，上BOSS直聘寻找最适合你的岗位并给BOSS打招呼\n"
               "3.BOSS直聘限制了每天200次的打招呼机会，所以我会以最合理的方式花掉这些机会"
               "4.我会记录已经投递过的岗位，并在下次需要投递的时候跳过它们哦"
        )
        #投递记录读取展示
        qprint(r"./backend/projects/cache/Sara_cache.json")
        #为本次项目创建资源目录
        time_stamp = str(int(time.time()))
        globals.PROJECT_NAME = project_name = f"project_{time_stamp}"
        globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
        globals.SUBMIT_PATH = submit_path = os.path.abspath(f"{project_path}/submit") 
        # os.makedirs(project_path, exist_ok=True)
        # os.makedirs(submit_path, exist_ok=True)    
        #模型设置
        model = {
            # "base_url": "https://api.deepseek.com",
            # "model": "deepseek-chat",
            # # "model": "deepseek-reasoner",
            # "api_key": "sk-76c10143bb404f6a81ac472b99f0d688"
            "api_key":"sk-121a8f5dd9f24398a51351a0b8e3e7d3",
            "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model":"qwen-flash"
        }
        system_prompt = (
            "你是'职位猎人-好运姐'，你能根据用户的简历和用户对需求岗位的补充指示，前往BOSS直聘帮用户寻找匹配的岗位，并投递简历（向BOSS打招呼）\n"
            "当用户发起会话时，你需要按照以下流程工作：\n"
            "1.主动向用户搜集：\n"
            "-简历文件\n"
            "-补充一些对岗位要求，例如：薪资待遇，工作区域，公司规模等\n"
            "2.搜集完用户的所有信息后，主动向用户确认是否可以开始投递\n"
            "3.用户确认可以开始投递后，你马上开始投递（调用你的工具）\n"
            "4.投递完成后向用户汇报投递结果，并告知用户：1.如果BOSS对ta感兴趣，将会在BOSS直聘APP中回复您的消息，请注意留意 2.祝ta很快找到自己满意的工作"
        )
        #声明本地部署MCP Server + SSE远端MCP Server
        mcp_servers = [
        ]
        #声明本地自定义tools
        local_toolboxes = [
            "Sara_tools",
        ]
        #加载所有MCP工具
        # qprint("职位猎人-好运姐：【好运，不会眷顾傻瓜】我正在血泉购买出门装......")
        mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
        local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
        mcp_tools.extend(local_mcp_tools)
        mcp_registry.update(local_mcp_registry)
        # qprint("职位猎人-好运姐：我已加入战场!")
        #开始对话
        try:
            await chat(model, system_prompt, mcp_tools, mcp_registry)
        finally:
            qprint("职位猎人-好运姐：正在尝试结束会话进程......")
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("职位猎人-好运姐：会话进程已结束......")
    except Exception as e:
        qprint(f"后端启动失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())