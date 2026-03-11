import os
import json
import time
import random
import asyncio
import contextlib
import importlib
from openai import OpenAI
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters
from mcp.client.sse import sse_client
from agent_utils.utils import update_metadata_file
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
        print("⏳ 爬虫之源-图奇：正在等待大模型服务器响应......")
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
            print("爬虫之源-图奇：大模型服务器返回Error:", e)
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
                    print(f"\n📦 爬虫之源-图奇：模型请求调用工具{tool_name}，参数{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    print("📦 爬虫之源-图奇：工具调用结果：\n", result)
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
                print(f"💬 爬虫之源-图奇 工作汇报：{message.content}\n")
                break

#工具化的图奇，供外部Agent用自然语言来调用Twitch工作
async def Twitch_teamwork(user_prompt:str="") -> str :
    workspace_path = globals.TWITCH_WORKSPACE_PATH = f"{globals.PROJECT_PATH}/Twitch_workspace"
    submit_path = globals.TWITCH_SUBMIT_PATH = f"{workspace_path}/submit"
    globals.TWITHCH_TASK = user_prompt
    os.makedirs(workspace_path, exist_ok=True)
    os.makedirs(submit_path, exist_ok=True)  
    #定义参数配置
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
        "你是图奇，是一名网络资源抓取专家，擅长从网络上抓取文本/图片资源，并下载到本地。\n"
        "1.首先抓取用户提供的关键词的相关文本信息，再根据文本中的关键内容逐项抓图片。\n"
        "-正确示例：用户让你抓取一些关于'潜江传统美食'的文本和图片，你从抓取到的文本中发现了'油焖大虾'和'锅盔'等具体美食，后续你需要分别去下载一些以'油焖大虾''锅盔'等具体美食名为关键词的图片\n"
        "-错误示例1：直接以'潜江传统美食'为关键词搜索图片\n"
        "-错误示例2：以'油焖大虾，锅盔，油条，鱼糕'整句为一个关键词搜索图片\n"
        "2.完成任务后，你需要做一个简短汇报：\n"
        "-采集到了哪些关键词的文本？\n"
        "-采集到了哪些关键词的图片，分别多少张？\n"
        "-采集过程中遇到什么困难？\n"
        "-除上述信息外，你的汇报中禁止添加任何内容！\n"
    )
    #声明本地部署MCP Server + SSE远端MCP Server
    mcp_servers = [
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", "./Twitch_workspace"]),   #文件系统控制
    ]
    #声明本地自定义tools
    local_toolboxes = [
        "Twitch_tools"
    ]
    #创建OPEN AI客户端实例
    client = OpenAI(api_key=model["api_key"], base_url=model["base_url"])
    #加载所有MCP工具
    print("⏳- 爬虫之源-图奇：正在血泉购买出门装......")
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
    local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
    mcp_tools.extend(local_mcp_tools)
    mcp_registry.update(local_mcp_registry)
    print("✅ 爬虫之源-图奇：已加入战场!")
    #发送消息方法定义
    async def send_messages(messages):
        print("⏳ 爬虫之源-图奇：正在等待大模型响应......")
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
            print("爬虫之源-图奇：大模型服务器返回Error:", e)
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
                    print(f"📦爬虫之源-图奇：大模型请求调用工具：{tool_name} 参数：{tool_args}")
                    result = await mcp_registry[tool_name](**tool_args)
                    print("📦 爬虫之源-图奇：工具调用结果：\n", result)
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
                #将所有获取到的资源的metadata写入SUBMIT_PATH下的metadata.json
                update_metadata_file(f"{submit_path}/metadata.json",random.shuffle(globals.TWITCH_SUBMIT_METADATA))                   
                report = (
                    f"{message.content}\n"
                    " 抓取到的所有资料已存入RAM，可供随时调用"
                    # f"下载到的所有资料已记录在{submit_path}/metadata.json"
                    # f"下载到的所有相关资源已被保存在{submit_path}，metadata保存在{submit_path}/metadata.json"
                )
                # print(f"💬 爬虫之源-图奇 工作汇报：\n{report}")
                return report
    finally:
        print("⏳ 爬虫之源-图奇：正在尝试结束内部会话进程......")
        #关闭所有浏览器driver实例
        for name, driver in list(globals.WEB_DRIVERS.items()):
            try:
                driver.quit()   # 彻底结束 session，而非仅关闭页面窗口
            except Exception as e:
                print(f"爬虫之源-图奇：关闭浏览器{name}失败: {e}")
        #终止所有MCP Server会话进程
        for mcp in mcp_sessions:
            await mcp.close()
        print("✅ 爬虫之源-图奇：内部会话进程已结束......")

# 工具图奇注册表，供外部Agent用自然语言来调用Twitch工作
tool_registry = {
    "Twitch_teamwork":Twitch_teamwork,
}

# 工具图奇注册详情，供外部Agent用自然语言来调用Twitch工作
tools = [
    {
        "type": "function",
        "function": {
            "name": "Twitch_teamwork",
            "description": "图奇（Twitch）是一名精通网络资源抓取的AI智能体，擅长从网络上抓取你需要的文本/图片并下载到本地，你需要通过**自然语言**命令他替你完成任务\n",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_prompt": {
                        "type": "string",
                        "description": ("图奇需要帮你完成的任务（自然语言描述）\n"
                                        "你可以向图奇指定：\n"
                                        "1.你需要的图片/文本关于哪些内容\n"
                                        "2.每种内容的图片/文本的需求数量各有多少\n"
                                        "3.图片的分辨率（像素/宽/高）有什么要求（一般不建议要求分辨率，避免下载不到图片）\n"
                                        "除此以外，你的其他要求他也会尽量满足")
                    }
                },
                "required": ["user_prompt"]
            }
        }
    }  
]



#独立与Twitch对话的主函数
async def main():
    #为本次项目创建资源目录
    time_stamp = str(int(time.time()))
    globals.PROJECT_NAME = project_name = f"project_{time_stamp}"
    globals.PROJECT_PATH = project_path = os.path.abspath(f"./projects/{project_name}")
    os.makedirs(project_path, exist_ok=True)
    workspace_path = globals.TWITCH_WORKSPACE_PATH = f"{globals.PROJECT_PATH}/Twitch_workspace"
    submit_path = globals.TWITCH_SUBMIT_PATH = f"{workspace_path}/submit"
    os.makedirs(workspace_path, exist_ok=True)
    os.makedirs(submit_path, exist_ok=True) 
    #模型设置
    model = {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        # "model": "deepseek-reasoner",
        "api_key": "sk-76c10143bb404f6a81ac472b99f0d688"
    }
    system_prompt = (
        "你是图奇，是一名网络资源抓取专家，擅长从网络上抓取文本/图片资源，并下载到本地。\n"
        "1.如果用户同时要求抓取文本和图片，你必须先抓文本，再根据文本中的关键内容针对性地单独抓图片。\n"
        "-示例：用户让你抓取一些关于'潜江传统美食'的文本和图片，你从抓取到的文本中发现了'油焖大虾'和'锅盔'等具体美食，后续你需要分别去下载一些以'油焖大虾''锅盔'等具体美食名为关键词的图片，而不是去抓取以'潜江传统美食'为关键词的图片\n"
        "2.完成任务后，你需要做一个简短汇报：\n"
        "-采集到了哪些关键词的文本？\n"
        "-采集到了哪些关键词的图片，分别多少张？\n"
        "-采集过程中遇到什么困难？\n"
        "-除上述信息外，你的汇报中禁止添加任何内容！\n"
    )
    #声明本地部署MCP Server + SSE远端MCP Server
    mcp_servers = [
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", "./Twitch_workspace"]),   #文件系统控制
            # MCPToolSession("npx", ["-y", "@executeautomation/playwright-mcp-server"]),    #浏览器自动化  
            # MCPToolSession("uvx", ["--index-url","https://pypi.tuna.tsinghua.edu.cn/simple","mcp-pandoc"]),    #标记文本格式互转                    
            # MCPToolSession("npx", ["@apify/mcp-server-rag-web-browser"], {"APIFY_TOKEN": "apify_api_ZGrscn4a5AV6hv3ndmaPiI46tTU0cC0K5sMF"}),   #RAG检索
            # MCPToolSession("npx", ["-y", "./local_servers/12306-mcp"]),   #火车票查询
            # MCPToolSession(sse_url="https://mcp-youxuan.baidu.com/mcp/sse?key=77316c70596936436750557644675075b6ba0e9ffca7ff32164725bc84fd9a53"),   #百度优选MCP(SSE)
    ]
    #声明本地自定义tools
    local_toolboxes = [
        "Twitch_tools"
    ]
    #加载所有MCP工具
    print("⏳- 爬虫之源-图奇：正在血泉购买出门装......")
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)   
    local_mcp_tools, local_mcp_registry = load_all_tools_from_local_toolboxes(local_toolboxes)
    mcp_tools.extend(local_mcp_tools)
    mcp_registry.update(local_mcp_registry)
    print("✅ 爬虫之源-图奇：已加入战场!")
    #开始对话
    try:
        await chat(model, system_prompt, mcp_tools, mcp_registry)
    finally:
        print("⏳ 正在尝试结束会话进程......")
        for mcp in mcp_sessions:
            await mcp.close()
        print("✅ 会话进程已结束......")


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(Twitch_teamwork("帮我在下载10张哈士奇图片和10张金毛的图片"))