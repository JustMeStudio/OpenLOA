import os
import json
import sys
import subprocess
from pathlib import Path

def run_launcher():
    # 1. 基础路径准备
    base_dir = Path(__file__).resolve().parent
    backend_dir = base_dir / "backend"
    config_path = base_dir / "configs" / "agents.json"

    # 2. 读取配置信息
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            agents_config = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误：找不到配置文件 {config_path}")
        return

    # 3. 扫描 ./backend 下的有效 py 文件
    # 只有在配置里的 Agent 且本地有对应 .py 文件的才展示
    available_agents = []
    agent_files = [p.stem for p in backend_dir.glob("*.py")]

    for agent in agents_config:
        if agent["name"] in agent_files:
            available_agents.append(agent)

    if not available_agents:
        print("Empty: ./backend 目录下没有找到匹配的 Agent 文件。")
        return

    # 4. 终端展示列表
    print("\n" + "="*50)
    print(f"{'🤖 OpenLOA Agent 终端控制台':^45}")
    print("="*50)
    print(f"{'编号':<6} {'代号':<15} {'功能说明'}")
    print("-" * 50)

    for idx, agent in enumerate(available_agents, 1):
        print(f"[{idx}]    {agent['nick_name']:<12} | {agent['description']}")

    print("-" * 50)

    # 5. 用户交互选择
    try:
        choice = input(f"\n请选择要运行的 Agent 编号 (1-{len(available_agents)}): ")
        selected_idx = int(choice) - 1
        if selected_idx < 0 or selected_idx >= len(available_agents):
            raise ValueError
    except (ValueError, IndexError):
        print("❌ 输入无效，程序退出。")
        return

    selected_agent = available_agents[selected_idx]
    agent_name = selected_agent["name"]
    target_py = backend_dir / f"{agent_name}.py"

    # 6. 【核心】执行 Agent
    print(f"\n🚀 正在启动 {selected_agent['nick_name']} ({agent_name})...\n")
    
    # 使用当前系统的 Python 解释器运行
    # 设置环境变量 PYTHONPATH 为 backend 目录，解决 Sara.py 里的 import 问题
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        # 执行脚本，并将工作目录设为 backend，这样 Sara.py 内部的相对路径就不会错
        subprocess.run([sys.executable, str(target_py)], cwd=backend_dir, env=env)
    except KeyboardInterrupt:
        print("\n👋 Agent 已停止运行。")

if __name__ == "__main__":
    run_launcher()