"""搜索函数步骤"""
from typing import Optional
from workflow.step.base_step import BaseStep, StepResult


class SearchFunctionsStep(BaseStep):
    """搜索函数步骤"""
    
    def __init__(self, workflow, keyword: Optional[str] = None):
        super().__init__("search_functions", "搜索函数", workflow)
        self.keyword = keyword
    
    def validate_parameters(self, context: dict) -> bool:
        """校验参数"""
        # 需要 indexer 已经存在（由前面的步骤创建）
        return "indexer" in context
    
    def execute(self, context: dict) -> StepResult:
        """执行搜索函数步骤"""
        try:
            indexer = context["indexer"]
            
            # 从 context 获取关键词，如果没有则使用初始化时的关键词
            keyword = context.get("search_keyword", self.keyword)
            
            if not keyword:
                # 如果没有指定关键词，返回所有函数
                all_functions = []
                for file_funcs in indexer.functions.values():
                    all_functions.extend(file_funcs)
                
                context["found_functions"] = all_functions[:50]  # 限制数量
                
                return StepResult(
                    success=True,
                    message=f"共找到 {len(all_functions)} 个函数（显示前50个）",
                    data={
                        "total_count": len(all_functions),
                        "显示数量": min(50, len(all_functions)),
                        "function_names": [f["name"] for f in all_functions[:50]]
                    },
                    next_step="trace_function_flow"  # 继续追踪函数流程
                )
            else:
                # 搜索包含关键词的函数
                functions = indexer.search_function(keyword)
                
                context["found_functions"] = functions
                context["search_keyword"] = keyword
                
                if len(functions) == 0:
                    return StepResult(
                        success=True,
                        message=f"未找到包含关键词 '{keyword}' 的函数",
                        data={"keyword": keyword, "count": 0},
                        next_step=None  # 没有找到函数，结束流程
                    )
                
                return StepResult(
                    success=True,
                    message=f"找到 {len(functions)} 个包含 '{keyword}' 的函数",
                    data={
                        "keyword": keyword,
                        "count": len(functions),
                        "function_names": [f["name"] for f in functions[:20]]
                    },
                    next_step="trace_function_flow"
                )
        except Exception as e:
            return StepResult(
                success=False,
                message=f"搜索函数失败：{str(e)}",
                data={"error": str(e)}
            )
