# 步骤基类 —— 用于步骤实现的基类
# 每个步骤都应该按以下顺序执行
# 1. 工具流初始化校验
# 2. 参数校验
# 3. 步骤执行
# 4. 报告生成（可选）
# 5. 步骤返回 （工具类/分析类，指明下一步）
from abc import abstractmethod


class BaseStep:
    """ 步骤基类，所有步骤集成此类 """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """ 执行步骤 """
        pass

    def get_name(self) -> str:
        """ 获取步骤名称 """
        return self.name

