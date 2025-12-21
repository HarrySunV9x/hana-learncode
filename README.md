# 基本用法
mcp 服务器文件结构

```python
"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo", json_response=True)


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

@mcp.resource("greeting://{name}")

- 提供静态或动态的数据资源（如文件、配置、数据等）

- AI 可以读取但不能修改，只读访问

- 使用 URI 模式定义资源路径（支持参数化）

- 返回的是资源内容/数据，供 AI 引用和使用

- 常用于：文档内容、配置数据、数据库记录、文件内容等

@mcp.tool()

- 根据prompt，AI 自动决定何时调用

- 用于执行具体任务（查询、计算、分析等）

- 返回数据或结果

@mcp.prompt()

- 用户手动选择使用，在cursor中，输入/可见

- 返回的是提示词文本，不是执行结果

- 用于引导 AI 完成特定任务

具体见：

https://github.com/modelcontextprotocol/python-sdk

# 实战：MCP 工具设计

在设计 MCP 工具时，根据任务的复杂度和对 AI 自主性的要求，主要有三种设计模式：

## 指导文档

```python
@mcp.tool()
def analyze_performance() -> str:
    """性能分析指导工具"""
    return '''
    # 性能分析流程
    
    ## 第一步：收集日志
    使用 search_events_files 工具搜索事件日志...
    
    ## 第二步：提取关键数据
    使用 find_keyword_logs 工具提取关键字...
    
    ## 第三步：生成报告
    调用 generate_report 工具生成分析报告...
    '''
```

根据一整篇指导文档执行步骤。

**优点：**

- 工具编写简单，提供完整的操作指导并接入mcp即可
- 维护方便，一个文档管理所有步骤

**缺点：**
- 上下文冗长，AI 容易遗漏、跳过、自我联想执行步骤，越靠后越难以控制
- 无法存储过程中的状态，不好追溯

## 工作流

```python
@mcp.tool()
def init_scene_workflow(log_path: str, timestamp: str, time_window: float = 20.0) -> str:
    """【步骤 1/6】初始化场景分析工作流"""
    workflow_id = f"workflow_{int(time.time())}"
    workflows[workflow_id] = {
        "current_step": 1,
        "log_path": log_path,
        "timestamp": timestamp,
        "time_window": time_window,
        "status": "initialized"
    }
    return json.dumps({
        "workflow_id": workflow_id,
        "next_step": "调用 search_events 工具继续",
        "status": "success"
    })

@mcp.tool()
def search_events(workflow_id: str) -> str:
    """【步骤 2/6】搜索 Events 日志文件"""
    workflow = workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"error": "工作流不存在"})
    
    # 执行搜索逻辑
    events_files = search_events_in_path(workflow["log_path"])
    
    # 更新状态
    workflow["current_step"] = 2
    workflow["events_files"] = events_files
    
    return json.dumps({
        "status": "success",
        "found_files": len(events_files),
        "next_step": "调用 extract_logs 工具继续"
    })

……
```

**优点：**
- AI 可按规定步骤执行，可控性强
- 各步骤均可按设计调节，结果可记录，灵活性强
- 每步职责单一，易于测试和调试

**缺点：**
- AI自主性低，设计要求难
- 多步骤维护，拓展性有，但维护起来很困难

- AI是否自主分析可能难以把控

**自主分析控制**

search_event 得到日志结果，如果想要AI自主分析，可能需要特别的返回值说明。

# 架构设计

项目目录结构：

```
hana-learncode/
├── core/              # 核心功能函数（业务逻辑）
│   ├── code_indexer.py      # 代码索引器
│   ├── code_analyzer.py     # 代码分析器
│   └── flowchart_generator.py  # 流程图生成器
├── tool/              # MCP tool 定义
│   └── create_tool.py        # 注册所有工具
├── workflow/          # 工作流定义、实现
│   ├── workflow_manager.py  # 工作流管理器
│   ├── workflow_control.py  # 工作流控制
│   ├── base_step.py         # 步骤基类
│   └── workflow_steps.py    # 具体步骤实现
├── resource/          # MCP resource 定义
│   └── create_resource.py   # 注册所有资源
├── prompt/            # MCP prompt 定义
│   └── create_prompt.py     # 注册所有提示词
└── main.py            # 主入口，注册所有组件
```

各模块说明：
- **core**: 核心功能函数，包含代码分析、索引、流程图生成等业务逻辑
- **tool**: MCP tool 定义，所有可执行的工具函数
- **workflow**: 工作流定义、实现，包含工作流管理和步骤实现
- **resource**: MCP resource 定义，提供只读数据资源
- **prompt**: MCP prompt 定义，提供提示词模板