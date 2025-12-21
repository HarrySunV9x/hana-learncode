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
    
    @mcp.resource("weather://beijing")
    def beijing_weather() -> str:
        """北京的天气数据"""
        return "北京：25°C，晴天，空气质量：良"
    
    # 可以在这里添加更多 resource 定义
    # 例如：
    # @mcp.resource("config://{name}")
    # def get_config(name: str) -> str:
    #     """获取配置数据"""
    #     return config_data

