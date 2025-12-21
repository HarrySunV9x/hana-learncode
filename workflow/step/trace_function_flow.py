"""追踪函数调用流程步骤"""
from typing import Optional
from workflow.step.base_step import BaseStep, StepResult
from core.code_analyzer import CodeAnalyzer


class TraceFunctionFlowStep(BaseStep):
    """追踪函数调用流程步骤"""
    
    def __init__(self, workflow, function_name: Optional[str] = None, max_depth: int = 3):
        super().__init__("trace_function_flow", "追踪函数调用流程", workflow)
        self.function_name = function_name
        self.max_depth = max_depth
    
    def validate_parameters(self, context: dict) -> bool:
        """校验参数"""
        return "indexer" in context
    
    def execute(self, context: dict) -> StepResult:
        """执行追踪函数流程步骤"""
        try:
            indexer = context["indexer"]
            analyzer = CodeAnalyzer(indexer)
            context["analyzer"] = analyzer
            
            # 获取要追踪的函数名
            function_name = context.get("trace_function", self.function_name)
            
            if not function_name:
                # 如果没有指定函数名，尝试从搜索结果中获取第一个
                found_functions = context.get("found_functions", [])
                if found_functions:
                    function_name = found_functions[0]["name"]
                else:
                    return StepResult(
                        success=False,
                        message="未指定要追踪的函数名",
                        data={}
                    )
            
            # 追踪函数流程
            flow = analyzer.trace_function_flow(function_name, self.max_depth)
            
            if "error" in flow:
                return StepResult(
                    success=False,
                    message=f"追踪函数流程失败：{flow['error']}",
                    data=flow
                )
            
            # 保存到 context
            context["function_flow"] = flow
            context["traced_function"] = function_name
            
            return StepResult(
                success=True,
                message=f"成功追踪函数 '{function_name}' 的调用流程",
                data={
                    "function": function_name,
                    "file": flow.get("file", ""),
                    "line": flow.get("line", 0),
                    "depth": self.max_depth
                },
                next_step="generate_flowchart"  # 生成流程图
            )
        except Exception as e:
            return StepResult(
                success=False,
                message=f"追踪函数流程失败：{str(e)}",
                data={"error": str(e)}
            )
