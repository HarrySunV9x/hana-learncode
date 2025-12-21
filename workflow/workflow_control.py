from abc import abstractmethod
from enum import Enum
from typing import Dict, Optional
import time

from .step.base_step import BaseStep

class WorkflowStatus(Enum):
    """ 工作流状态 """
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class Workflow:
    """ 工作流类 """
    def __init__(self, workflow_id: str, workflow_name: str, workflow_description: str):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        self.status = WorkflowStatus.INITIALIZED
        self.steps = []
        self.current_step_index = 0
        self.start_time = time.time()
        self.end_time = None

    def add_step(self, step: BaseStep):
        """ 添加步骤 """
        self.steps.append(step)

    def get_current_step(self) -> Optional[BaseStep]:
        """ 获取当前步骤 """
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        else:
            return None

    def next_step(self) -> Optional[BaseStep]:
        """ 前进到下一个步骤 """
        if self.current_step_index + 1 < len(self.steps):
            self.current_step_index += 1
            return self.steps[self.current_step_index]
        else:
            return None

    def get_workflow_status(self) -> Dict:
        """ 获取工作流状态 """
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_description": self.workflow_description,
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "steps": [step.get_name() for step in self.steps],
            "start_time": self.start_time,
            "end_time": self.end_time
        }

