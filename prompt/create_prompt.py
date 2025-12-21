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
    def learn_code(code_path: str, learn_context: str) -> str:
        """学习代码"""
        return f"帮我学习代码，我想学习{learn_context}，代码文件：{code_path}"

    @mcp.prompt()
    def learn_code_for_kernel(learn_context: str) -> str:
        """学习内核代码上下文"""
        return f"帮我学习内核代码，我想学习{learn_context}，内核代码地址：F:/Code/kernel/common"
