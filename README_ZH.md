<div align="center">

**[🇨🇳 中文](README_ZH.md) | [🇺🇸 English](README.md)**

</div>

---

# 🤖 OpenLOA - League of Agents (智能体联盟)

![OpenLOA Banner](./assets/hub/banner_zh.png)

<div align="center">

![OpenLOA Banner](https://img.shields.io/badge/OpenLOA-Agent%20Framework-blue?style=for-the-badge&logo=robot)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

**一个开源的 AI Agent 开发与应用框架**  
*让每个开发者都能轻松创建、分享和部署生产级别的智能体*

[功能展示](#-功能特性) • [快速开始](#-快速开始) • [自定义Agent](#-自定义你的agent) • [文档](#-项目结构)

</div>

---

## 🎯 项目愿景

**智能体联盟 (League of Agents, OpenLOA)** 是一个开源的 AI Agent 开发与应用框架。我们相信，随着大语言模型的发展，Agent 将成为连接 AI 和真实世界的桥梁。

我们的使命是：
- ✨ 降低 Agent 的开发门槛，让更多开发者参与其中
- 🚀 提供开箱即用的 GUI 和 TUI 界面
- 🛠️ 为开发者提供完整的工具链和最佳实践
- 🌍 建立一个繁荣的 Agent 生态，共同创造更强大的 AI 应用

---

## ✨ 功能特性

| 特性 | 描述 |
|------|------|
| 🎨 **双界面支持** | 同时支持现代化 GUI（PySide6）和高效 TUI 界面 |
| 🧠 **灵活的Agent框架** | 基于 LLM + Tools 的模块化设计 |
| 🔧 **工具包系统** | 提供丰富的工具库，支持自定义扩展 |
| ⚙️ **多模型支持** | 支持 OpenAI、Claude、本地模型等多种 LLM |
| 📊 **持久化存储** | 集成 ChromaDB 向量数据库 |
| 🤝 **MCP 协议** | 支持 Model Context Protocol 协议 |
| 🎯 **低代码开发** | 配置驱动的 Agent 生成流程 |

---

## 🚀 快速开始

### 1️⃣ 安装依赖

首先，克隆项目并安装必要的依赖包：

```bash
# 克隆项目
git clone https://github.com/DeanFan1994/OpenLOA.git
cd OpenLOA

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置模型 API

编辑 `./configs/models.yaml` 文件，为每个 Agent 及其工具配置模型和 API Key：

```yaml
# Zed Agent 配置
Zed_agent_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: "sk-xxxxxxxxxxxxx"  # 替换为你的 API Key

Zed_writer_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-reasoner"
  api_key: "sk-xxxxxxxxxxxxx"  # 替换为你的 API Key

# Sara Agent 配置
Sara_agent_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: "sk-xxxxxxxxxxxxx"  # 替换为你的 API Key

Sara_job_filter_generate_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-reasoner"
  api_key: "sk-xxxxxxxxxxxxx"  # 替换为你的 API Key

# 你的自定义 Agent 配置
MyCustomAgent_model_config:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
  api_key: "sk-xxxxxxxxxxxxx"  # 替换为你的 API Key
```

> 💡 **提示**：
> - **Agent 可以有多个模型配置**：不同的任务可以使用不同的模型（如：主要任务用 `deepseek-chat`，复杂推理用 `deepseek-reasoner`）
> - **命名规范**：`{AgentName}_{task_name}_model_config`
> - **支持多个提供商**：可以同时配置 OpenAI、Deepseek、Anthropic 等不同的 API 服务商
> - **在 Agent 代码中引用**：在你的 Agent 代码中加载对应的配置即可

### 3️⃣ 启动应用

#### 📱 启动 GUI 版本（推荐新手）
```bash
python app_GUI.py
```

#### 🖥️ 启动 TUI 版本（推荐高级用户）
```bash
python app_TUI.py
```

<div align="center">

**就这么简单！三步即可启动你的第一个 Agent！** 🎉

</div>

---

## 🎨 自定义你的 Agent

OpenLOA 采用模块化设计，让你可以轻松定制属于自己的 Agent。以下是完整的创建流程：

### 第一步：编写 Agent 主体

在 `./backend/` 目录下创建你的 Agent 主文件：

```python
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from utils.config import load_model_config
from utils.com import qprint, chat
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers, load_all_tools_from_local_toolboxes
from globals import globals

# 防止输出乱码
sys.stdout.reconfigure(encoding="utf-8", newline=None)

# 加载模型配置
agent_model_config = load_model_config("MyCustomAgent_agent_model_config")

# 定义 Agent 的系统提示词
system_prompt = """你是一个智能助手，具备以下能力：
- [在这里描述你的 Agent 的能力和职责]
- [具体的工作流程和目标]
"""

async def main():
    try:
        # Agent 开场白
        qprint("👋 欢迎使用我的智能 Agent ")
        
        # 初始化项目资源
        globals.PROJECT_NAME = "MyCustomAgent"
        globals.PROJECT_PATH = os.path.abspath(f"./projects/{globals.PROJECT_NAME}")
        os.makedirs(globals.PROJECT_PATH, exist_ok=True)
        
        # 声明本地自定义工具包（可配置多个）
        local_tool_boxes = [
            "MyCustomTools",     # 你的自定义工具包
            # "OtherTools",      # 可以添加更多工具包
        ]
        local_tools, local_tools_registry = load_all_tools_from_local_toolboxes(local_tool_boxes)
        
        # 加载 MCP 服务器工具（可选）
        # 支持以下几种配置方式，取消注释使用：
        mcp_servers = [
            # 1️⃣ NPX 包方式 - 文件系统控制
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]),
            
            # 2️⃣ UVX 包方式 - 标记文本格式互转（需要 uv 工具）
            # MCPToolSession("uvx", ["--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple", "mcp-pandoc"]),
            
            # 3️⃣ 本地包方式 - 火车票查询等自定义服务
            # MCPToolSession("npx", ["-y", "./local_servers/12306-mcp"]),
            
            # 4️⃣ SSE 链接方式 - 远端 MCP 服务（如百度优选 MCP）
            # MCPToolSession(sse_url="https://mcp-youxuan.baidu.com/mcp/sse?key=<your-api-key>"),
        ]
        mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)
        
        # 合并所有工具
        tools = local_tools + mcp_tools
        tools_registry = local_tools_registry | mcp_registry
        
        # 列举已有的工具
        tools_names = "\n".join(tools_registry.keys())
        qprint(f"✅ 已加载工具：\n{tools_names}")
        
        qprint("🚀 Agent 已就绪！")
        
        # 启动对话循环
        try:
            await chat(agent_model_config, system_prompt, tools, tools_registry)
        finally:
            # 关闭 MCP 会话
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("👋 会话已结束")
    
    except Exception as e:
        qprint(f"❌ 启动失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

**关键点说明：**

✅ **配置加载** - 使用 `load_model_config()` 加载 YAML 配置  
✅ **异步架构** - 采用 `async/await` 支持非阻塞操作  
✅ **工具集成** - 支持本地工具和 MCP 远端工具  
✅ **统一对话** - 通过 `chat()` 函数处理所有对话和工具调用  
✅ **资源管理** - 自动创建项目资源目录并管理生命周期

### 第二步：创建工具包

在 `./backend/tools/` 下创建你的工具包文件：

```python
# backend/tools/MyCustomTools.py
import json
from utils.config import load_model_config
from utils.com import request_LLM_api

# ==================== 工具实现 ====================

def search_web(query: str) -> str:
    """
    在网络上搜索信息
    Args:
        query: 搜索关键词
    Returns:
        搜索结果字符串
    """
    # 实现你的搜索逻辑
    return f"搜索结果：{query}"

def analyze_data(data: str) -> str:
    """
    分析数据
    Args:
        data: 待分析数据
    Returns:
        分析结果
    """
    # 实现你的数据分析逻辑
    return f"分析完成：{data}"

def generate_summary(content: str) -> str:
    """
    使用 LLM 生成内容摘要
    Args:
        content: 待摘要的内容
    Returns:
        生成的摘要
    """
    # 在工具内部调用 LLM API 的示例
    
    # 1️⃣ 加载模型配置
    model_config = load_model_config("MyCustomAgent_agent_model_config")
    
    # 2️⃣ 定义提示词
    system_prompt = "你是一个专业的文本摘要助手，能够快速提炼内容要点。"
    user_prompt = f"请为以下内容生成一个简洁的摘要：\n{content}"
    
    # 3️⃣ 调用 LLM API
    summary = request_LLM_api(model_config, user_prompt, system_prompt)
    
    return summary

# ==================== 工具注册 ====================

# 工具函数映射表（LLM 调用工具时根据名称查找函数）
tool_registry = {
    "search_web": search_web,
    "analyze_data": analyze_data,
    "generate_summary": generate_summary,
}

# 工具定义数组（符合 OpenAI Function Calling 格式）
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "在网络上搜索相关信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_data",
            "description": "对数据进行分析和处理",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "待分析的数据"
                    }
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_summary",
            "description": "使用 AI 生成内容摘要",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "待摘要的内容"
                    }
                },
                "required": ["content"]
            }
        }
    }
]
```

**工具包的核心要素：**

✅ **工具函数** - 实现具体的业务逻辑的 Python 函数  
✅ **工具注册表** - `tool_registry` 字典，将工具名称映射到函数对象  
✅ **工具定义** - `tools` 列表，遵循 OpenAI Function Calling 规范  
✅ **参数描述** - 清晰的参数名称和说明，帮助 LLM 正确调用  

**💡 工具内部调用 LLM API：**

当工具需要 LLM 的支持时（如数据分析、文本生成等），可使用 `request_LLM_api()` 函数：

```python
from utils.config import load_model_config
from utils.com import request_LLM_api

# 加载模型配置
model_config = load_model_config("Config_Name")

# 调用 LLM API - 三个必需参数
response = request_LLM_api(
    model_config,      # ✅ 模型配置对象
    user_prompt,       # ✅ 用户提示词
    system_prompt      # ✅ 系统提示词
)
```

在 Agent 主文件中动态加载工具：

```python
from utils.mcp import load_all_tools_from_local_toolboxes

# 声明要加载的工具包名称
local_tool_boxes = [
    "MyCustomTools",     # 你的工具包名称
    # "OtherTools",      # 支持加载多个工具包
]

# 动态加载所有工具
local_tools, local_tools_registry = load_all_tools_from_local_toolboxes(local_tool_boxes)
```

### 第三步：配置 Agent 信息

编辑 `./configs/agents.json`，添加你的 Agent 配置：

```json
{
    "name": "MyCustomAgent",
    "type": "文本处理",
    "nick_name": "我的智能体",
    "description": "这是我定制的超强智能体，能够...",
    "avatar": "./assets/avatar/MyCustomAgent.jpg",
    "model": "gpt-4",
    "tools": ["search_information", "analyze_data"]
}
```

### 第四步：配置模型和 API

在 `./configs/models.yaml` 中为你的 Agent 配置所需的模型：

```yaml
# MyCustomAgent 主要任务配置
MyCustomAgent_agent_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: "sk-xxxxxxxxxxxxx"

# MyCustomAgent 复杂任务配置（可选）
MyCustomAgent_reasoning_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-reasoner"
  api_key: "sk-xxxxxxxxxxxxx"
```

在你的 Agent 代码中使用 `load_model_config()` 函数加载配置：

```python
from utils.config import load_model_config

# 加载主要任务的模型配置
agent_config = load_model_config("MyCustomAgent_agent_model_config")

# 加载复杂推理任务的模型配置（可选）
reasoning_config = load_model_config("MyCustomAgent_reasoning_model_config")

# 配置会自动被传递给 chat() 函数使用
await chat(agent_config, system_prompt, tools, tools_registry)
```

### 第五步（可选）：创建自定义 GUI 页面

在 `./pages/agents/` 下创建专属的 GUI 页面：

```python
# pages/agents/MyCustomAgent.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit
from backend.MyCustomAgent import MyCustomAgent

class MyCustomAgentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent = MyCustomAgent(api_key="your-api-key")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入你的需求...")
        
        self.run_button = QPushButton("执行")
        self.run_button.clicked.connect(self.run_agent)
        
        self.output_field = QTextEdit()
        self.output_field.setReadOnly(True)
        
        layout.addWidget(self.input_field)
        layout.addWidget(self.run_button)
        layout.addWidget(self.output_field)
        
        self.setLayout(layout)
    
    def run_agent(self):
        user_input = self.input_field.text()
        result = self.agent.run(user_input)
        self.output_field.setText(result)
```

---

## 📁 项目结构

```
OpenLOA/
├── app_GUI.py                 # GUI 应用入口
├── app_TUI.py                 # TUI 应用入口
├── requirements.txt           # Python 依赖
├── README.md                  # 项目文档
│
├── assets/                    # 资源文件
│   ├── avatar/               # Agent 头像
│   └── home/                 # 首页资源
│
├── backend/                   # Agent 核心逻辑
│   ├── Sara.py               # Sara Agent
│   ├── Zed.py                # Zed Agent
│   ├── tools/                # 工具包
│   │   ├── Sara_tools.py
│   │   ├── Zed_tools.py
│   │   └── __pycache__/
│   ├── utils/                # 工具函数
│   │   ├── config.py         # 配置管理
│   │   ├── mcp.py            # MCP 协议支持
│   │   └── com.py            # 通信工具
│   └── chroma_db/            # 向量数据库
│
├── pages/                     # GUI 页面
│   ├── MainWindow.py         # 主窗口
│   ├── WelcomePage.py        # 欢迎页
│   ├── ChooseAgentPage.py    # Agent 选择页
│   └── agents/               # Agent 专用页面
│       ├── Sara.py
│       └── Zed.py
│
└── configs/                   # 配置文件
    ├── agents.json           # Agent 配置
    ├── models.yaml           # 模型配置
    └── settings.yaml         # 应用配置
```

---

## 📦 现有 Agent 展示

OpenLOA 提供了多个开箱即用的 Agent：

| Agent | 功能 | 描述 |
|-------|------|------|
| 🎭 **Zed** | 文本处理 | 替你写汇报（仿造你以前的文字风格） |
| 💼 **Sara** | 求职招聘 | 自动投简历（自动根据简历内容投递） |
| 🧠 **Riven** | 资源抓取 | 图神经网络专家 |
| 💨 **Yasuo** | 图片生成 | 强化学习玩家 |
| 🌸 **Catherine** | 图片处理 | 多模态处理专家 |
| 🥷 **Akali** | 数据分析 | 隐秘的数据分析师 |
| 🧪 **Singed** | 实验生成 | 疯狂的科学家 |
| 💣 **Jinx** | 视频生成 | 视频生成演员 |

---

## 🔧 开发指南

### 环境要求

- Python 3.8+
- pip 或其他包管理工具
- 有效的 LLM API Key（OpenAI、Anthropic 等）

### 推荐的开发流程

1. **创建新分支** 用于开发你的 Agent
   ```bash
   git checkout -b feature/my-agent
   ```

2. **开发并测试**
   ```bash
   # 在本地测试你的 Agent
   python backend/MyAgent.py
   ```

3. **提交代码**
   ```bash
   git commit -m "feat: Add MyAgent"
   git push origin feature/my-agent
   ```

4. **提交 Pull Request**
   详细描述你的 Agent 功能、使用方式等

---

## 🌟 高级功能

### 💾 向量数据库集成 - 实现 RAG 架构

**什么是 RAG (Retrieval-Augmented Generation)？**

RAG 是一种先进的 AI 技术，结合了检索（Retrieval）和生成（Generation）两个阶段：
1. **检索阶段** - 从向量数据库中检索与用户问题相关的信息
2. **生成阶段** - 基于检索到的上下文，LLM 生成更准确、更具体的回答

通过 ChromaDB 为你的 Agent 实现 RAG 架构，可以：
- 🧠 为 Agent 添加长期记忆和专业知识库
- 🎯 基于历史数据做出更准确的决策
- 📚 支持持续学习，Agent 的能力随时间积累而增强

#### 第一步：配置 Embedding 模型

在 `./configs/models.yaml` 中添加向量化模型配置：

```yaml
# MyCustomAgent 向量化模型配置（用于 RAG 检索）
MyCustomAgent_embedding_model_config:
  base_url: "https://api.deepseek.com"
  model: "text-embedding-3-small"      # 将文本转换为向量
  api_key: "sk-xxxxxxxxxxxxx"
```

#### 第二步：在工具或 Agent 中实现 RAG

```python
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from utils.config import load_model_config
from ulid import ULID

# 1️⃣ 加载向量化模型配置（从 YAML 读取）
embedding_model_config = load_model_config("MyCustomAgent_embedding_model_config")

# 2️⃣ 初始化 OpenAI 客户端（使用配置中的参数）
oa_client = OpenAI(
    api_key=embedding_model_config.get("api_key"),
    base_url=embedding_model_config.get("base_url")
)

# 3️⃣ 初始化持久化向量数据库客户端
client = chromadb.PersistentClient(
    path="./chroma_db",                 # 数据存储位置
    settings=Settings()
)

# 4️⃣ 获取或创建集合（Collection）
collection = client.get_or_create_collection(name="agent_memory")

# 5️⃣ 生成文本向量
def embed_text(text: str) -> list:
    """将文本转换为向量"""
    response = oa_client.embeddings.create(
        model=embedding_model_config.get("model"),  # 使用配置中的模型
        input=text
    )
    return response.data[0].embedding

# 6️⃣ 存储内容到向量数据库
embedding = embed_text("User experience and feedback")
collection.add(
    ids=[str(ULID())],                  # 生成唯一 ID
    embeddings=[embedding],
    documents=["User experience and feedback"],
    metadatas=[{"type": "feedback", "date": "2024-03-12"}]
)

# 7️⃣ 向量搜索 - 检索相似信息
query_embedding = embed_text("What did users say?")
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,                        # 返回最相似的 3 条
    include=["documents", "metadatas", "distances"]
)

# 8️⃣ 处理搜索结果
for doc, metadata, distance in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
):
    print(f"📄 文档: {doc}")
    print(f"📊 相似度: {1 - distance:.4f}")  # 距离越小，相似度越高
```

**RAG 工作流程：**

```
【RAG 流程】
用户问题 → 向量化 → 向量检索 → 相似文档 → LLM 上下文生成 → 精准回答
         (Embedding)  (Retrieval) (Top-K)    (Augmented Generation)
```

**关键点提示：**

✅ **使用配置加载** - 通过 `load_model_config()` 读取 YAML 配置，便于修改  
✅ **不硬编码密钥** - API Key 和 Base URL 都从配置中读取  
✅ **唯一 ID 生成** - 使用 ULID 库生成全局唯一的记录 ID  
✅ **元数据管理** - 为每条记录附加类型、日期等信息，便于后续查询  
✅ **相似度排序** - 返回的结果按相似度排序，距离越小相似度越高  

**RAG 架构的优势：**

✅ **知识增强** - LLM 基于实际数据生成答案，减少幻觉（Hallucination）  
✅ **上下文感知** - 检索相关信息作为上下文，提升答案准确性和相关性  
✅ **持续学习** - 新数据持续录入向量库，Agent 能力不断提升  
✅ **可追溯性** - 用户可查看 Agent 的回答基于哪些资料  

**ChromaDB 的核心优势：**

✅ **持久化存储** - 数据保存在本地文件系统，支持长期积累  
✅ **向量检索** - 快速找到相似内容，用于 RAG 的检索阶段  
✅ **元数据管理** - 为每条记录附加类型、日期等信息  
✅ **灵活查询** - 支持向量相似性搜索，而非精确匹配  

---

### 🌐 MCP 协议支持

通过 Model Context Protocol 实现与其他系统的无缝集成。在 Agent 主文件中配置 MCP 服务器：

```python
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers
import asyncio

async def main():
    # 配置支持 4 种不同的 MCP 服务器连接方式
    mcp_servers = [
        # 1️⃣ NPX 包方式 - 访问本地文件系统
        MCPToolSession("npx", [
            "-y", 
            "@modelcontextprotocol/server-filesystem", 
            "./workspace"
        ]),
        
        # 2️⃣ UVX 包方式 - 使用 PyPI 上的 MCP 工具（需要安装 uv）
        MCPToolSession("uvx", [
            "--index-url",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "mcp-pandoc"                    # 标记文本格式互转工具
        ]),
        
        # 3️⃣ 本地包方式 - 使用本地开发的 MCP 服务
        MCPToolSession("npx", [
            "-y",
            "./local_servers/train-ticket-mcp"  # 本地火车票查询服务
        ]),
        
        # 4️⃣ SSE 链接方式 - 连接远端 MCP 服务（如云端 MCP）
        MCPToolSession(sse_url="https://mcp-baidu.example.com/sse?key=your-api-key"),
    ]
    
    # 加载所有 MCP 工具
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)
    
    # 合并工具
    tools = local_tools + mcp_tools
    tools_registry = local_tools_registry | mcp_registry
    
    # 启动 Agent 对话时就拥有 MCP 工具的能力了
    await chat(agent_model_config, system_prompt, tools, tools_registry)
    
    # 对话结束后关闭 MCP 会话
    for mcp in mcp_sessions:
        await mcp.close()
```

**MCP 集成的应用场景：**

| 方式 | 用途 | 示例 |
|------|------|------|
| **NPX 包** | 系统级工具 | 文件系统访问、命令执行 |
| **UVX 包** | Python 工具库 | 文本处理、数据转换 |
| **本地服务** | 自定义服务 | 业务逻辑、数据查询 |
| **SSE 链接** | 云端服务 | 三方 API、外部数据源 |

---

## 📝 许可证

本项目采用 **MIT 许可证**。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！包括但不限于：

- 🐛 报告 Bug
- ✨ 提议新功能
- 📝 改进文档
- 🎨 创建新的 Agent
- 🔧 优化代码

### 贡献步骤

1. Fork 本项目
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

---

## 📞 联系方式

- 📧 Email: fdshiwoa@gmail.com
- 💬 微信: fdshiwoa
- 💬 GitHub Discussions: [在此提问](https://github.com/DeanFan1994/OpenLOA/discussions)
- 🐛 Issue Tracker: [报告问题](https://github.com/DeanFan1994/OpenLOA/issues)

---

## 🙏 致谢

感谢所有为 OpenLOA 做出贡献的开发者和用户！

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

Made with ❤️ by the OpenLOA Team

</div>
