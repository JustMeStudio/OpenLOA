# -*- coding: utf-8 -*-
import sys
import json
import time
from openai import OpenAI

# 将消息输出封装成一个函数，增加输出前后的停顿，前端正确分割消息
def qprint(*args, **kwargs):
    time.sleep(0.1)
    print(*args, **kwargs)
    time.sleep(0.1)


# 前端与agent交互式对话函数，支持工具调用和上下文管理
async def chat(model_config, system_prompt: str = "", tools=[], tool_registry={}):
    client = OpenAI(api_key=model_config["api_key"], base_url=model_config["base_url"])
    # 发送消息方法定义
    async def send_messages(messages):
        qprint("\n🔍 AI：正在脑暴中，请稍候...")
        try:
            response = client.chat.completions.create(
                model=model_config["model"],
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=1.0
            )
        except Exception as e:
            response = None
            qprint(f"❌ AI：糟糕，思考回路短路了！Error: {e}")
        return response.choices[0].message if response else None
    # 对话逻辑
    messages = [{"role": "system", "content": system_prompt}]
    qprint("\n" + "="*20 + " 🛠️ 隐藏命令列表 " + "="*20)
    qprint(" 📝 `-clear`          | 清除记忆上下文")
    qprint(" 📂 `-read <path>`    | 注入外部文本文件")
    qprint(" 🚪 `-exit`           | 结束本次召唤")
    qprint("="*55 + "\n")
    while True:
        qprint("✨ 召唤师，请下达指令：")
        # 强制utf-8接收输入内容
        user_input = sys.stdin.buffer.readline().decode('utf-8').strip()
        # -read 触发第三方文本文件输入      
        if user_input.startswith("-read "):
            file_path = user_input.split(maxsplit=1)[1]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                user_input = text.strip()
                qprint(f"📖 系统：已成功解析文件内容 [ {file_path} ]")
            except FileNotFoundError:
                qprint(f"🚫 系统：找不到文件 '{file_path}'，请检查路径是否正确。")
                continue
            except IOError as e:
                qprint(f"⚠️ 系统：读取文件失败: {e}")
                continue
        # -clear 触发清空上下文
        if user_input == "-clear":
            messages = [{"role": "system", "content": system_prompt}]
            qprint("🧹 系统：记忆已重置，我们重新开始吧！\n" + "-"*50 + "\n")
            continue
        # -exit 退出会话
        if user_input == "-exit":
            qprint("👋 系统：再见，召唤师！期待下次合作。")
            break
        if not user_input: continue # 防止空输入
        messages.append({"role": "user", "content": user_input})
        while True:
            message = await send_messages(messages)
            if not message: break
            # 检查是否有工具调用
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    qprint(f"🛠️  AI：启动插件 [ {tool_name} ]")
                    qprint(f"📦 参数：{tool_args}")
                    result = await tool_registry[tool_name](**tool_args)
                    qprint(f"✅ 结果：{result}")
                    # 结果序列化处理
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
                # 最终文本回答
                qprint(f"\n🤖 AI：{message.content}\n")
                messages.append({
                    "role": "assistant",
                    "content": message.content
                })
                break


# get text response from LLM API, with retry mechanism for network issues
def request_LLM_api(model_config:dict, prompt:str, system_prompt:str="", response_format=None):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    client = OpenAI(api_key=model_config["api_key"], base_url=model_config["base_url"])
    # 正常识别流程
    for i in range(3):
        try:
            # 这里的 qprint 增加了动态感
            qprint(f"📡 正在建立精神连接 [模型: {model_config['model']}] ...")
            completion = client.chat.completions.create(
                model=model_config["model"],
                messages=messages,
                response_format=response_format,
                temperature=1.0
            )
            content = completion.choices[0].message.content
            qprint("✅ 接收到远端信号，解析成功。")
            return content
        except Exception as e:
            # 失败时的重试提醒，加入倒计时或次数感
            retry_icons = ["⏳", "🔄", "⚠️"]
            qprint(f"{retry_icons[i]} 信号波动中... 正在进行第 {i+1} 次频率重调")
            qprint(f"   💡 错误报告: {str(e)}")
            # 如果是最后一次尝试失败，就不再打印“重试中”
            if i < 2:
                continue
    qprint("\n" + "!"*10 + " 🛑 传输彻底中断 " + "!"*10)
    qprint("❌ 很遗憾，召唤师，大模型未能在规定时间内回应你的呼唤。")
    return None