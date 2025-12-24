"""
MCP Resource 定义
提供静态或动态的数据资源
"""
import json

from workflow.registry import workflow_registry
from core.logger import get_logger

logger = get_logger("resources")


def register_resources(mcp):
    """注册所有 resource 到 MCP 服务器"""
    
    @mcp.resource("code://sessions")
    def list_all_sessions() -> str:
        """获取所有活跃会话列表"""
        session_list = []
        for wf in workflow_registry.list_sessions():
            sid = wf.session_id
            ctx = wf.context
            indexer = ctx.get("indexer")
            session_list.append({
                "session_id": sid,
                "code_path": ctx.get("code_path", ""),
                "scanned": indexer is not None,
                "functions_count": sum(len(f) for f in indexer.functions.values()) if indexer else 0
            })
        return json.dumps(session_list, ensure_ascii=False, indent=2)
    
    @mcp.resource("code://session/{session_id}/info")
    def get_session_info(session_id: str) -> str:
        """获取会话详情"""
        wf = workflow_registry.get_session(session_id)
        if not wf:
            return json.dumps({"error": f"会话不存在: {session_id}"}, ensure_ascii=False)
        ctx = wf.context
        
        indexer = ctx.get("indexer")
        return json.dumps({
            "session_id": session_id,
            "workflow_type": wf.workflow_type,
            "code_path": ctx.get("code_path", ""),
            "scanned": indexer is not None,
            "functions_count": sum(len(f) for f in indexer.functions.values()) if indexer else 0,
            "structs_count": sum(len(s) for s in indexer.structs.values()) if indexer else 0,
            "traced_function": ctx.get("traced_function"),
            "analyzed_concept": ctx.get("concept_analysis", {}).get("concept"),
            "has_flowchart": ctx.get("flowchart") is not None
        }, ensure_ascii=False, indent=2)
    
    @mcp.resource("code://session/{session_id}/functions")
    def get_session_functions(session_id: str) -> str:
        """获取会话中的函数列表"""
        wf = workflow_registry.get_session(session_id)
        if not wf:
            return json.dumps({"error": "会话不存在"}, ensure_ascii=False)
        ctx = wf.context
        
        indexer = ctx.get("indexer")
        if not indexer:
            return json.dumps({"error": "请先执行扫描"}, ensure_ascii=False)
        
        all_functions = indexer.get_all_functions()
        return json.dumps({
            "total": len(all_functions),
            "functions": all_functions[:100]
        }, ensure_ascii=False, indent=2)
    
    @mcp.resource("code://session/{session_id}/flowchart")
    def get_session_flowchart(session_id: str) -> str:
        """获取会话的流程图"""
        wf = workflow_registry.get_session(session_id)
        if not wf:
            return json.dumps({"error": "会话不存在"}, ensure_ascii=False)
        ctx = wf.context
        
        flowchart = ctx.get("flowchart")
        if not flowchart:
            return json.dumps({"error": "请先生成流程图"}, ensure_ascii=False)
        
        return json.dumps({
            "chart_info": ctx.get("chart_info", {}),
            "flowchart": flowchart
        }, ensure_ascii=False, indent=2)
    
    @mcp.resource("code://help")
    def get_help() -> str:
        """获取使用帮助"""
        return """
# CodeLearnAssistant 使用指南

## 工具列表

1. `init_learn_code_workflow(code_path)` - 初始化会话
2. `scan_repository(session_id)` - 扫描代码库
3. `search_functions(session_id, keyword)` - 搜索函数
4. `trace_function_flow(session_id, function_name)` - 追踪函数调用
5. `analyze_concept(session_id, concept, keywords)` - 分析概念
6. `generate_flowchart(session_id)` - 生成流程图

## 典型流程

1. init_learn_code_workflow -> 获取 session_id
2. scan_repository -> 扫描索引
3. search_functions 或 trace_function_flow
4. generate_flowchart -> 生成可视化

## 资源

- `code://sessions` - 会话列表
- `code://session/{id}/info` - 会话信息
- `code://session/{id}/functions` - 函数列表
- `code://session/{id}/flowchart` - 流程图
"""
    
    logger.info("资源注册完成")
