"""
MCP Prompt 定义
用户手动选择使用，在 cursor 中，输入/可见
返回的是提示词文本，不是执行结果
用于引导 AI 完成特定任务
"""


def register_prompts(mcp):
    """
    注册所有 prompt 到 MCP 服务器
    
    Args:
        mcp: FastMCP 实例
    """
    
    @mcp.prompt()
    def weather_report(city: str) -> str:
        """生成天气播报任务"""
        return f"请扮演气象主播，用专业且生动的语言播报{city}的天气情况，包括温度、天气状况和出行建议。"
    
    # 可以在这里添加更多 prompt 定义
    # 例如：
    # @mcp.prompt()
    # def code_review_prompt(file_path: str) -> str:
    #     """代码审查提示词"""
    #     return f"请审查以下代码文件：{file_path}，重点关注代码质量、性能和安全性。"

