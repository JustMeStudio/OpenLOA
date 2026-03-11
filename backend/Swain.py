import os
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
from globals import globals

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
        # print(f"--------------------⏳ 正在获取来自{mcp.args}的工具-----------------------------")
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
            # print(f"✅ 成功注册来自MCP_Server的工具：{name}")
    return tools, tool_registry, mcp_sessions

def load_all_tools_from_local_toolboxes(local_toolboxes=[]):
    mcp_tools,mcp_registry = [],{}
    for toolbox in local_toolboxes:
        # print(f"--------------------⏳ 正在获取来自本地自定义{toolbox}的工具-----------------------------")
        if os.path.exists(f'./local_tools/{toolbox}.py'):
            module_path = f"local_tools.{toolbox}"
        elif os.path.exists(f'./{toolbox}.py'):
            module_path = f"{toolbox}"
        else:
            continue
        tools_module = importlib.import_module(module_path)   # 动态导入模块
        mcp_registry.update(tools_module.tool_registry)
        mcp_tools.extend(tools_module.tools)
        # print("✅ 成功注册本地自定义工具：", [tool["function"]["name"] for tool in mcp_tools])
    return mcp_tools,mcp_registry

async def chat(model, system_prompt: str = "", tools=[], tool_registry={}):
    client = OpenAI(api_key=model["api_key"], base_url=model["base_url"])
    #发送消息方法定义
    async def send_messages(messages):
        print("⏳ 智能体统领-斯维因：正在等待大模型服务器响应......")
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
            print("智能体统领-斯维因：大模型服务器返回Error:", e)
        return response.choices[0].message if response else None
    #对话逻辑
    messages = [{"role": "system", "content": system_prompt}]
    print("============🔧 隐藏命令列表 ============\n",
            "\"-clear\" 清除上下文\n",
            "\"-read <file_path>\" 读取外部文本作为输入\n",
            )
    while True:
        user_input = input("📝 请输入会话内容：")
        # -read 触发第三方文本文件输入      
        if user_input.startswith("-read "):
            file_path = user_input.split(maxsplit=1)[1]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                user_input = text.strip()
                print(f"从{file_path}读取到内容作为会话输入：\n",text)
            except FileNotFoundError:
                print(f"Error: 文件 '{file_path}' 未找到")
            except IOError as e:
                print(f"Error: 无法读取 '{file_path}': {e}")
        # -clear 触发清空上下文
        if user_input == "-clear":
            messages = [{"role": "system", "content": system_prompt}]
            print("-----------------------------✅ 已成功清除上下文----------------------------------------\n\n")
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
                    print(f"📦 智能体统领-斯维因：请求调用工具{tool_name}，参数{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    print("📦 智能体统领-斯维因：工具调用结果：\n", result)
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
                print(f"💬 智能体统领-斯维因：{message.content}\n")
                break

#独立与Swain对话的主函数
async def main():
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
        "你是斯维因（Swain），一个智能体统领，可以调度你手下的其他智能体协作完成各种复杂任务"
    )
    #声明本地部署MCP Server + SSE远端MCP Server
    mcp_servers = [
            MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", ".", "~/Desktop"]),   #文件系统控制
    ]
    #声明本地自定义tools
    local_toolboxes = [
        "Twitch",
        "Ashe",
        "Ryze"
    ]
    #加载所有MCP工具
    print("⏳ 智能体统领-斯维因：正在血泉购买出门装......")
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
    local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
    mcp_tools.extend(local_mcp_tools)
    mcp_registry.update(local_mcp_registry)
    print("✅ 智能体统领-斯维因：已加入战场!")
    #开始对话
    try:
        await chat(model, system_prompt, mcp_tools, mcp_registry)
    finally:
        print("⏳智能体统领-斯维因：正在尝试结束会话进程......")
        for mcp in mcp_sessions:
            await mcp.close()
        print("✅智能体统领-斯维因：会话进程已结束......")


if __name__ == "__main__":
    asyncio.run(main())