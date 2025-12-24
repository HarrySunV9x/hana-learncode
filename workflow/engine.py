"""
工作流引擎：严格按步骤执行（并支持 repeatable 步骤在当前位置动态插入）

说明：
- “严格”体现在：不可跳过 REQUIRED / FINAL 步骤；必须从 current_step 开始推进
- “repeatable” 体现在：当用户请求执行可重复步骤时，允许在 current_index 插入该步骤后执行
"""

from __future__ import annotations

from typing import Optional, Tuple

from workflow.registry import Step, StepType, WorkflowSession, get_step_type


def try_execute_step(session: WorkflowSession, step_name: str) -> Tuple[bool, Optional[str]]:
    """
    尝试执行步骤，做顺序校验/必要时插入 repeatable 步骤。

    Returns:
        (can_execute, error_message)
    """
    current = session.get_current_step()

    if session.is_completed():
        return False, _format_engine_error(
            "工作流已完成",
            "所有步骤已执行完毕\n如需继续分析，请创建新会话",
        )

    # 情况1：当前步骤就是要执行的步骤
    if current and current.name == step_name:
        return True, None

    # 情况2：要执行的是可重复步骤：允许插入到当前位置
    step_type = get_step_type(step_name)
    if step_type == StepType.REPEATABLE:
        # 前置条件：必须先 scan_repository（用 indexer 是否存在作为事实）
        if not session.context.get("indexer"):
            return False, _format_engine_error(
                f"无法执行 {step_name}",
                "请先完成 scan_repository 步骤",
            )
        session.insert_step(Step(name=step_name, step_type=StepType.REPEATABLE))
        return True, None

    # 情况3：不允许的跳步
    return False, _format_engine_error(
        "步骤顺序错误",
        f"当前应执行: {current.name if current else 'None'}\n尝试执行: {step_name}\n\n请按顺序执行步骤",
    )


def _format_engine_error(title: str, message: str) -> str:
    # 这里不依赖 tool 层的格式化函数，避免循环依赖
    lines = ["═" * 45, f"❌ {title}", "═" * 45, ""]
    for line in message.split("\n"):
        lines.append(f"  {line}")
    lines.append("")
    lines.append("═" * 45)
    return "\n".join(lines)


