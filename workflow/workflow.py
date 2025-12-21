"""
工作流管理器
用于管理多个工作流实例、执行步骤、状态追踪等
"""
from typing import Dict, Optional, Any, Callable
import uuid
import json
from .workflow_control import Workflow, WorkflowStatus
from .base_step import BaseStep


class Workflow:
    """工作流类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_contexts: Dict[str, Dict[str, Any]] = {}
        self._initialized = True
    
    def create_workflow(self, workflow_name: str, workflow_description: str) -> str:
        """
        创建新的工作流
        
        Args:
            workflow_name: 工作流名称
            workflow_description: 工作流描述
            
        Returns:
            workflow_id: 工作流唯一标识符
        """
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(workflow_id, workflow_name, workflow_description)
        self.workflows[workflow_id] = workflow
        self.workflow_contexts[workflow_id] = {}
        
        return workflow_id
    
    def add_step(self, workflow_id: str, step: BaseStep) -> Dict[str, Any]:
        """
        向工作流添加步骤
        
        Args:
            workflow_id: 工作流ID
            step: 步骤实例
            
        Returns:
            操作结果
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        workflow = self.workflows[workflow_id]
        workflow.add_step(step)
        
        return {
            "status": "success",
            "message": f"成功添加步骤: {step.get_name()}",
            "total_steps": len(workflow.steps)
        }
    
    def execute_next_step(self, workflow_id: str) -> Dict[str, Any]:
        """
        执行工作流的下一个步骤
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            步骤执行结果
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        workflow = self.workflows[workflow_id]
        context = self.workflow_contexts[workflow_id]
        
        # 获取当前步骤
        current_step = workflow.get_current_step()
        
        if not current_step:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.end_time = None
            return {
                "status": "completed",
                "message": "所有步骤已执行完成"
            }
        
        try:
            # 更新工作流状态
            workflow.status = WorkflowStatus.RUNNING
            
            # 执行步骤
            step_result = current_step.execute(context)
            
            # 检查执行结果
            if step_result.get("status") == "error":
                workflow.status = WorkflowStatus.FAILED
                return {
                    "status": "error",
                    "step": current_step.get_name(),
                    "error": step_result.get("error"),
                    "workflow_status": workflow.get_workflow_status()
                }
            
            # 移动到下一步
            next_step = workflow.next_step()
            
            if not next_step:
                # 所有步骤完成
                workflow.status = WorkflowStatus.COMPLETED
                import time
                workflow.end_time = time.time()
            
            return {
                "status": "success",
                "step": current_step.get_name(),
                "step_result": step_result,
                "workflow_status": workflow.get_workflow_status(),
                "next_step": next_step.get_name() if next_step else None
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            return {
                "status": "error",
                "step": current_step.get_name(),
                "error": str(e),
                "workflow_status": workflow.get_workflow_status()
            }
    
    def execute_all_steps(self, workflow_id: str) -> Dict[str, Any]:
        """
        执行工作流的所有步骤
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            所有步骤的执行结果
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        workflow = self.workflows[workflow_id]
        results = []
        
        while True:
            result = self.execute_next_step(workflow_id)
            results.append(result)
            
            if result["status"] == "completed" or result["status"] == "error":
                break
        
        return {
            "status": "success" if workflow.status == WorkflowStatus.COMPLETED else "error",
            "workflow_id": workflow_id,
            "total_steps": len(workflow.steps),
            "results": results,
            "workflow_status": workflow.get_workflow_status()
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流状态
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流状态信息
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        workflow = self.workflows[workflow_id]
        status = workflow.get_workflow_status()
        
        # 添加当前步骤信息
        current_step = workflow.get_current_step()
        if current_step:
            status["current_step"] = {
                "name": current_step.get_name(),
                "description": current_step.description
            }
        
        return {
            "status": "success",
            "workflow_status": status
        }
    
    def get_workflow_context(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流上下文
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流上下文
        """
        if workflow_id not in self.workflow_contexts:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        context = self.workflow_contexts[workflow_id]
        
        # 过滤掉不可序列化的对象
        serializable_context = {}
        for key, value in context.items():
            if key not in ['indexer', 'analyzer']:  # 跳过这些复杂对象
                try:
                    json.dumps(value)
                    serializable_context[key] = value
                except (TypeError, ValueError):
                    serializable_context[key] = str(type(value))
        
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "context": serializable_context
        }
    
    def list_workflows(self) -> Dict[str, Any]:
        """
        列出所有工作流
        
        Returns:
            所有工作流的列表
        """
        workflow_list = []
        
        for workflow_id, workflow in self.workflows.items():
            workflow_list.append({
                "workflow_id": workflow_id,
                "workflow_name": workflow.workflow_name,
                "workflow_description": workflow.workflow_description,
                "status": workflow.status.value,
                "total_steps": len(workflow.steps),
                "current_step_index": workflow.current_step_index
            })
        
        return {
            "status": "success",
            "total_workflows": len(workflow_list),
            "workflows": workflow_list
        }
    
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            操作结果
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        del self.workflows[workflow_id]
        del self.workflow_contexts[workflow_id]
        
        return {
            "status": "success",
            "message": f"成功删除工作流: {workflow_id}"
        }
    
    def pause_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        暂停工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            操作结果
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.PAUSED
        
        return {
            "status": "success",
            "message": f"工作流已暂停",
            "workflow_status": workflow.get_workflow_status()
        }
    
    def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        恢复工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            操作结果
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": f"工作流 {workflow_id} 不存在"
            }
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PAUSED:
            return {
                "status": "error",
                "error": "只能恢复已暂停的工作流"
            }
        
        workflow.status = WorkflowStatus.RUNNING
        
        return {
            "status": "success",
            "message": f"工作流已恢复",
            "workflow_status": workflow.get_workflow_status()
        }


# 创建全局实例
workflow_manager = WorkflowManager()

