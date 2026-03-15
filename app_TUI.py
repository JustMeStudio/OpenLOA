import os
import sys
import subprocess
import yaml
from pathlib import Path

def load_yaml(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 错误：读取文件 {file_path} 失败 - {e}")
        return None

def run_launcher():
    # 1. 基础路径准备
    base_dir = Path(__file__).resolve().parent
    backend_dir = base_dir / "backend"
    settings_path = base_dir / "configs" / "settings.yaml"
    profiles_path = base_dir / "configs" / "profiles.yaml"

    # 2. 读取语言设置
    settings = load_yaml(settings_path)
    lang = settings.get("language", "en") if settings else "en"

    # 3. 读取 Agent Profiles
    profiles = load_yaml(profiles_path)
    if not profiles:
        print("❌ 错误：未能加载配置文件。")
        return

    # 4. 扫描 ./backend 下的有效 py 文件并匹配 Profile
    available_agents = []
    # 获取本地 .py 文件列表
    local_files = [p.stem for p in backend_dir.glob("*.py")]

    for name, info in profiles.items():
        # 如果这个 Agent 在 backend 目录有对应的脚本，则加入可选列表
        if name in local_files:
            # 获取对应语言的内容
            content = info.get(lang, info.get("zh", {})) # 如果设置的语言不存在，降级取 zh
            available_agents.append({
                "name": name,
                "nick_name": content.get("nick_name", name),
                "description": content.get("description", "No description"),
                "type": content.get("type", "General")
            })

    if not available_agents:
        print(f"Empty: ./backend 目录下没有找到匹配的 Agent 文件。")
        return

    # 5. 终端展示列表
    title = "OpenLOA Agent Console" if lang == "en" else "🤖 OpenLOA Agent 终端控制台"
    idx_label = "ID" if lang == "en" else "编号"
    name_label = "Name" if lang == "en" else "代号"
    desc_label = "Description" if lang == "en" else "功能说明"
    
    print("\n" + "="*65)
    print(f"{title:^60}")
    print("="*65)
    print(f"{idx_label:<6} {name_label:<20} | {desc_label}")
    print("-" * 65)

    for idx, agent in enumerate(available_agents, 1):
        print(f"[{idx}]    {agent['nick_name']:<17} | {agent['description']}")

    print("-" * 65)

    # 6. 用户交互选择
    prompt = f"\nSelect Agent ID (1-{len(available_agents)}): " if lang == "en" else f"\n请选择要运行的 Agent 编号 (1-{len(available_agents)}): "
    
    try:
        choice = input(prompt)
        if not choice.strip(): return
        selected_idx = int(choice) - 1
        if selected_idx < 0 or selected_idx >= len(available_agents):
            raise ValueError
    except (ValueError, IndexError):
        err_msg = "Invalid input, exiting." if lang == "en" else "❌ 输入无效，程序退出。"
        print(err_msg)
        return

    selected_agent = available_agents[selected_idx]
    agent_name = selected_agent["name"]
    target_py = backend_dir / f"{agent_name}.py"

    # 7. 执行 Agent
    run_msg = f"🚀 Launching" if lang == "en" else "🚀 正在启动"
    print(f"\n{run_msg} {selected_agent['nick_name']} ({agent_name})...\n")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        subprocess.run([sys.executable, str(target_py)], cwd=backend_dir, env=env)
    except KeyboardInterrupt:
        stop_msg = "\n👋 Agent stopped." if lang == "en" else "\n👋 Agent 已停止运行。"
        print(stop_msg)

if __name__ == "__main__":
    run_launcher()