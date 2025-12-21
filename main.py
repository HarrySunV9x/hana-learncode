from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP("CodeLearnAssistant", json_response=True)

# 注册工具
from tool.create_tool import register_tools
register_tools(mcp)

# 注册资源
from resource.create_resource import register_resources
register_resources(mcp)

# 注册提示词
from prompt.create_prompt import register_prompts
register_prompts(mcp)


if __name__ == "__main__":
    mcp.run()
