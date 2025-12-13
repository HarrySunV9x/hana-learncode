# 使用示例

本文档提供了详细的使用示例，帮助你快速上手 Hana LearnCode MCP Server。

## 前提条件

1. 确保已经安装了依赖：`uv sync` 或 `pip install -e .`
2. 启动 MCP Server：`uv run main.py` 或 `python main.py`
3. 在 MCP 客户端（如 Claude Desktop）中配置好服务器

## 示例 1: 学习 Linux Kernel 内存分配机制

### 对话示例

**你：** 我想了解 Linux kernel 内存分配的原理，能通过源码告诉我整个过程吗？并生成流程图。代码地址在：/home/user/linux

**AI 助手会依次调用以下工具：**

#### 步骤 1: 扫描代码仓库

```
工具: scan_code_repository
参数:
  - repo_path: /home/user/linux
  - extensions: .c,.h
```

**返回结果：**
```json
{
  "status": "success",
  "repo_path": "/home/user/linux",
  "scan": {
    "total_files": 25000,
    "extensions": {
      ".c": 20000,
      ".h": 5000
    }
  },
  "index": {
    "indexed": 25000,
    "errors": 0,
    "total_functions": 150000,
    "total_structs": 30000
  },
  "message": "成功扫描 25000 个文件，索引了 150000 个函数"
}
```

#### 步骤 2: 分析内存分配概念

```
工具: analyze_code_concept
参数:
  - repo_path: /home/user/linux
  - concept: "内存分配"
  - keywords: "kmalloc,vmalloc,alloc_pages,__get_free_pages,kzalloc"
```

**返回结果：** 会找到所有相关的内存分配函数，包括它们的位置和代码片段。

#### 步骤 3: 追踪 kmalloc 函数流程

```
工具: trace_function_flow
参数:
  - repo_path: /home/user/linux
  - function_name: kmalloc
  - max_depth: 4
```

**返回结果：** 会显示 kmalloc 调用的所有子函数，构建调用树。

#### 步骤 4: 生成流程图

```
工具: generate_flowchart
参数:
  - repo_path: /home/user/linux
  - function_name: kmalloc
  - max_depth: 3
  - direction: TD
```

**返回结果：**
```json
{
  "status": "success",
  "function": "kmalloc",
  "flowchart": "graph TD\n    node1[\"kmalloc\\n(mm/slab.c:3654)\"]\n    style node1 fill:#f9f,stroke:#333,stroke-width:4px\n    node2[\"__kmalloc\\n(mm/slab.c:3710)\"]\n    node1 --> node2\n    node3[\"slab_alloc\\n(mm/slab.c:3245)\"]\n    node2 --> node3\n    ...",
  "format": "mermaid"
}
```

#### 步骤 5: 获取关键函数代码

```
工具: get_function_code
参数:
  - repo_path: /home/user/linux
  - function_name: kmalloc
```

**AI 助手的回答可能包括：**

> Linux kernel 的内存分配机制主要通过 slab 分配器实现。让我为你详细解释：
> 
> **核心流程：**
> 1. **kmalloc()** 是用户空间最常用的内存分配函数
> 2. 它会调用 **__kmalloc()** 进行实际分配
> 3. __kmalloc 使用 **slab_alloc()** 从 slab 缓存中分配
> 4. 如果缓存不足，会调用 **cache_grow()** 扩展缓存
> 5. 最终通过 **alloc_pages()** 从伙伴系统获取物理页
> 
> **流程图：**
> ```mermaid
> [此处会显示生成的 Mermaid 流程图]
> ```
> 
> **关键代码片段：**
> [此处会显示 kmalloc 的实际源代码]

---

## 示例 2: 理解 Python Web 框架的请求处理流程

### 对话示例

**你：** 这个 Flask 项目是如何处理 HTTP 请求的？能帮我追踪一下从接收请求到返回响应的整个流程吗？

#### 步骤 1: 扫描项目

```
工具: scan_code_repository
参数:
  - repo_path: /home/user/my-flask-app
```

#### 步骤 2: 搜索相关函数

```
工具: search_functions
参数:
  - repo_path: /home/user/my-flask-app
  - keyword: "request"
```

#### 步骤 3: 追踪路由处理

```
工具: trace_function_flow
参数:
  - repo_path: /home/user/my-flask-app
  - function_name: handle_request
  - max_depth: 3
```

#### 步骤 4: 查找调用路径

```
工具: find_function_path
参数:
  - repo_path: /home/user/my-flask-app
  - from_function: wsgi_app
  - to_function: process_response
```

---

## 示例 3: 学习数据结构实现

### 对话示例

**你：** 我想学习 Redis 是如何实现哈希表的，能帮我分析一下吗？

#### 步骤 1: 扫描 Redis 源码

```
工具: scan_code_repository
参数:
  - repo_path: /home/user/redis
  - extensions: .c,.h
```

#### 步骤 2: 搜索哈希表相关函数

```
工具: search_functions
参数:
  - repo_path: /home/user/redis
  - keyword: "dictAdd"
```

#### 步骤 3: 分析哈希表概念

```
工具: analyze_code_concept
参数:
  - repo_path: /home/user/redis
  - concept: "哈希表实现"
  - keywords: "dictAdd,dictFind,dictReplace,dictDelete,dictResize"
```

#### 步骤 4: 生成概念流程图

```
工具: generate_concept_flowchart
参数:
  - repo_path: /home/user/redis
  - concept: "哈希表操作"
  - keywords: "dictAdd,dictFind,dictReplace,dictDelete"
  - direction: LR
```

#### 步骤 5: 查看具体实现

```
工具: get_function_code
参数:
  - repo_path: /home/user/redis
  - function_name: dictAdd
```

---

## 示例 4: 调试和理解现有代码

### 对话示例

**你：** 这个项目中，main 函数最终是怎么调用到 process_payment 函数的？中间经过了哪些步骤？

#### 直接使用 find_function_path

```
工具: find_function_path
参数:
  - repo_path: /home/user/my-project
  - from_function: main
  - to_function: process_payment
  - max_depth: 10
```

**返回结果：**
```json
{
  "status": "success",
  "from": "main",
  "to": "process_payment",
  "total_paths": 2,
  "paths": [
    ["main", "handle_order", "validate_order", "process_payment"],
    ["main", "handle_order", "retry_payment", "process_payment"]
  ],
  "flowchart": "...",
  "format": "mermaid"
}
```

**AI 会解释：**
> 找到了 2 条从 main 到 process_payment 的调用路径：
> 
> **路径 1（正常流程）：**
> main → handle_order → validate_order → process_payment
> 
> **路径 2（重试流程）：**
> main → handle_order → retry_payment → process_payment
> 
> [此处会显示可视化的流程图]

---

## 示例 5: 学习算法实现

### 对话示例

**你：** 我想学习快速排序的实现，这个代码库中的快速排序是如何实现的？

#### 步骤 1: 搜索快速排序函数

```
工具: search_functions
参数:
  - repo_path: /home/user/algorithms
  - keyword: "quicksort"
```

#### 步骤 2: 获取完整代码

```
工具: get_function_code
参数:
  - repo_path: /home/user/algorithms
  - function_name: quicksort
```

#### 步骤 3: 追踪调用流程

```
工具: trace_function_flow
参数:
  - repo_path: /home/user/algorithms
  - function_name: quicksort
  - max_depth: 5
```

#### 步骤 4: 生成流程图

```
工具: generate_flowchart
参数:
  - repo_path: /home/user/algorithms
  - function_name: quicksort
  - max_depth: 3
```

---

## 提示和技巧

### 1. 首次使用前必须扫描

在使用任何其他工具之前，必须先使用 `scan_code_repository` 扫描并索引代码库。

### 2. 控制流程图复杂度

对于大型项目，建议：
- 从较小的 `max_depth`（如 2-3）开始
- 逐步增加深度以获取更多细节
- 过深的追踪可能导致图表过于复杂

### 3. 使用合适的关键字

在分析概念时，选择精准的关键字可以获得更好的结果：
- **好的关键字**：具体的函数名、类型名（如 "kmalloc", "alloc_pages"）
- **避免的关键字**：过于通用的词（如 "get", "set"）

### 4. 组合使用多个工具

最好的学习效果来自于组合使用多个工具：
1. 先搜索相关函数
2. 再追踪具体流程
3. 最后生成可视化图表
4. 配合查看源代码

### 5. 针对不同语言调整扩展名

扫描时指定正确的扩展名可以提高效率：
- C/C++ 项目：`.c,.h,.cpp,.hpp`
- Python 项目：`.py`
- Java 项目：`.java`
- JavaScript 项目：`.js,.ts`

### 6. 处理大型代码库

对于像 Linux kernel 这样的大型代码库：
- 扫描可能需要几分钟时间，请耐心等待
- 可以通过指定特定目录（未来功能）来加速
- 建议在本地缓存索引结果（未来功能）

---

## 常见问题

### Q: 扫描失败或结果不准确？

**A:** 可能的原因：
1. 路径不存在或无权限访问
2. 代码使用了复杂的语法，正则表达式无法准确解析
3. 文件编码问题

### Q: 为什么找不到某些函数？

**A:** 可能的原因：
1. 函数是宏定义或内联函数
2. 函数在头文件中但未被索引
3. 函数名拼写错误
4. 需要扫描更多的文件扩展名

### Q: 流程图太复杂看不清？

**A:** 建议：
1. 减小 `max_depth` 参数
2. 使用 `LR`（左到右）方向代替 `TD`（上到下）
3. 专注于特定的子流程
4. 使用 `find_function_path` 查找特定路径

### Q: 支持哪些编程语言？

**A:** 当前版本支持：
- C/C++ (较好支持)
- Python (较好支持)
- Java, JavaScript (基础支持)

未来会添加更多语言支持。

---

## 高级用法

### 组合查询示例

**场景：** 深入理解 Linux 内核的进程调度机制

```
1. scan_code_repository(repo_path="/path/to/linux", extensions=".c,.h")

2. analyze_code_concept(
     concept="进程调度",
     keywords="schedule,pick_next_task,context_switch,__schedule"
   )

3. trace_function_flow(function_name="schedule", max_depth=4)

4. find_function_path(
     from_function="schedule",
     to_function="context_switch"
   )

5. generate_concept_flowchart(
     concept="调度流程",
     keywords="schedule,pick_next_task,context_switch"
   )

6. get_function_code(function_name="schedule")
7. get_function_code(function_name="context_switch")
```

这样可以全面了解进程调度的实现细节。

---

## 反馈和贡献

如果你有任何问题、建议或想贡献代码，欢迎：
- 提交 Issue
- 发起 Pull Request
- 分享你的使用案例

祝你学习愉快！🚀

