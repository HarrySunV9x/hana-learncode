"""
MCP Resource 定义
提供静态或动态的数据资源（如文件、配置、数据等）
AI 可以读取但不能修改，只读访问
"""


def register_resources(mcp):
    """
    注册所有 resource 到 MCP 服务器
    
    Args:
        mcp: FastMCP 实例
    """
    
    @mcp.resource("resource://example")
    def resorce_example() -> str:
        """资源示例"""
        return "资源示例"