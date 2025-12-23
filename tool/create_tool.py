from typing import List, Optional
from pathlib import Path
import json
import uuid

from core.code_indexer import CodeIndexer
from core.code_analyzer import CodeAnalyzer
from core.flowchart_generator import FlowchartGenerator

# 导入步骤类
from workflow.step.scan_repository import ScanRepositoryStep
from workflow.step.search_functions import SearchFunctionsStep
from workflow.step.trace_function_flow import TraceFunctionFlowStep
from workflow.step.analyze_concept import AnalyzeConceptStep
from workflow.step.generate_flowchart import GenerateFlowchartStep

# 全局上下文 - 用于在多个工具调用之间传递数据
# session_id -> context
sessions = {}


def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, dict]:
    """获取或创建会话上下文"""
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    
    # 创建新会话
    new_session_id = f"session_{uuid.uuid4().hex[:8]}"
    sessions[new_session_id] = {}
    return new_session_id, sessions[new_session_id]

def register_tools(mcp):
    """注册所有工具到 MCP 服务器 - 每个工具对应一个具体步骤"""
    
    @mcp.tool()
    async def scan_repository(
        repo_path: str,
        session_id: Optional[str] = None,
        extensions: Optional[str] = None
    ) -> str:
        """
        扫描代码仓库并建立索引
        
        Args:
            repo_path: 代码仓库路径
            session_id: 会话ID（可选，用于多步骤操作）
            extensions: 要扫描的文件扩展名，逗号分隔（可选，如：.py,.js,.go）
        
        Returns:
            扫描结果
        """
        try:
            # 获取或创建会话
            sid, context = get_or_create_session(session_id)
            
            # 解析扩展名
            ext_list = None
            if extensions:
                ext_list = [ext.strip() for ext in extensions.split(",")]
            
            # 创建并执行步骤
            step = ScanRepositoryStep(None, repo_path, ext_list)
            return step.run(context)
        except Exception as e:
            return f"❌ 扫描仓库失败：{str(e)}"
    
    @mcp.tool()
    async def search_functions(
        session_id: str,
        keyword: Optional[str] = None
    ) -> str:
        """
        搜索函数（需要先执行 scan_repository）
        
        Args:
            session_id: 会话ID
            keyword: 搜索关键词（可选，不指定则返回所有函数）
        
        Returns:
            搜索结果
        """
        try:
            # 获取会话
            if session_id not in sessions:
                return f"❌ 会话不存在：{session_id}\n请先执行 scan_repository"

            context = sessions[session_id]

            # 创建并执行步骤
            step = SearchFunctionsStep(None, keyword)
            return step.run(context)
        except Exception as e:
            return f"❌ 搜索函数失败：{str(e)}"
    
    @mcp.tool()
    async def trace_function_flow(
        session_id: str,
        function_name: Optional[str] = None,
        max_depth: int = 3
    ) -> str:
        """
        追踪函数调用流程（需要先执行 scan_repository）
        
        Args:
            session_id: 会话ID
            function_name: 函数名（可选，不指定则使用搜索结果的第一个函数）
            max_depth: 最大追踪深度（默认3层）
        
        Returns:
            追踪结果
        """
        try:
            # 获取会话
            if session_id not in sessions:
                return f"❌ 会话不存在：{session_id}\n请先执行 scan_repository"

            context = sessions[session_id]

            # 创建并执行步骤
            step = TraceFunctionFlowStep(None, function_name, max_depth)
            return step.run(context)
        except Exception as e:
            return f"❌ 追踪函数流程失败：{str(e)}"
    
    @mcp.tool()
    async def analyze_concept(
        session_id: str,
        concept: str,
        keywords: str
    ) -> str:
        """
        分析代码概念（需要先执行 scan_repository）
        
        Args:
            session_id: 会话ID
            concept: 概念名称
            keywords: 关键词，逗号分隔（如：init,setup,configure）
        
        Returns:
            分析结果
        """
        try:
            # 获取会话
            if session_id not in sessions:
                return f"❌ 会话不存在：{session_id}\n请先执行 scan_repository"

            context = sessions[session_id]

            # 解析关键词
            keyword_list = [kw.strip() for kw in keywords.split(",")]

            # 创建并执行步骤
            step = AnalyzeConceptStep(None, concept, keyword_list)
            return step.run(context)
        except Exception as e:
            return f"❌ 分析概念失败：{str(e)}"
    
    @mcp.tool()
    async def generate_flowchart(
        session_id: str,
        chart_type: Optional[str] = None,
        direction: str = "TD"
    ) -> str:
        """
        生成流程图（需要先执行 trace_function_flow 或 analyze_concept）
        
        Args:
            session_id: 会话ID
            chart_type: 图表类型（call_tree=函数调用树, concept=概念图，可选，自动检测）
            direction: 方向（TD=上到下, LR=左到右）
        
        Returns:
            流程图（Mermaid格式）
        """
        try:
            # 获取会话
            if session_id not in sessions:
                return f"❌ 会话不存在：{session_id}\n请先执行相应的分析步骤"

            context = sessions[session_id]

            # 创建并执行步骤
            step = GenerateFlowchartStep(None, chart_type or "call_tree", direction)
            return step.run(context)
        except Exception as e:
            return f"❌ 生成流程图失败：{str(e)}"
    
    @mcp.tool()
    async def list_sessions() -> str:
        """
        列出所有会话
        
        Returns:
            所有会话列表
        """
        if not sessions:
            return "暂无会话"
        
        result = f"""═══════════════════════════════════════════
📋 所有会话 (共 {len(sessions)} 个)
═══════════════════════════════════════════

"""
        for sid, context in sessions.items():
            has_indexer = "indexer" in context
            has_flow = "function_flow" in context
            has_concept = "concept_analysis" in context
            has_chart = "flowchart" in context
            
            result += f"""
会话ID: {sid}
  • 已扫描: {'✓' if has_indexer else '✗'}
  • 已追踪函数: {'✓' if has_flow else '✗'}
  • 已分析概念: {'✓' if has_concept else '✗'}
  • 已生成图表: {'✓' if has_chart else '✗'}
---"""
        
        result += "\n═══════════════════════════════════════════"
        
        return result
    
    @mcp.tool()
    async def get_session_info(session_id: str) -> str:
        """
        获取会话详细信息
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话信息
        """
        if session_id not in sessions:
            return f"❌ 会话不存在：{session_id}"
        
        context = sessions[session_id]
        
        result = f"""═══════════════════════════════════════════
📊 会话信息
═══════════════════════════════════════════

会话 ID: {session_id}

"""
        
        # 扫描结果
        if "scan_result" in context:
            scan = context["scan_result"]
            result += f"""📁 扫描结果：
  • 文件数: {scan.get('total_files', 0)}
  • 扩展名: {scan.get('extensions', {})}

"""
        
        # 索引结果
        if "index_result" in context:
            index = context["index_result"]
            result += f"""📑 索引结果：
  • 函数数: {index.get('total_functions', 0)}
  • 结构体/类数: {index.get('total_structs', 0)}

"""
        
        # 搜索结果
        if "found_functions" in context:
            funcs = context["found_functions"]
            result += f"""🔍 搜索结果：
  • 找到函数数: {len(funcs)}

"""
        
        # 追踪结果
        if "function_flow" in context:
            flow = context["function_flow"]
            result += f"""🔄 函数追踪：
  • 函数: {flow.get('function', '')}
  • 文件: {flow.get('file', '')}
  • 行号: {flow.get('line', 0)}

"""
        
        # 概念分析结果
        if "concept_analysis" in context:
            analysis = context["concept_analysis"]
            result += f"""💡 概念分析：
  • 概念: {analysis.get('concept', '')}
  • 相关函数数: {analysis.get('total_functions', 0)}

"""
        
        # 流程图
        if "flowchart" in context:
            chart_info = context.get("chart_info", {})
            flowchart = context["flowchart"]
            result += f"""📊 流程图：
  • 类型: {chart_info.get('type', 'unknown')}
  • 格式: Mermaid
  • 大小: {len(flowchart)} 字符

"""
        
        result += "═══════════════════════════════════════════"
        
        return result