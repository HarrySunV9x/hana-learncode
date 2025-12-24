"""
工作流集（Registry）

目标：
- 统一管理「工作流类型」与「会话(Workflow Session)」
- 让 init_workflow 既能注册工作流到工作流集，也能创建会话并装配步骤
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Dict, List, Optional, Tuple
from uuid import uuid4


class StepType(Enum):
    """步骤类型"""

    REQUIRED = "required"  # 必经步骤，只能执行一次（或不可跳过）
    REPEATABLE = "repeatable"  # 可重复步骤（可在当前位置动态插入）
    FINAL = "final"  # 终结步骤


@dataclass
class Step:
    """步骤定义（轻量元数据）"""

    name: str
    step_type: StepType
    executed: bool = False


@dataclass
class WorkflowDefinition:
    """工作流定义（工作流类型）"""

    workflow_type: str
    name: str
    description: str
    steps: List[str]


@dataclass
class WorkflowSession:
    """工作流会话（每次 init 产生一个 session）"""

    session_id: str
    workflow_type: str
    steps: List[Step] = field(default_factory=list)
    current_index: int = 0
    context: dict = field(default_factory=dict)

    def get_current_step(self) -> Optional[Step]:
        if 0 <= self.current_index < len(self.steps):
            return self.steps[self.current_index]
        return None

    def advance(self) -> None:
        if self.current_index < len(self.steps):
            self.steps[self.current_index].executed = True
            self.current_index += 1

    def insert_step(self, step: Step) -> None:
        """在当前位置插入步骤（用于 repeatable）"""
        self.steps.insert(self.current_index, step)

    def is_completed(self) -> bool:
        return self.current_index >= len(self.steps)

    def get_status(self) -> dict:
        return {
            "workflow_type": self.workflow_type,
            "current_index": self.current_index,
            "total_steps": len(self.steps),
            "current_step": self.get_current_step().name if self.get_current_step() else None,
            "steps": [(s.name, "✓" if s.executed else "○") for s in self.steps],
        }


class WorkflowRegistry:
    """工作流集：注册工作流类型 + 管理会话"""

    def __init__(self) -> None:
        self._definitions: Dict[str, WorkflowDefinition] = {}
        self._sessions: Dict[str, WorkflowSession] = {}

    # ---------- 工作流类型 ----------
    def register(self, definition: WorkflowDefinition) -> None:
        # 注册前校验步骤类型配置是否存在，避免运行期缺失
        for step_name in definition.steps:
            if step_name not in _STEP_CONFIG:
                raise ValueError(f"未配置步骤类型: {step_name}")
        self._definitions[definition.workflow_type] = definition

    def has_definition(self, workflow_type: str) -> bool:
        return workflow_type in self._definitions

    def get_definition(self, workflow_type: str) -> Optional[WorkflowDefinition]:
        return self._definitions.get(workflow_type)

    def list_definitions(self) -> List[WorkflowDefinition]:
        return list(self._definitions.values())

    # ---------- 会话 ----------
    def create_session(
        self,
        workflow_type: str,
        *,
        session_prefix: str = "learn_code",
        context: Optional[dict] = None,
    ) -> WorkflowSession:
        definition = self.get_definition(workflow_type)
        if not definition:
            raise ValueError(f"未注册工作流类型: {workflow_type}")

        session_id = f"{session_prefix}_{uuid4().hex}"
        steps = [Step(name=s, step_type=_STEP_CONFIG[s]) for s in definition.steps]
        session = WorkflowSession(
            session_id=session_id,
            workflow_type=workflow_type,
            steps=steps,
            context=context or {},
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[WorkflowSession]:
        return list(self._sessions.values())

    def sessions_map(self) -> Dict[str, WorkflowSession]:
        """给 resource/调试用：返回原始 dict 视图（不要在外部修改）"""
        return self._sessions


# ---------- 默认步骤配置（单一事实来源） ----------
_STEP_CONFIG: Dict[str, StepType] = {
    "scan_repository": StepType.REQUIRED,
    "search_functions": StepType.REPEATABLE,
    "trace_function_flow": StepType.REPEATABLE,
    "analyze_concept": StepType.REPEATABLE,
    "generate_flowchart": StepType.FINAL,
}


def get_step_type(step_name: str) -> Optional[StepType]:
    return _STEP_CONFIG.get(step_name)


# 全局单例：整个 MCP Server 进程共享
workflow_registry = WorkflowRegistry()


