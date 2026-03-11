# -*- coding: utf-8 -*-
import sys
import json
import time
from openai import OpenAI

def qprint(*args, **kwargs):
    time.sleep(0.1)
    print(*args, **kwargs)
    time.sleep(0.1)

async def chat(model_config, system_prompt: str = "", tools=[], tool_registry={}):
    client = OpenAI(api_key=model_config["api_key"], base_url=model_config["base_url"])
    #发送消息方法定义
    async def send_messages(messages):
        qprint("AI：我正在思考......")
        try:
            response = client.chat.completions.create(
                model=model_config["model"],
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature= 1.0
            )
        except Exception as e:
            response = None
            qprint("AI：思考出故障了，Error:", e)
        return response.choices[0].message if response else None
    #对话逻辑
    messages = [{"role": "system", "content": system_prompt}]
    qprint("============隐藏命令列表 ============\n",
            "\"-clear\" 清除上下文\n",
            "\"-read <file_path>\" 读取外部文本作为输入\n",
        )
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
                    qprint(f"AI：我需要使用工具{tool_name}，参数{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    qprint("AI：工具使用结果：\n", result)
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
                messages.append({
                    "role": "assistant",
                    "content": message.content
                })
                break



def request_LLM_api(model_config:dict, prompt:str, system_prompt:str=""):
    messages = [{"role": "system", "content":system_prompt}]
    messages.append({"role": "user", "content": prompt})
    client = OpenAI(api_key= model_config["api_key"], base_url= model_config["base_url"],)
    #正常识别流程
    for i in range(3):
        try:
            qprint("正在请求大模型......")
            completion = client.chat.completions.create(
                model= model_config["model"],
                messages= messages,
            )
            content = completion.choices[0].message.content
            return content
        except Exception as e:
            qprint (f"请求大模型过程中到网络问题，第{i+1}次重试中......", str(e))
    qprint("很遗憾，获取大模型返回结果失败~")
    return None