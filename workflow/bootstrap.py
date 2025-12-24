"""
工作流注册入口（init_workflow 的“注册阶段”）

约定：
- 该模块只负责把工作流类型注册到 workflow_registry
- 可被多次调用，必须幂等
"""

from __future__ import annotations

from workflow.registry import WorkflowDefinition, workflow_registry


def init_workflows() -> None:
    """注册内置工作流类型（幂等）"""

    # learn_code：默认学习/追踪链路
    workflow_registry.register(
        WorkflowDefinition(
            workflow_type="learn_code",
            name="代码学习",
            description="扫描代码库 -> 搜索函数 -> 追踪调用 -> 生成流程图（可动态插入可重复步骤）",
            steps=[
                "scan_repository",
                "search_functions",
                "trace_function_flow",
                "generate_flowchart",
            ],
        )
    )


