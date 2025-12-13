# Hana LearnCode - 代码学习助手 MCP Server

一个专门用于帮助学习和理解代码的 MCP (Model Context Protocol) 服务器。通过自动索引、分析代码库，追踪函数调用流程，并生成可视化流程图，帮助你深入理解复杂代码的工作原理。

## 功能特性

🔍 **代码仓库扫描与索引**
- 支持多种编程语言（C/C++, Python, Java, JavaScript 等）
- 自动提取函数、类、结构体定义
- 智能忽略无关文件和目录

📊 **函数调用流程追踪**
- 追踪函数调用链路
- 分析函数调用深度和关系
- 查找函数之间的调用路径

🎨 **流程图生成**
- 自动生成 Mermaid 格式的流程图
- 支持调用树、概念图、路径图等多种类型
- 可在 Markdown 中直接渲染

🧠 **概念学习助手**
- 基于关键字搜索相关代码
- 分析特定主题的实现（如内存分配、线程管理等）
- 提供代码片段和位置信息

## 安装

1. 克隆或下载此项目

2. 安装依赖（使用 uv）：

```bash
uv sync
```

或者使用 pip：

```bash
pip install -e .
```

## 使用方法

### 1. 启动 MCP Server

```bash
uv run main.py
```

或者：

```bash
python main.py
```

### 2. 配置 MCP 客户端

在你的 MCP 客户端（如 Claude Desktop）配置文件中添加：

```json
{
  "mcpServers": {
    "code-learning": {
      "command": "uv",
      "args": ["run", "F:\\Code\\hana-learncode\\main.py"]
    }
  }
}
```

### 3. 使用工具

服务器提供以下工具：

#### `scan_code_repository`
扫描并索引代码仓库

**参数：**
- `repo_path`: 代码仓库的本地路径
- `extensions`: (可选) 要扫描的文件扩展名，用逗号分隔

**示例：**
```
扫描 Linux kernel 源码：
repo_path: /path/to/linux
extensions: .c,.h
```

#### `search_functions`
搜索包含关键字的函数

**参数：**
- `repo_path`: 代码仓库路径
- `keyword`: 搜索关键字

**示例：**
```
搜索所有包含 "alloc" 的函数
```

#### `trace_function_flow`
追踪函数调用流程

**参数：**
- `repo_path`: 代码仓库路径
- `function_name`: 要追踪的函数名
- `max_depth`: 追踪深度（默认3）

**示例：**
```
追踪 kmalloc 函数的调用流程
```

#### `analyze_code_concept`
分析特定概念相关的代码

**参数：**
- `repo_path`: 代码仓库路径
- `concept`: 概念名称
- `keywords`: 相关关键字，用逗号分隔

**示例：**
```
concept: "内存分配"
keywords: "kmalloc,vmalloc,alloc_pages"
```

#### `get_function_code`
获取完整的函数源代码

**参数：**
- `repo_path`: 代码仓库路径
- `function_name`: 函数名

#### `generate_flowchart`
生成函数调用流程图

**参数：**
- `repo_path`: 代码仓库路径
- `function_name`: 函数名
- `chart_type`: 图表类型（默认 call_tree）
- `max_depth`: 追踪深度（默认3）
- `direction`: 图的方向（TD=上到下，LR=左到右）

#### `generate_concept_flowchart`
生成概念相关的流程图

**参数：**
- `repo_path`: 代码仓库路径
- `concept`: 概念名称
- `keywords`: 相关关键字，用逗号分隔
- `direction`: 图的方向

#### `find_function_path`
查找函数之间的调用路径

**参数：**
- `repo_path`: 代码仓库路径
- `from_function`: 起始函数名
- `to_function`: 目标函数名
- `max_depth`: 最大搜索深度（默认10）

## 使用场景示例

### 场景 1: 学习 Linux Kernel 内存分配原理

```
提问：我想了解 Linux kernel 内存分配的原理，能通过源码告诉我整个过程吗？并生成流程图

步骤：
1. scan_code_repository(repo_path="/path/to/linux", extensions=".c,.h")
2. analyze_code_concept(repo_path="/path/to/linux", concept="内存分配", keywords="kmalloc,vmalloc,alloc_pages,__get_free_pages")
3. trace_function_flow(repo_path="/path/to/linux", function_name="kmalloc", max_depth=4)
4. generate_flowchart(repo_path="/path/to/linux", function_name="kmalloc", max_depth=3)
5. get_function_code(repo_path="/path/to/linux", function_name="kmalloc")
```

### 场景 2: 理解项目中的某个功能模块

```
提问：这个项目的用户认证是如何实现的？

步骤：
1. scan_code_repository(repo_path="/path/to/project")
2. search_functions(repo_path="/path/to/project", keyword="auth")
3. trace_function_flow(repo_path="/path/to/project", function_name="authenticate_user")
4. generate_concept_flowchart(repo_path="/path/to/project", concept="用户认证", keywords="auth,login,verify")
```

### 场景 3: 查找函数调用关系

```
提问：main 函数是如何调用到 process_data 函数的？

步骤：
1. find_function_path(repo_path="/path/to/project", from_function="main", to_function="process_data")
```

## 支持的编程语言

- C/C++ (.c, .h, .cpp, .hpp)
- Python (.py)
- Java (.java)
- JavaScript/TypeScript (.js, .ts)

## 技术栈

- **FastMCP**: MCP 服务器框架
- **Python 3.13+**: 开发语言
- **正则表达式**: 代码解析
- **Mermaid**: 流程图生成

## 项目结构

```
hana-learncode/
├── core/                    # 核心功能模块
│   ├── code_indexer.py     # 代码索引器
│   ├── code_analyzer.py    # 代码分析器
│   └── flowchart_generator.py  # 流程图生成器
├── tool/                    # MCP 工具定义
│   └── create_tool.py      # 工具注册
├── main.py                  # MCP 服务器入口
├── pyproject.toml          # 项目配置
└── README.md               # 说明文档
```

## 注意事项

1. 首次使用时需要先扫描代码仓库建立索引
2. 大型代码库（如 Linux kernel）的扫描可能需要较长时间
3. 流程图复杂度受 `max_depth` 参数控制，建议从小值开始
4. 目前使用正则表达式进行代码解析，对于复杂语法可能不够准确

## 未来计划

- [ ] 集成 Tree-sitter 进行更准确的语法解析
- [ ] 支持更多编程语言
- [ ] 添加代码复杂度分析
- [ ] 支持增量索引
- [ ] 添加代码搜索和相似度分析
- [ ] 生成更丰富的可视化图表

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！
