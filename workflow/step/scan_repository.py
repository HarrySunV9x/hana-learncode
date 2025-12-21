"""扫描代码仓库步骤"""
from typing import Optional
from workflow.step.base_step import BaseStep, StepResult
from core.code_indexer import CodeIndexer


class ScanRepositoryStep(BaseStep):
    """扫描代码仓库步骤"""
    
    def __init__(self, workflow, repo_path: str, extensions: Optional[list] = None):
        super().__init__("scan_repository", "扫描代码仓库", workflow)
        self.repo_path = repo_path
        self.extensions = extensions
    
    def validate_parameters(self, context: dict) -> bool:
        """校验参数"""
        return self.repo_path is not None and len(self.repo_path) > 0
    
    def execute(self, context: dict) -> StepResult:
        """执行扫描仓库步骤"""
        try:
            # 创建索引器
            indexer = CodeIndexer(self.repo_path)
            
            # 扫描仓库
            scan_result = indexer.scan_repository(self.extensions)
            
            # 索引所有文件
            index_result = indexer.index_all_files()
            
            # 保存到 context 供后续步骤使用
            context["indexer"] = indexer
            context["scan_result"] = scan_result
            context["index_result"] = index_result
            
            return StepResult(
                success=True,
                message=f"成功扫描 {scan_result['total_files']} 个文件，索引了 {index_result['total_functions']} 个函数和 {index_result['total_structs']} 个结构体/类",
                data={
                    "total_files": scan_result["total_files"],
                    "total_functions": index_result["total_functions"],
                    "total_structs": index_result["total_structs"],
                    "extensions": scan_result.get("extensions", {})
                },
                next_step="search_functions"  # 扫描完成后搜索函数
            )
        except Exception as e:
            return StepResult(
                success=False,
                message=f"扫描仓库失败：{str(e)}",
                data={"error": str(e)}
            )

