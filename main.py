from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP("CodeLearnAssistant", json_response=True)

# 注册工具
from tool.create_tool import register_tools
register_tools(mcp)

@mcp.resource("weather://beijing")
def beijing_weather() -> str:
    """北京的天气数据"""
    return "北京：25°C，晴天，空气质量：良"

@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    # 这里会真正执行查询操作
    if city == "北京":
        return "北京：25°C，晴天，空气质量：良"
    elif city == "上海":
        return "上海：28°C，多云，空气质量：优"
    else:
        return f"无法查询{city}的天气"

@mcp.prompt()
def weather_report(city: str) -> str:
    """生成天气播报任务"""
    return f"请扮演气象主播，用专业且生动的语言播报{city}的天气情况，包括温度、天气状况和出行建议。"


if __name__ == "__main__":
    mcp.run()
