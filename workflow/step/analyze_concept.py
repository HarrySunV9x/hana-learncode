"""分析代码概念步骤"""
from typing import List, Optional
from workflow.step.base_step import BaseStep, StepResult
from core.code_analyzer import CodeAnalyzer


class AnalyzeConceptStep(BaseStep):
    """分析代码概念步骤"""
    
    def __init__(self, workflow, concept: Optional[str] = None, keywords: Optional[List[str]] = None):
        super().__init__("analyze_concept", "分析代码概念", workflow)
        self.concept = concept
        self.keywords = keywords or []
    
    def validate_parameters(self, context: dict) -> bool:
        """校验参数"""
        return "indexer" in context
    
    def execute(self, context: dict) -> StepResult:
        """执行分析概念步骤"""
        try:
            indexer = context["indexer"]
            
            # 获取 analyzer，如果不存在则创建
            if "analyzer" not in context:
                analyzer = CodeAnalyzer(indexer)
                context["analyzer"] = analyzer
            else:
                analyzer = context["analyzer"]
            
            # 获取概念和关键词
            concept = context.get("concept", self.concept)
            keywords = context.get("keywords", self.keywords)
            
            if not concept or not keywords:
                return StepResult(
                    success=False,
                    message="未指定概念名称或关键词",
                    data={}
                )
            
            # 分析概念
            analysis = analyzer.analyze_concept(concept, keywords)
            
            # 保存到 context
            context["concept_analysis"] = analysis
            
            return StepResult(
                success=True,
                message=f"成功分析概念 '{concept}'，找到 {analysis['total_functions']} 个相关函数",
                data={
                    "concept": concept,
                    "keywords": keywords,
                    "total_functions": analysis["total_functions"]
                },
                next_step="generate_flowchart"  # 生成概念流程图
            )
        except Exception as e:
            return StepResult(
                success=False,
                message=f"分析概念失败：{str(e)}",
                data={"error": str(e)}
            )
