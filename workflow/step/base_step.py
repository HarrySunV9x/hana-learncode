# 步骤基类 —— 用于步骤实现的基类
# 每个步骤都应该按以下顺序执行
# 1. 工具流初始化校验
# 2. 参数校验
# 3. 步骤执行
# 4. 报告生成（可选）
# 5. 步骤返回 （工具类/分析类，指明下一步）
from abc import abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING

# 避免循环导入：只在类型检查时导入
if TYPE_CHECKING:
    from workflow.workflow import Workflow, WorkflowStatus


class StepResult:
    """ 步骤执行结果 """
    def __init__(self, success: bool, message: str, data: Optional[Dict[Any, Any]] = None, next_step: Optional[str] = None):
        self.success = success  # 是否成功
        self.message = message  # 返回消息
        self.data = data or {}  # 执行结果数据
        self.next_step = next_step  # 指定下一步步骤名称（可选）


class BaseStep:
    """ 步骤基类，所有步骤集成此类 """
    def __init__(self, name: str, description: str, workflow: "Workflow"):
        self.name = name
        self.description = description
        self.workflow = workflow

    @abstractmethod
    def validate_parameters(self, context: dict) -> bool:
        """ 校验步骤参数 """
        pass

    @abstractmethod
    def execute(self, context: dict) -> StepResult:
        """ 执行步骤，返回StepResult对象 """
        pass

    def get_name(self) -> str:
        """ 获取步骤名称 """
        return self.name
    
    def format_result(self, result: StepResult) -> str:
        """
        格式化步骤执行结果为字符串（MCP tool 返回格式）
        
        格式：
        ═══════════════════════════════════
        📋 步骤：{步骤名称}
        ═══════════════════════════════════
        
        ✅/❌ 执行结果：
        {执行结果消息}
        
        📊 执行数据：
        {数据详情}
        
        ➡️ 下一步：
        执行 {下一步步骤名} 步骤
        ═══════════════════════════════════
        """
        lines = []
        lines.append("═" * 40)
        lines.append(f"📋 步骤：{self.name}")
        lines.append("═" * 40)
        lines.append("")
        
        # 执行结果
        status_icon = "✅" if result.success else "❌"
        lines.append(f"{status_icon} 执行结果：")
        lines.append(f"  {result.message}")
        lines.append("")
        
        # 执行数据（如果有）
        if result.data:
            lines.append("📊 执行数据：")
            for key, value in result.data.items():
                lines.append(f"  • {key}: {value}")
            lines.append("")
        
        # 下一步（如果有）
        if result.success and result.next_step:
            lines.append("➡️ 下一步：")
            lines.append(f"  执行 [{result.next_step}] 步骤")
        elif result.success:
            lines.append("✓ 工作流完成")
        
        lines.append("═" * 40)
        
        return "\n".join(lines)

    def run(self, context: dict) -> str:
        """
        执行步骤
        返回：格式化的字符串结果（用于 MCP tool）
        """
        # 1. 如果有 workflow，进行工作流相关校验
        if self.workflow is not None:
            if self.workflow.get_status().value != "running":
                return self._format_error(f"工作流状态不正确，当前状态：{self.workflow.get_status().value}")

            # 校验当前步骤是否是 workflow 的当前步骤
            current_step = self.workflow.get_current_step()
            if current_step != self:
                current_name = current_step.get_name() if current_step else "None"
                return self._format_error(
                    f"工作流步骤不匹配\n"
                    f"  • 当前应执行步骤：{current_name}\n"
                    f"  • 实际尝试执行：{self.name}"
                )
        
        # 3. 校验步骤参数
        if not self.validate_parameters(context):
            return self._format_error("参数校验失败，请检查输入参数")

        # 4. 执行步骤
        result = self.execute(context)

        # 5. 如果有 workflow，更新工作流状态
        if self.workflow is not None and result.success:
            if result.next_step:
                self.workflow.set_expected_next_step(result.next_step)
                self.workflow.jump_to_step(result.next_step)
            else:
                self.workflow.next_step()
        
        # 6. 格式化并返回结果
        return self.format_result(result)
    
    def _format_error(self, error_message: str) -> str:
        """ 格式化错误消息 """
        lines = []
        lines.append("═" * 40)
        lines.append(f"📋 步骤：{self.name}")
        lines.append("═" * 40)
        lines.append("")
        lines.append("❌ 执行失败：")
        lines.append(f"  {error_message}")
        lines.append("")
        lines.append("═" * 40)
        return "\n".join(lines)
