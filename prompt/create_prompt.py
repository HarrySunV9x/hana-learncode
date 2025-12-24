"""
MCP Prompt 定义
用户手动选择使用，在 cursor 中，输入/可见
返回的是提示词文本，不是执行结果
用于引导 AI 完成特定任务
"""
from typing import Optional

from core.logger import get_logger

logger = get_logger("prompts")


def register_prompts(mcp):
    """
    注册所有 prompt 到 MCP 服务器
    
    Args:
        mcp: FastMCP 实例
    """
    
    @mcp.prompt()
    def learn_code(code_path: str, topic: str) -> str:
        """
        学习代码 - 通用代码学习提示词
        
        Args:
            code_path: 代码仓库路径
            topic: 要学习的主题或功能
        """
        return f"""# 代码学习任务

## 目标
帮我学习和理解代码，主题：**{topic}**

## 代码位置
{code_path}

调用 init_learn_code_workflow 初始化工作流。
"""
