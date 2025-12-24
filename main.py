"""
CodeLearnAssistant - MCP 代码学习助手

优化设计：工作流集(Registry) + 引擎(Engine) 严格按步骤执行
"""
from mcp.server.fastmcp import FastMCP

from core.config import config
from core.logger import logger

# 创建 MCP 服务器
mcp = FastMCP(config.SERVER_NAME, json_response=True)

# 注册工具
from tool.create_tool import register_tools
register_tools(mcp)

# 注册资源
from resource.create_resource import register_resources
register_resources(mcp)

# 注册提示词
from prompt.create_prompt import register_prompts
register_prompts(mcp)

logger.info(f"MCP 服务器 '{config.SERVER_NAME}' 初始化完成")


if __name__ == "__main__":
    mcp.run()
