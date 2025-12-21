"""生成流程图步骤"""
from typing import Optional
from workflow.step.base_step import BaseStep, StepResult
from core.flowchart_generator import FlowchartGenerator


class GenerateFlowchartStep(BaseStep):
    """生成流程图步骤"""
    
    def __init__(self, workflow, chart_type: str = "call_tree", direction: str = "TD"):
        super().__init__("generate_flowchart", "生成流程图", workflow)
        self.chart_type = chart_type
        self.direction = direction
    
    def validate_parameters(self, context: dict) -> bool:
        """校验参数"""
        # 需要至少有函数流程或概念分析结果
        return "function_flow" in context or "concept_analysis" in context
    
    def execute(self, context: dict) -> StepResult:
        """执行生成流程图步骤"""
        try:
            generator = FlowchartGenerator()
            
            chart_type = context.get("chart_type", self.chart_type)
            direction = context.get("direction", self.direction)
            
            flowchart = ""
            chart_info = {}
            
            if chart_type == "call_tree" and "function_flow" in context:
                # 生成函数调用树流程图
                flow = context["function_flow"]
                flowchart = generator.generate_call_tree_flowchart(flow["call_tree"], direction)
                chart_info = {
                    "type": "call_tree",
                    "function": flow.get("function", ""),
                    "file": flow.get("file", "")
                }
            
            elif chart_type == "concept" and "concept_analysis" in context:
                # 生成概念分析流程图
                analysis = context["concept_analysis"]
                flowchart = generator.generate_concept_flowchart(analysis, direction)
                chart_info = {
                    "type": "concept",
                    "concept": analysis.get("concept", ""),
                    "total_functions": analysis.get("total_functions", 0)
                }
            
            else:
                # 尝试智能选择
                if "function_flow" in context:
                    flow = context["function_flow"]
                    flowchart = generator.generate_call_tree_flowchart(flow["call_tree"], direction)
                    chart_info = {
                        "type": "call_tree",
                        "function": flow.get("function", "")
                    }
                elif "concept_analysis" in context:
                    analysis = context["concept_analysis"]
                    flowchart = generator.generate_concept_flowchart(analysis, direction)
                    chart_info = {
                        "type": "concept",
                        "concept": analysis.get("concept", "")
                    }
                else:
                    return StepResult(
                        success=False,
                        message="没有可用的数据生成流程图",
                        data={}
                    )
            
            # 保存到 context
            context["flowchart"] = flowchart
            context["chart_info"] = chart_info
            
            return StepResult(
                success=True,
                message=f"成功生成 {chart_info['type']} 类型的流程图",
                data={
                    **chart_info,
                    "format": "mermaid",
                    "direction": direction,
                    "flowchart_length": len(flowchart)
                },
                next_step=None  # 最后一步
            )
        except Exception as e:
            return StepResult(
                success=False,
                message=f"生成流程图失败：{str(e)}",
                data={"error": str(e)}
            )
