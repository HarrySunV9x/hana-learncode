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
        self.steps_map = {}  # 步骤名称到步骤对象的映射（保持插入顺序）
        self.current_step_index = 0
        self.expected_next_step = None  # 预期的下一步步骤名称
        self.start_time = time.time()
        self.end_time = None

    def add_step(self, step: BaseStep):
        """ 添加步骤 """
        self.steps_map[step.get_name()] = step
    
    @property
    def steps(self) -> list:
        """ 获取步骤列表（按插入顺序） """
        return list(self.steps_map.values())

    def get_current_step(self) -> Optional[BaseStep]:
        """ 获取当前步骤 """
        steps_list = self.steps
        if 0 <= self.current_step_index < len(steps_list):
            return steps_list[self.current_step_index]
        else:
            return None

    def next_step(self) -> Optional[BaseStep]:
        """ 前进到下一个步骤 """
        steps_list = self.steps
        if self.current_step_index + 1 < len(steps_list):
            self.current_step_index += 1
            return steps_list[self.current_step_index]
        else:
            return None
    
    def set_expected_next_step(self, step_name: str):
        """ 设置预期的下一步步骤名称 """
        self.expected_next_step = step_name
    
    def get_expected_next_step(self) -> Optional[str]:
        """ 获取预期的下一步步骤名称 """
        return self.expected_next_step
    
    def jump_to_step(self, step_name: str) -> Optional[BaseStep]:
        """ 跳转到指定步骤 """
        if step_name in self.steps_map:
            step = self.steps_map[step_name]
            # 找到该步骤在列表中的索引
            steps_list = self.steps
            for i, s in enumerate(steps_list):
                if s.get_name() == step_name:
                    self.current_step_index = i
                    return step
        return None
    
    def get_status(self) -> WorkflowStatus:
        """ 获取工作流运行状态 """
        return self.status
    
    def set_status(self, status: WorkflowStatus):
        """ 设置工作流状态 """
        self.status = status

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

