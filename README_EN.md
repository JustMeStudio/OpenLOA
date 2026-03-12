<div align="center">

**[🇨🇳 中文](README.md) | [🇺🇸 English](README_EN.md)**

</div>

---

# 🤖 OpenLOA - League of Agents

<div align="center">

![OpenLOA Banner](https://img.shields.io/badge/OpenLOA-Agent%20Framework-blue?style=for-the-badge&logo=robot)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

**An Open-Source AI Agent Development & Application Framework**  
*Empower every developer to easily create, share, and deploy production-grade intelligent agents*

[Features](#-features) • [Quick Start](#-quick-start) • [Custom Agent](#-customize-your-agent) • [Docs](#-project-structure)

</div>

---

## 🎯 Vision

**OpenLOA (League of Agents)** is an open-source AI Agent development and application framework. We believe that as Large Language Models evolve, Agents will become the bridge connecting AI to the real world.

Our Mission:
- ✨ Lower the barrier to Agent development and enable more developers to participate
- 🚀 Provide out-of-the-box GUI and TUI interfaces
- 🛠️ Provide developers with a complete toolchain and best practices
- 🌍 Build a thriving Agent ecosystem and create more powerful AI applications together

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **Dual Interface Support** | Support for modern GUI (PySide6) and efficient TUI interfaces |
| 🧠 **Flexible Agent Framework** | Modular design based on LLM + Tools |
| 🔧 **Tool Package System** | Rich tool library with custom extension support |
| ⚙️ **Multi-Model Support** | Support for OpenAI, Claude, local models and more |
| 📊 **Persistent Storage** | Integrated ChromaDB vector database |
| 🤝 **MCP Protocol** | Support for Model Context Protocol |
| 🎯 **Low-Code Development** | Configuration-driven Agent generation process |

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies

Clone the project and install required packages:

```bash
# Clone the project
git clone https://github.com/DeanFan1994/OpenLOA.git
cd OpenLOA

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure Model API

Edit `./configs/models.yaml` to configure models and API keys for each Agent:

```yaml
# Zed Agent Configuration
Zed_agent_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: "sk-xxxxxxxxxxxxx"  # Replace with your API Key

Zed_writer_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-reasoner"
  api_key: "sk-xxxxxxxxxxxxx"  # Replace with your API Key

# Sara Agent Configuration
Sara_agent_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: "sk-xxxxxxxxxxxxx"  # Replace with your API Key

Sara_job_filter_generate_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-reasoner"
  api_key: "sk-xxxxxxxxxxxxx"  # Replace with your API Key

# Your Custom Agent Configuration
MyCustomAgent_model_config:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
  api_key: "sk-xxxxxxxxxxxxx"  # Replace with your API Key
```

> 💡 **Tips**:
> - **Agents can have multiple model configurations**: Different tasks can use different models
> - **Naming convention**: `{AgentName}_{task_name}_model_config`
> - **Multiple providers**: Configure OpenAI, Deepseek, Anthropic and other providers simultaneously
> - **Reference in Agent code**: Load corresponding configuration in your Agent code

### 3️⃣ Launch Application

#### 📱 Launch GUI Version (Recommended for beginners)
```bash
python app_GUI.py
```

#### 🖥️ Launch TUI Version (Recommended for advanced users)
```bash
python app_TUI.py
```

<div align="center">

**That's it! Launch your first Agent in just three steps!** 🎉

</div>

---

## 🎨 Customize Your Agent

OpenLOA uses modular design to let you easily customize your own Agent. Here's the complete creation process:

### Step 1: Write Agent Core

Create your Agent main file in `./backend/`:

```python
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from utils.config import load_model_config
from utils.com import qprint, chat
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers, load_all_tools_from_local_toolboxes
from globals import globals

# Prevent output encoding issues
sys.stdout.reconfigure(encoding="utf-8", newline=None)

# Load model configuration
agent_model_config = load_model_config("MyCustomAgent_agent_model_config")

# Define Agent system prompt
system_prompt = """You are an intelligent assistant with the following capabilities:
- [Describe your Agent's abilities and responsibilities here]
- [Specific workflow and objectives]
"""

async def main():
    try:
        # Agent welcome message
        qprint("👋 Welcome to use my intelligent Agent ")
        
        # Initialize project resources
        globals.PROJECT_NAME = "MyCustomAgent"
        globals.PROJECT_PATH = os.path.abspath(f"./projects/{globals.PROJECT_NAME}")
        os.makedirs(globals.PROJECT_PATH, exist_ok=True)
        
        # Declare local custom tool packages (configurable)
        local_tool_boxes = [
            "MyCustomTools",     # Your custom tool package
            # "OtherTools",      # Can add more tool packages
        ]
        local_tools, local_tools_registry = load_all_tools_from_local_toolboxes(local_tool_boxes)
        
        # Load MCP server tools (optional)
        # Support the following configuration methods, uncomment to use:
        mcp_servers = [
            # 1️⃣ NPX package method - File system control
            # MCPToolSession("npx", ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]),
            
            # 2️⃣ UVX package method - Markup text format conversion (requires uv tool)
            # MCPToolSession("uvx", ["--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple", "mcp-pandoc"]),
            
            # 3️⃣ Local package method - Custom services like train ticket queries
            # MCPToolSession("npx", ["-y", "./local_servers/12306-mcp"]),
            
            # 4️⃣ SSE link method - Remote MCP services (e.g., Baidu selected MCP)
            # MCPToolSession(sse_url="https://mcp-youxuan.baidu.com/mcp/sse?key=<your-api-key>"),
        ]
        mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)
        
        # Merge all tools
        tools = local_tools + mcp_tools
        tools_registry = local_tools_registry | mcp_registry
        
        # List loaded tools
        tools_names = "\n".join(tools_registry.keys())
        qprint(f"✅ Loaded tools:\n{tools_names}")
        
        qprint("🚀 Agent is ready!")
        
        # Start conversation loop
        try:
            await chat(agent_model_config, system_prompt, tools, tools_registry)
        finally:
            # Close MCP sessions
            for mcp in mcp_sessions:
                await mcp.close()
            qprint("👋 Session ended")
    
    except Exception as e:
        qprint(f"❌ Startup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points:**

✅ **Config Loading** - Use `load_model_config()` to load YAML configuration  
✅ **Async Architecture** - Use `async/await` for non-blocking operations  
✅ **Tool Integration** - Support local tools and remote MCP tools  
✅ **Unified Chat** - Use `chat()` function to handle all conversations and tool calls  
✅ **Resource Management** - Automatically create project directories and manage lifecycle

### Step 2: Create Tool Package

Create your tool package file in `./backend/tools/`:

```python
# backend/tools/MyCustomTools.py
import json
from utils.config import load_model_config
from utils.com import request_LLM_api

# ==================== Tool Implementation ====================

def search_web(query: str) -> str:
    """
    Search information on the web
    Args:
        query: Search keywords
    Returns:
        Search results
    """
    # Implement your search logic
    return f"Search results: {query}"

def analyze_data(data: str) -> str:
    """
    Analyze data
    Args:
        data: Data to analyze
    Returns:
        Analysis results
    """
    # Implement your data analysis logic
    return f"Analysis complete: {data}"

def generate_summary(content: str) -> str:
    """
    Use LLM to generate content summary
    Args:
        content: Content to summarize
    Returns:
        Generated summary
    """
    # Example of calling LLM API inside tool
    
    # 1️⃣ Load model configuration
    model_config = load_model_config("MyCustomAgent_agent_model_config")
    
    # 2️⃣ Define prompts
    system_prompt = "You are a professional text summarization assistant."
    user_prompt = f"Please generate a concise summary for the following content:\n{content}"
    
    # 3️⃣ Call LLM API
    summary = request_LLM_api(model_config, user_prompt, system_prompt)
    
    return summary

# ==================== Tool Registration ====================

# Tool function mapping table (LLM finds functions by name)
tool_registry = {
    "search_web": search_web,
    "analyze_data": analyze_data,
    "generate_summary": generate_summary,
}

# Tool definition array (conform to OpenAI Function Calling format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search for relevant information on the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords"
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
            "description": "Analyze and process data",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Data to analyze"
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
            "description": "Use AI to generate content summary",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to summarize"
                    }
                },
                "required": ["content"]
            }
        }
    }
]
```

**Core Elements of Tool Package:**

✅ **Tool Functions** - Python functions implementing business logic  
✅ **Tool Registry** - `tool_registry` dictionary mapping tool names to functions  
✅ **Tool Definitions** - `tools` list conforming to OpenAI Function Calling specification  
✅ **Parameter Descriptions** - Clear parameter names and descriptions for LLM  

**💡 Calling LLM API Inside Tools:**

When tools need LLM support (e.g., data analysis, text generation), use `request_LLM_api()`:

```python
from utils.config import load_model_config
from utils.com import request_LLM_api

# Load model configuration
model_config = load_model_config("Config_Name")

# Call LLM API - three required parameters
response = request_LLM_api(
    model_config,      # ✅ Model configuration object
    user_prompt,       # ✅ User prompt
    system_prompt      # ✅ System prompt
)
```

Dynamically load tools in Agent main file:

```python
from utils.mcp import load_all_tools_from_local_toolboxes

# Declare tool package names to load
local_tool_boxes = [
    "MyCustomTools",     # Your tool package name
    # "OtherTools",      # Support loading multiple tool packages
]

# Dynamically load all tools
local_tools, local_tools_registry = load_all_tools_from_local_toolboxes(local_tool_boxes)
```

### Step 3: Configure Agent Info

Edit `./configs/agents.json` to add your Agent configuration:

```json
{
    "name": "MyCustomAgent",
    "type": "Text Processing",
    "nick_name": "My Intelligent Agent",
    "description": "This is my custom powerful agent that can...",
    "avatar": "./assets/avatar/MyCustomAgent.jpg",
    "model": "gpt-4",
    "tools": ["search_information", "analyze_data"]
}
```

### Step 4: Configure Models and API

Configure required models for your Agent in `./configs/models.yaml`:

```yaml
# MyCustomAgent main task configuration
MyCustomAgent_agent_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: "sk-xxxxxxxxxxxxx"

# MyCustomAgent complex task configuration (optional)
MyCustomAgent_reasoning_model_config:
  base_url: "https://api.deepseek.com"
  model: "deepseek-reasoner"
  api_key: "sk-xxxxxxxxxxxxx"
```

Use `load_model_config()` function to load configuration in your Agent code:

```python
from utils.config import load_model_config

# Load main task model configuration
agent_config = load_model_config("MyCustomAgent_agent_model_config")

# Load complex reasoning task model configuration (optional)
reasoning_config = load_model_config("MyCustomAgent_reasoning_model_config")

# Configuration will be automatically passed to chat() function
await chat(agent_config, system_prompt, tools, tools_registry)
```

### Step 5 (Optional): Create Custom GUI Page

Create dedicated GUI page in `./pages/agents/`:

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
        self.input_field.setPlaceholderText("Enter your request...")
        
        self.run_button = QPushButton("Execute")
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

## 📁 Project Structure

```
OpenLOA/
├── app_GUI.py                 # GUI application entry point
├── app_TUI.py                 # TUI application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
│
├── assets/                    # Resource files
│   ├── avatar/               # Agent avatars
│   └── home/                 # Home page resources
│
├── backend/                   # Agent core logic
│   ├── Sara.py               # Sara Agent
│   ├── Zed.py                # Zed Agent
│   ├── tools/                # Tool packages
│   │   ├── Sara_tools.py
│   │   ├── Zed_tools.py
│   │   └── __pycache__/
│   ├── utils/                # Utility functions
│   │   ├── config.py         # Configuration management
│   │   ├── mcp.py            # MCP protocol support
│   │   └── com.py            # Communication tools
│   └── chroma_db/            # Vector database
│
├── pages/                     # GUI pages
│   ├── MainWindow.py         # Main window
│   ├── WelcomePage.py        # Welcome page
│   ├── ChooseAgentPage.py    # Agent selection page
│   └── agents/               # Agent-specific pages
│       ├── Sara.py
│       └── Zed.py
│
└── configs/                   # Configuration files
    ├── agents.json           # Agent configuration
    ├── models.yaml           # Model configuration
    └── settings.yaml         # Application configuration
```

---

## 📦 Existing Agents

OpenLOA provides several ready-to-use Agents:

| Agent | Function | Description |
|-------|----------|-------------|
| 🎭 **Zed** | Text Processing | Write reports for you (mimicking your writing style) |
| 💼 **Sara** | Job Recruitment | Auto-submit resumes (automatically apply based on resume content) |
| 🧠 **Riven** | Resource Scraping | Graph neural network expert |
| 💨 **Yasuo** | Image Generation | Reinforcement learning player |
| 🌸 **Catherine** | Image Processing | Multimodal processing expert |
| 🥷 **Akali** | Data Analysis | Secret data analyst |
| 🧪 **Singed** | Experiment Generation | Mad scientist |
| 💣 **Jinx** | Video Generation | Video generation actor |

---

## 🔧 Development Guide

### Requirements

- Python 3.8+
- pip or other package manager
- Valid LLM API Key (OpenAI, Anthropic, etc.)

### Recommended Development Workflow

1. **Create a new branch** for developing your Agent
   ```bash
   git checkout -b feature/my-agent
   ```

2. **Develop and test**
   ```bash
   # Test your Agent locally
   python backend/MyAgent.py
   ```

3. **Commit code**
   ```bash
   git commit -m "feat: Add MyAgent"
   git push origin feature/my-agent
   ```

4. **Submit Pull Request**
   Describe your Agent's functionality and usage

---

## 🌟 Advanced Features

### 💾 Vector Database Integration - Implementing RAG Architecture

**What is RAG (Retrieval-Augmented Generation)?**

RAG is an advanced AI technique combining retrieval and generation stages:
1. **Retrieval Stage** - Retrieve information related to user questions from vector database
2. **Generation Stage** - Based on retrieved context, LLM generates more accurate answers

Implementing RAG architecture for your Agent with ChromaDB enables:
- 🧠 Add long-term memory and knowledge base for Agents
- 🎯 Make more accurate decisions based on historical data
- 📚 Support continuous learning, Agent capabilities accumulate over time

#### Step 1: Configure Embedding Model

Add embedding model configuration in `./configs/models.yaml`:

```yaml
# MyCustomAgent embedding model configuration (for RAG retrieval)
MyCustomAgent_embedding_model_config:
  base_url: "https://api.deepseek.com"
  model: "text-embedding-3-small"      # Convert text to vectors
  api_key: "sk-xxxxxxxxxxxxx"
```

#### Step 2: Implement RAG in Tools or Agent

```python
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from utils.config import load_model_config
from ulid import ULID

# 1️⃣ Load embedding model configuration (from YAML)
embedding_model_config = load_model_config("MyCustomAgent_embedding_model_config")

# 2️⃣ Initialize OpenAI client (using configuration parameters)
oa_client = OpenAI(
    api_key=embedding_model_config.get("api_key"),
    base_url=embedding_model_config.get("base_url")
)

# 3️⃣ Initialize persistent vector database client
client = chromadb.PersistentClient(
    path="./chroma_db",                 # Data storage location
    settings=Settings()
)

# 4️⃣ Get or create collection
collection = client.get_or_create_collection(name="agent_memory")

# 5️⃣ Generate text vectors
def embed_text(text: str) -> list:
    """Convert text to vectors"""
    response = oa_client.embeddings.create(
        model=embedding_model_config.get("model"),  # Use model from configuration
        input=text
    )
    return response.data[0].embedding

# 6️⃣ Store content to vector database
embedding = embed_text("User experience and feedback")
collection.add(
    ids=[str(ULID())],                  # Generate unique ID
    embeddings=[embedding],
    documents=["User experience and feedback"],
    metadatas=[{"type": "feedback", "date": "2024-03-12"}]
)

# 7️⃣ Vector search - Retrieve similar information
query_embedding = embed_text("What did users say?")
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,                        # Return top 3 similar items
    include=["documents", "metadatas", "distances"]
)

# 8️⃣ Process search results
for doc, metadata, distance in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
):
    print(f"📄 Document: {doc}")
    print(f"📊 Similarity: {1 - distance:.4f}")  # Smaller distance = higher similarity
```

**RAG Workflow:**

```
【RAG Process】
User Question → Vectorization → Vector Retrieval → Similar Documents → LLM Context Generation → Accurate Answer
         (Embedding)  (Retrieval)  (Top-K)          (Augmented Generation)
```

**Key Points:**

✅ **Use Config Loading** - Read YAML configuration via `load_model_config()`  
✅ **No Hardcoded Keys** - API Keys and Base URLs loaded from configuration  
✅ **Unique ID Generation** - Use ULID library to generate globally unique IDs  
✅ **Metadata Management** - Attach type, date and other info to records  
✅ **Similarity Ranking** - Results ranked by similarity, smaller distance = higher similarity  

**RAG Architecture Advantages:**

✅ **Knowledge Enhancement** - LLM generates answers based on real data, reducing hallucinations  
✅ **Context Awareness** - Retrieved information as context improves accuracy and relevance  
✅ **Continuous Learning** - New data continuously recorded enables Agent capability accumulation  
✅ **Traceability** - Users can see which resources Agent answers are based on  

**ChromaDB Core Advantages:**

✅ **Persistent Storage** - Data saved in local file system, supports long-term accumulation  
✅ **Vector Retrieval** - Fast retrieval of similar content for RAG retrieval stage  
✅ **Metadata Management** - Attach type, date and other info to records  
✅ **Flexible Queries** - Support vector similarity search, not just exact matching  

---

### 🌐 MCP Protocol Support

Implement seamless integration with other systems via Model Context Protocol. Configure MCP servers in your Agent main file:

```python
from utils.mcp import MCPToolSession, load_all_tools_from_MCP_servers
import asyncio

async def main():
    # Configure 4 different MCP server connection methods
    mcp_servers = [
        # 1️⃣ NPX package method - Access local file system
        MCPToolSession("npx", [
            "-y", 
            "@modelcontextprotocol/server-filesystem", 
            "./workspace"
        ]),
        
        # 2️⃣ UVX package method - Use MCP tools from PyPI (requires uv tool)
        MCPToolSession("uvx", [
            "--index-url",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "mcp-pandoc"                    # Markup text format conversion tool
        ]),
        
        # 3️⃣ Local package method - Use locally developed MCP services
        MCPToolSession("npx", [
            "-y",
            "./local_servers/train-ticket-mcp"  # Local train ticket query service
        ]),
        
        # 4️⃣ SSE link method - Connect to remote MCP services (e.g., cloud MCP)
        MCPToolSession(sse_url="https://mcp-baidu.example.com/sse?key=your-api-key"),
    ]
    
    # Load all MCP tools
    mcp_tools, mcp_registry, mcp_sessions = await load_all_tools_from_MCP_servers(mcp_servers)
    
    # Merge tools
    tools = local_tools + mcp_tools
    tools_registry = local_tools_registry | mcp_registry
    
    # Agent conversation now has MCP tool capabilities
    await chat(agent_model_config, system_prompt, tools, tools_registry)
    
    # Close MCP sessions after conversation
    for mcp in mcp_sessions:
        await mcp.close()
```

**MCP Integration Use Cases:**

| Method | Purpose | Example |
|--------|---------|---------|
| **NPX Package** | System-level tools | File system access, command execution |
| **UVX Package** | Python tool libraries | Text processing, data transformation |
| **Local Services** | Custom services | Business logic, data queries |
| **SSE Links** | Cloud services | Third-party APIs, external data sources |

---

## 📝 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing Guide

We welcome all forms of contributions! Including but not limited to:

- 🐛 Report bugs
- ✨ Propose new features
- 📝 Improve documentation
- 🎨 Create new Agents
- 🔧 Optimize code

### Contribution Steps

1. Fork this project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Contact

- 📧 Email: fdshiwoa@gmail.com
- 💬 WeChat: fdshiwoa
- 💬 GitHub Discussions: [Ask Here](https://github.com/DeanFan1994/OpenLOA/discussions)
- 🐛 Issue Tracker: [Report Issues](https://github.com/DeanFan1994/OpenLOA/issues)

---

## 🙏 Acknowledgments

Thanks to all developers and users who have contributed to OpenLOA!

---

<div align="center">

**⭐ If this project helps you, please give it a Star!**

Made with ❤️ by the OpenLOA Team

</div>
