# 快速开始指南

## 5 分钟快速上手

### 步骤 1: 安装依赖

```bash
cd F:\Code\hana-learncode
uv sync
```

或使用 pip：

```bash
pip install -e .
```

### 步骤 2: 测试运行

```bash
uv run main.py
```

或：

```bash
python main.py
```

看到类似输出表示成功：
```
MCP Server running on stdio
```

按 `Ctrl+C` 停止服务器。

### 步骤 3: 配置 Claude Desktop

1. 找到 Claude Desktop 的配置文件：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. 编辑配置文件，添加以下内容（根据你的实际路径调整）：

**使用 uv（推荐）：**
```json
{
  "mcpServers": {
    "code-learning": {
      "command": "uv",
      "args": [
        "run",
        "F:\\Code\\hana-learncode\\main.py"
      ]
    }
  }
}
```

**使用 Python：**
```json
{
  "mcpServers": {
    "code-learning": {
      "command": "python",
      "args": [
        "F:\\Code\\hana-learncode\\main.py"
      ]
    }
  }
}
```

**注意：** 
- Windows 路径使用双反斜杠 `\\` 或单正斜杠 `/`
- macOS/Linux 路径使用正斜杠 `/`

### 步骤 4: 重启 Claude Desktop

关闭并重新打开 Claude Desktop 应用。

### 步骤 5: 验证安装

在 Claude Desktop 中，你应该看到一个工具图标或提示，表明 MCP 服务器已连接。

尝试发送以下消息：

```
你好！请帮我扫描这个代码库：F:\Code\hana-learncode
```

如果 Claude 开始调用工具并返回扫描结果，说明安装成功！

---

## 第一个完整示例

让我们尝试分析这个项目本身：

### 1. 扫描项目

**你说：**
```
请帮我扫描并分析这个项目：F:\Code\hana-learncode
```

### 2. 查看有哪些函数

**你说：**
```
这个项目中有哪些函数包含 "index" 关键字？
```

### 3. 追踪函数调用

**你说：**
```
请追踪 scan_repository 函数的调用流程，并生成流程图
```

### 4. 查看源代码

**你说：**
```
请展示 scan_repository 函数的完整代码
```

---

## 学习真实项目示例

### 示例：学习 Flask 源码

假设你已经克隆了 Flask 源码到 `/path/to/flask`

**你说：**
```
我想学习 Flask 是如何处理 HTTP 请求的。
请帮我分析这个 Flask 源码：/path/to/flask/src/flask

步骤：
1. 先扫描代码库
2. 搜索处理请求相关的函数
3. 追踪请求处理流程
4. 生成流程图
```

Claude 会自动：
1. 扫描 Flask 源码
2. 找到 `wsgi_app`, `full_dispatch_request` 等关键函数
3. 追踪它们的调用关系
4. 生成可视化的流程图
5. 解释整个请求处理流程

---

## 常见使用模式

### 模式 1: 快速理解某个功能

```
提问模板：
这个项目的 [功能名] 是如何实现的？
代码路径：[本地路径]
```

例如：
```
这个项目的用户认证是如何实现的？
代码路径：F:\MyProjects\web-app
```

### 模式 2: 学习特定算法或机制

```
提问模板：
我想学习 [项目名] 中 [算法/机制] 的实现原理，
能通过源码告诉我整个过程吗？并生成流程图。
代码地址在：[本地路径]
```

例如：
```
我想学习 Redis 中哈希表的实现原理，
能通过源码告诉我整个过程吗？并生成流程图。
代码地址在：F:\opensource\redis
```

### 模式 3: 追踪函数调用链

```
提问模板：
在 [项目路径] 中，[函数A] 是如何调用到 [函数B] 的？
能展示完整的调用路径吗？
```

例如：
```
在 F:\MyProjects\app 中，main 函数是如何调用到 process_data 的？
能展示完整的调用路径吗？
```

### 模式 4: 分析代码结构

```
提问模板：
请帮我分析 [项目路径] 的代码结构，
重点关注 [关键字1, 关键字2, 关键字3] 相关的部分
```

例如：
```
请帮我分析 F:\opensource\nginx 的代码结构，
重点关注 http_process, ngx_event, ngx_connection 相关的部分
```

---

## 故障排除

### 问题 1: Claude Desktop 没有显示工具

**解决方案：**
1. 检查配置文件路径是否正确
2. 确保 JSON 格式正确（使用 JSON 验证器）
3. 完全退出并重启 Claude Desktop（不是最小化）
4. 查看 Claude Desktop 的日志文件

### 问题 2: 工具调用失败

**解决方案：**
1. 手动运行 `uv run main.py` 检查是否有错误
2. 确保所有依赖已安装：`uv sync`
3. 检查 Python 版本（需要 3.13+）
4. 尝试使用绝对路径

### 问题 3: 扫描代码库失败

**解决方案：**
1. 检查路径是否存在
2. 确保有读取权限
3. 如果路径包含空格，确保在配置中正确转义
4. Windows 路径使用双反斜杠或正斜杠

### 问题 4: 性能问题

**解决方案：**
1. 对于大型代码库，首次扫描可能需要几分钟
2. 减小 `max_depth` 参数
3. 使用更精确的文件扩展名过滤

---

## 下一步

- 📖 阅读完整文档：[README.md](README.md)
- 💡 查看详细示例：[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- 🔧 了解项目结构和技术细节

## 获取帮助

- GitHub Issues: [提交问题]
- 文档问题：查看 README 和 USAGE_EXAMPLES
- 功能建议：欢迎提 PR！

祝你学习愉快！🎉

