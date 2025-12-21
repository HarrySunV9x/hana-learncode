"""工作流管理器 - 单例模式管理所有工作流"""
from typing import Optional, Dict
from workflow.workflow import Workflow, WorkflowStatus


class WorkflowManager:
    """工作流管理器（单例模式）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._workflows: Dict[str, Workflow] = {}
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'WorkflowManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def create_workflow(self, workflow_id: str, workflow_name: str, workflow_description: str) -> Workflow:
        """创建新的工作流"""
        workflow = Workflow(workflow_id, workflow_name, workflow_description)
        self._workflows[workflow_id] = workflow
        return workflow
    
    def add_workflow(self, workflow: Workflow) -> None:
        """添加工作流"""
        self._workflows[workflow.workflow_id] = workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self._workflows.get(workflow_id)
    
    def remove_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False
    
    def list_workflows(self) -> Dict[str, Dict]:
        """列出所有工作流"""
        return {
            wf_id: wf.get_workflow_status()
            for wf_id, wf in self._workflows.items()
        }
    
    def get_workflow_count(self) -> int:
        """获取工作流数量"""
        return len(self._workflows)


# 全局实例
workflow_manager = WorkflowManager.get_instance()