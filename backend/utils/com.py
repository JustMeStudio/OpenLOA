# -*- coding: utf-8 -*-
import sys
import json
import time
from openai import OpenAI
from utils.config import load_user_settings

# I18n dictionary for multilingual support in terminal interactions
T = {
    "zh": {
        "brainstorm": "🔍 AI：正在脑暴中，请稍候...",
        "error": "❌ AI：糟糕，思考回路短路了！",
        "cmd_title": " 🛠️ 隐藏命令列表 ",
        "commands": {
            "📝 -clear": "清除记忆上下文",
            "📂 -read <path>": "注入外部文本文件",
            "🚪 -exit": "结束本次召唤"
        },
        "prompt": "✨ 召唤师，请下达指令：",
        "read_ok": "📖 系统：已成功解析文件内容",
        "read_err": "🚫 系统：读取文件失败",
        "clear_ok": "🧹 系统：记忆已重置，我们重新开始吧！",
        "exit": "👋 系统：再见，召唤师！期待下次合作。",
        "tool_start": "🛠️  AI：启动插件",
        "tool_args": "📦 参数：",
        "tool_res": "✅ 结果：",
        "api_connect": "📡 正在建立精神连接",
        "api_success": "✅ 接收到远端信号，解析成功。",
        "api_retry_prefix": "信号波动中... 正在进行第",
        "api_retry_suffix": "次频率重调",
        "api_err_report": "错误报告",
        "api_fail_title": "传输彻底中断",
        "api_fail_msg": "很遗憾，召唤师，大模型未能在规定时间内回应你的呼唤。",
        "retry_icons": ["⏳", "🔄", "⚠️"],
    },
    "en": {
        "brainstorm": "🔍 AI: Brainstorming, please wait...",
        "error": "❌ AI: Circuit shorted!",
        "cmd_title": " 🛠️  Hidden Commands ",
        "commands": {
            "📝 -clear": "Clear context",
            "📂 -read <path>": "Inject local file",
            "🚪 -exit": "End session"
        },
        "prompt": "✨ Summoner, enter your command:",
        "read_ok": "📖 System: File parsed successfully",
        "read_err": "🚫 System: Failed to read file",
        "clear_ok": "🧹 System: Memory reset!",
        "exit": "👋 System: Goodbye!",
        "tool_start": "🛠️  AI: Tool call started",
        "tool_args": "📦 Args:",
        "tool_res": "✅ Result:",
        "api_connect": "📡 Establishing neural link",
        "api_success": "✅ Remote signal received and parsed.",
        "api_retry_prefix": "Signal fluctuating... Re-tuning frequency #",
        "api_retry_suffix": "",
        "api_err_report": "Error Report",
        "api_fail_title": "Transmission Terminated",
        "api_fail_msg": "Alas, Summoner, the LLM failed to answer your call in time.",
        "retry_icons": ["⏳", "🔄", "⚠️"],
    }
}

# load user settings for language preference
user_settings = load_user_settings()
language = user_settings.get("language", "en")

# select the appropriate language dictionary, default to English if not found
L = T.get(language, T["en"])

# enhanced print function with delay for better UX in terminal interactions
def qprint(*args, **kwargs):
    time.sleep(0.1)
    print(*args, **kwargs)
    time.sleep(0.1)

# asynchronous chat function that supports tool calls and dynamic response handling
async def chat(model_config, system_prompt: str = "", tools=[], tool_registry={}):
    client = OpenAI(api_key=model_config["api_key"], base_url=model_config["base_url"])
    async def send_messages(messages):
        qprint(f"\n{L['brainstorm']}")
        try:
            response = client.chat.completions.create(
                model=model_config["model"],
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=1.0
            )
        except Exception as e:
            qprint(f"{L['error']} Error: {e}")
            return None
        return response.choices[0].message if response else None
    messages = [{"role": "system", "content": system_prompt}]
    # --- Generate Help List ---
    qprint("\n" + "="*20 + L["cmd_title"] + "="*20)
    for cmd, desc in L["commands"].items():
        qprint(f" {cmd:<18} | {desc}")
    qprint("="*55 + "\n")
    while True:
        qprint(L["prompt"])
        user_input = sys.stdin.buffer.readline().decode('utf-8').strip()
        if not user_input: continue
        # ---System Commands ---
        if user_input.startswith("-read "):
            file_path = user_input.split(maxsplit=1)[1]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    user_input = f.read().strip()
                qprint(f"{L['read_ok']} [ {file_path} ]")
            except Exception as e:
                qprint(f"{L['read_err']}: {e}")
                continue
        elif user_input == "-clear":
            messages = [{"role": "system", "content": system_prompt}]
            qprint(f"{L['clear_ok']}\n" + "-"*50 + "\n")
            continue
        elif user_input == "-exit":
            qprint(L["exit"])
            break
        messages.append({"role": "user", "content": user_input})
        while True:
            message = await send_messages(messages)
            if not message: break
            qprint(f"\n🤖 AI：{message.content}\n")
            messages.append({"role": "assistant", "content": message.content})
            if hasattr(message, "tool_calls") and message.tool_calls:     
                for tool_call in message.tool_calls:
                    t_name = tool_call.function.name
                    t_args = json.loads(tool_call.function.arguments)
                    qprint(f"{L['tool_start']} [ {t_name} ]")
                    qprint(f"{L['tool_args']} {t_args}")
                    result = await tool_registry[t_name](**t_args)
                    qprint(f"{L['tool_res']} {result}")
                    content = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                    messages.append({"role": "assistant", "tool_calls": [tool_call.model_dump()]})
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})
            else:
                break


# get text response from LLM API, with retry mechanism for network issues
def request_LLM_api(model_config: dict, prompt: str, system_prompt: str = "", response_format=None):
    L = T.get(language, T["en"])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    client = OpenAI(api_key=model_config["api_key"], base_url=model_config["base_url"])
    for i in range(3):
        try:
            qprint(f"{L['api_connect']} [ {model_config['model']} ] ...")
            completion = client.chat.completions.create(
                model=model_config["model"],
                messages=messages,
                response_format=response_format,
                temperature=1.0
            )
            content = completion.choices[0].message.content
            qprint(L['api_success'])
            return content
        except Exception as e:
            # choose retry icon based on attempt number, default to warning if out of range
            icon = L['retry_icons'][i] if i < len(L['retry_icons']) else "⚠️"
            # print retry message with error details
            qprint(f"{icon} {L['api_retry_prefix']} {i+1} {L['api_retry_suffix']}")
            qprint(f"   💡 {L['api_err_report']}: {str(e)}")
            if i < 2:
                continue
    # after 3 failed attempts, print final failure message and return None
    qprint("\n" + "!"*10 + f" {L['api_fail_title']} " + "!"*10)
    qprint(f"❌ {L['api_fail_msg']}")
    return None