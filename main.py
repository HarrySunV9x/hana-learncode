from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP("CodeLearnAssistant", json_response=True)

# 注册工具
from tool.create_tool import register_tools
register_tools(mcp)

if __name__ == "__main__":
    mcp.run()
