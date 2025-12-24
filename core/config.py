"""配置管理模块"""
import os
from typing import List, Optional


class Config:
    """项目配置"""

    # 代码扫描配置
    DEFAULT_EXTENSIONS: List[str] = [
        ".py",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".java",
        ".js",
        ".ts",
        ".go",
        ".rs",
    ]

    # 忽略模式（可用于文件/目录）
    IGNORE_PATTERNS: List[str] = [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.o",
        "*.a",
        "*.exe",
        ".DS_Store",
        "Thumbs.db",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "target",
        "*.egg-info",
    ]

    # 工作流/分析配置
    MAX_TRACE_DEPTH: int = 5
    MAX_SEARCH_RESULTS: int = 50
    MAX_SNIPPET_LENGTH: int = 500
    SESSION_TIMEOUT: int = 3600

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)

    # MCP 服务器名称
    SERVER_NAME: str = "CodeLearnAssistant"

    @classmethod
    def get_extensions(cls, custom: Optional[List[str]] = None) -> List[str]:
        """返回要扫描的扩展名列表，支持环境/参数覆盖。"""
        if custom:
            return custom
        env_ext = os.getenv("CODE_EXTENSIONS")
        if env_ext:
            return [ext.strip() for ext in env_ext.split(",") if ext.strip()]
        return cls.DEFAULT_EXTENSIONS

    @classmethod
    def get_ignore_patterns(cls, additional: Optional[List[str]] = None) -> List[str]:
        """返回忽略模式列表，允许追加自定义模式。"""
        patterns = cls.IGNORE_PATTERNS.copy()
        if additional:
            patterns.extend(additional)
        return patterns


config = Config()

