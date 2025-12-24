# Hana-LearnCode

基于 MCP（Model Context Protocol）的**代码学习助手服务端**：支持扫描代码库、索引函数/类、追踪调用链、概念分析，并输出 Mermaid 流程图，帮助你快速理解陌生仓库。

## 快速开始

### 环境要求

- Python >= 3.13
- 推荐使用 `uv` 管理依赖（仓库已包含 `uv.lock`）

### 安装依赖

```bash
uv sync
```

### 启动 MCP Server

```bash
uv run python main.py
```

> 启动后，使用支持 MCP 的客户端（如 Claude Desktop / Cursor）连接并调用下方 Tools。

## Tools（主要能力）

> 推荐按顺序调用；其中 `search_functions / trace_function_flow / analyze_concept` 属于 **repeatable**，可在会话中多次执行。

1. `init_learn_code_workflow(code_path, extensions?, workflow_type?)`
2. `scan_repository(session_id, repo_path?, extensions?)`
3. `search_functions(session_id, keyword?)`
4. `trace_function_flow(session_id, function_name?, max_depth?)`
5. `analyze_concept(session_id, concept, keywords)`
6. `generate_flowchart(session_id, chart_type?, direction?)`
7. `get_workflow_status(session_id)`
8. `list_sessions()`

## Resources（只读观测）

- `code://sessions`
- `code://session/{session_id}/info`
- `code://session/{session_id}/functions`
- `code://session/{session_id}/flowchart`
- `code://help`

## 典型使用流程

1) 初始化会话（返回 `session_id`）

- `init_learn_code_workflow(code_path="你的仓库路径")`

2) 扫描并索引（必须先做）

- `scan_repository(session_id="...")`

3) 搜索函数 / 追踪调用链 / 概念分析（三选一或多选）

- `search_functions(session_id="...", keyword="register")`
- `trace_function_flow(session_id="...", function_name="main", max_depth=3)`
- `analyze_concept(session_id="...", concept="内存分配", keywords="malloc,alloc,kmalloc")`

4) 生成 Mermaid 图

- `generate_flowchart(session_id="...", chart_type="call_tree", direction="TD")`
- `generate_flowchart(session_id="...", chart_type="concept", direction="LR")`

## 文档

- 架构概览：`架构设计文档.md`
- 学习版详解：`项目架构与实现详解（学习版）.md`


