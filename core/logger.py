"""日志系统模块"""
import logging
import sys
from typing import Optional

from core.config import config


def setup_logger(
    name: str = "hana-learncode",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """配置统一的 logger，支持控制台 + 可选文件输出。"""
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    log_level = getattr(logging, (level or config.LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(config.LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_path = log_file or config.LOG_FILE
    if file_path:
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 默认 logger 实例
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """获取模块子 logger。"""
    return logging.getLogger(f"hana-learncode.{name}")

