"""
MCP Tool 注册模块

优化后结构：
- 工作流类型注册/会话管理：`workflow.registry`
- 严格步骤执行/重复步骤插入：`workflow.engine`

该文件只保留“工具函数”本身的业务逻辑：扫描、搜索、追踪、概念分析、生成流程图。
"""
from typing import Optional, List
from time import time

from core.code_indexer import CodeIndexer
from core.code_analyzer import CodeAnalyzer
from core.flowchart_generator import FlowchartGenerator

from core.logger import get_logger

logger = get_logger("tools")

from workflow.bootstrap import init_workflows
from workflow.engine import try_execute_step
from workflow.registry import workflow_registry, WorkflowSession


def get_workflow(session_id: str) -> tuple:
    """获取工作流会话"""
    wf = workflow_registry.get_session(session_id)
    if not wf:
        return None, format_error("会话不存在", f"session_id: {session_id}\n请先调用 init_learn_code_workflow")
    return wf, None


def format_success(title: str, message: str, data: dict = None, next_step: str = None) -> str:
    """格式化成功输出"""
    lines = ["═" * 45, f"📋 {title}", "═" * 45, "", f"✅ {message}", ""]
    
    if data:
        lines.append("📊 数据:")
        for key, value in data.items():
            if isinstance(value, list):
                if len(value) > 8:
                    display = ", ".join(str(v) for v in value[:8]) + f"... (共{len(value)}项)"
                else:
                    display = ", ".join(str(v) for v in value) if value else "无"
            elif isinstance(value, dict):
                display = ", ".join(f"{k}:{v}" for k, v in list(value.items())[:5])
            else:
                display = str(value)
            lines.append(f"  • {key}: {display}")
        lines.append("")
    
    if next_step:
        lines.append(f"➡️ 下一步: {next_step}")
        lines.append("")
    
    lines.append("═" * 45)
    return "\n".join(lines)


def format_error(title: str, message: str) -> str:
    """格式化错误输出"""
    lines = ["═" * 45, f"❌ {title}", "═" * 45, ""]
    for line in message.split('\n'):
        lines.append(f"  {line}")
    lines.append("")
    lines.append("═" * 45)
    return "\n".join(lines)


def format_workflow_status(workflow: WorkflowSession) -> str:
    """格式化工作流状态"""
    status = workflow.get_status()
    steps_display = "  ".join(
        f"[{name}]{mark}" for name, mark in status["steps"]
    )
    return f"进度: {steps_display}"


def register_tools(mcp):
    """注册所有工具"""
    
    @mcp.tool()
    async def init_learn_code_workflow(
        code_path: str,
        extensions: Optional[str] = None,
        workflow_type: str = "learn_code",
    ) -> str:
        """
        初始化学习代码工作流
        
        Args:
            code_path: 代码仓库路径
            extensions: 要扫描的文件扩展名，逗号分隔（可选）
        
        Returns:
            初始化结果和 session_id
        """
        # 1) 注册工作流到工作流集（幂等）
        init_workflows()

        # 2) 创建会话 + 装配步骤
        ext_list = None
        if extensions:
            ext_list = [ext.strip() for ext in extensions.split(",")]

        workflow = workflow_registry.create_session(
            workflow_type,
            session_prefix="learn_code",
            context={
                "code_path": code_path,
                "extensions": ext_list,
                "created_at": time(),
            },
        )

        logger.info(f"初始化工作流: {workflow.session_id} type={workflow_type}")
        
        return format_success(
            "工作流初始化成功",
            "会话已创建",
            {
                "会话ID": workflow.session_id,
                "代码路径": code_path,
                "扩展名": extensions or "默认",
                "工作流类型": workflow_type,
                "步骤队列": [s.name for s in workflow.steps],
            },
            "执行 scan_repository(session_id) 扫描代码库",
        )

    @mcp.tool()
    async def scan_repository(
        session_id: str,
        repo_path: Optional[str] = None,
        extensions: Optional[str] = None
    ) -> str:
        """
        扫描代码仓库并建立索引
        
        Args:
            session_id: 会话ID
            repo_path: 代码仓库路径（可选）
            extensions: 文件扩展名（可选）
        
        Returns:
            扫描结果
        """
        workflow, error = get_workflow(session_id)
        if error:
            return error
        
        can_execute, error = try_execute_step(workflow, "scan_repository")
        if not can_execute:
            return error
        
        ctx = workflow.context
        path = repo_path or ctx.get("code_path")
        if not path:
            return format_error("扫描失败", "未指定代码路径")
        
        ext_list = ctx.get("extensions")
        if extensions:
            ext_list = [ext.strip() for ext in extensions.split(",")]
        
        try:
            indexer = CodeIndexer(path)
            scan_result = indexer.scan_repository(ext_list)
            index_result = indexer.index_all_files()
            
            ctx["indexer"] = indexer
            ctx["scan_result"] = scan_result
            
            # 前进到下一步
            workflow.advance()
            next_step = workflow.get_current_step()
            
            logger.info(f"扫描完成: {scan_result['total_files']} 文件")
            
            return format_success(
                "扫描完成",
                f"成功扫描 {scan_result['total_files']} 个文件\n{format_workflow_status(workflow)}",
                {
                    "文件数": scan_result["total_files"],
                    "函数数": index_result["total_functions"],
                    "类/结构体": index_result["total_structs"],
                    "文件类型": scan_result.get("extensions", {})
                },
                f"执行 {next_step.name}(session_id)" if next_step else None
            )
        except Exception as e:
            logger.error(f"扫描失败: {e}")
            return format_error("扫描失败", str(e))

    @mcp.tool()
    async def search_functions(
        session_id: str,
        keyword: Optional[str] = None
    ) -> str:
        """
        搜索函数
        
        Args:
            session_id: 会话ID
            keyword: 搜索关键词（可选）
        
        Returns:
            搜索结果
        """
        workflow, error = get_workflow(session_id)
        if error:
            return error
        
        can_execute, error = try_execute_step(workflow, "search_functions")
        if not can_execute:
            return error
        
        ctx = workflow.context
        indexer = ctx.get("indexer")
        if not indexer:
            return format_error("搜索失败", "尚未扫描代码库，请先执行 scan_repository")
        
        try:
            if keyword:
                functions = indexer.search_function(keyword)
                ctx["found_functions"] = functions
                ctx["search_keyword"] = keyword
            else:
                functions = indexer.get_all_functions()
                ctx["found_functions"] = functions[:50]
            
            # 前进到下一步
            workflow.advance()
            next_step = workflow.get_current_step()
            
            result_msg = f"找到 {len(functions)} 个函数" if keyword else f"共 {len(functions)} 个函数"
            
            return format_success(
                "搜索完成",
                f"{result_msg}\n{format_workflow_status(workflow)}",
                {
                    "关键词": keyword or "全部",
                    "结果数": len(functions),
                    "函数列表": [f["name"] for f in functions[:15]]
                },
                f"执行 {next_step.name}(session_id)" if next_step else None
            )
        except Exception as e:
            return format_error("搜索失败", str(e))

    @mcp.tool()
    async def trace_function_flow(
        session_id: str,
        function_name: Optional[str] = None,
        max_depth: int = 3
    ) -> str:
        """
        追踪函数调用流程
        
        Args:
            session_id: 会话ID
            function_name: 函数名（可选）
            max_depth: 最大深度
        
        Returns:
            追踪结果
        """
        workflow, error = get_workflow(session_id)
        if error:
            return error
        
        can_execute, error = try_execute_step(workflow, "trace_function_flow")
        if not can_execute:
            return error
        
        ctx = workflow.context
        indexer = ctx.get("indexer")
        if not indexer:
            return format_error("追踪失败", "尚未扫描代码库，请先执行 scan_repository")
        
        func_name = function_name
        if not func_name:
            found = ctx.get("found_functions", [])
            if found:
                func_name = found[0]["name"]
            else:
                return format_error("追踪失败", "请指定函数名，或先搜索函数")
        
        try:
            analyzer = ctx.get("analyzer") or CodeAnalyzer(indexer)
            ctx["analyzer"] = analyzer
            
            flow = analyzer.trace_function_flow(func_name, max_depth)
            
            if "error" in flow:
                return format_error("追踪失败", flow["error"])
            
            ctx["function_flow"] = flow
            ctx["traced_function"] = func_name
            
            # 前进到下一步
            workflow.advance()
            next_step = workflow.get_current_step()
            
            return format_success(
                "追踪完成",
                f"成功追踪 '{func_name}'\n{format_workflow_status(workflow)}",
                {
                    "函数": func_name,
                    "文件": flow.get("file", ""),
                    "行号": flow.get("line", 0),
                    "深度": max_depth
                },
                f"执行 {next_step.name}(session_id)" if next_step else None
            )
        except Exception as e:
            return format_error("追踪失败", str(e))

    @mcp.tool()
    async def analyze_concept(
        session_id: str,
        concept: str,
        keywords: str
    ) -> str:
        """
        分析代码概念
        
        Args:
            session_id: 会话ID
            concept: 概念名称
            keywords: 关键词，逗号分隔
        
        Returns:
            分析结果
        """
        workflow, error = get_workflow(session_id)
        if error:
            return error
        
        can_execute, error = try_execute_step(workflow, "analyze_concept")
        if not can_execute:
            return error
        
        ctx = workflow.context
        indexer = ctx.get("indexer")
        if not indexer:
            return format_error("分析失败", "尚未扫描代码库，请先执行 scan_repository")
        keyword_list = [kw.strip() for kw in keywords.split(",")]
        
        try:
            analyzer = ctx.get("analyzer") or CodeAnalyzer(indexer)
            ctx["analyzer"] = analyzer
            
            analysis = analyzer.analyze_concept(concept, keyword_list)
            ctx["concept_analysis"] = analysis
            
            # 前进到下一步
            workflow.advance()
            next_step = workflow.get_current_step()
            
            return format_success(
                "概念分析完成",
                f"'{concept}' 相关函数: {analysis['total_functions']} 个\n{format_workflow_status(workflow)}",
                {
                    "概念": concept,
                    "关键词": keyword_list,
                    "函数数": analysis["total_functions"],
                    "函数列表": [f["name"] for f in analysis.get("functions", [])[:10]]
                },
                f"执行 {next_step.name}(session_id, chart_type='concept')" if next_step else None
            )
        except Exception as e:
            return format_error("分析失败", str(e))

    @mcp.tool()
    async def generate_flowchart(
        session_id: str,
        chart_type: Optional[str] = None,
        direction: str = "TD"
    ) -> str:
        """
        生成流程图
        
        Args:
            session_id: 会话ID
            chart_type: 图表类型（call_tree/concept）
            direction: 方向（TD/LR）
        
        Returns:
            Mermaid格式流程图
        """
        workflow, error = get_workflow(session_id)
        if error:
            return error
        
        can_execute, error = try_execute_step(workflow, "generate_flowchart")
        if not can_execute:
            return error
        
        ctx = workflow.context
        function_flow = ctx.get("function_flow")
        concept_analysis = ctx.get("concept_analysis")
        
        if not function_flow and not concept_analysis:
            return format_error(
                "生成失败",
                "没有可用数据\n"
                "请先执行 trace_function_flow 或 analyze_concept"
            )
        
        try:
            generator = FlowchartGenerator()
            flowchart = ""
            chart_info = {}
            
            if chart_type == "concept" and concept_analysis:
                flowchart = generator.generate_concept_flowchart(concept_analysis, direction)
                chart_info = {"type": "concept", "name": concept_analysis.get("concept", "")}
            elif function_flow:
                flowchart = generator.generate_call_tree_flowchart(function_flow["call_tree"], direction)
                chart_info = {"type": "call_tree", "name": function_flow.get("function", "")}
            elif concept_analysis:
                flowchart = generator.generate_concept_flowchart(concept_analysis, direction)
                chart_info = {"type": "concept", "name": concept_analysis.get("concept", "")}
            
            ctx["flowchart"] = flowchart
            ctx["chart_info"] = chart_info
            
            # 前进（完成）
            workflow.advance()
            
            return f"""═══════════════════════════════════════════════
📊 流程图生成完成
═══════════════════════════════════════════════

{format_workflow_status(workflow)}

类型: {chart_info.get('type')}
目标: {chart_info.get('name')}

```mermaid
{flowchart}
```

═══════════════════════════════════════════════
✅ 工作流已完成
═══════════════════════════════════════════════"""
        except Exception as e:
            return format_error("生成失败", str(e))

    @mcp.tool()
    async def get_workflow_status(session_id: str) -> str:
        """获取工作流状态"""
        workflow, error = get_workflow(session_id)
        if error:
            return error
        
        status = workflow.get_status()
        ctx = workflow.context
        
        lines = [
            "═" * 45,
            "📊 工作流状态",
            "═" * 45,
            "",
            f"会话ID: {session_id}",
            f"当前步骤: {status['current_step'] or '已完成'}",
            f"进度: {status['current_index']}/{status['total_steps']}",
            "",
            "步骤队列:",
        ]
        
        for i, (name, mark) in enumerate(status["steps"]):
            indicator = "→" if i == workflow.current_index else " "
            lines.append(f"  {indicator} {i+1}. [{name}] {mark}")
        
        lines.extend(["", "═" * 45])
        
        return "\n".join(lines)

    @mcp.tool()
    async def list_sessions() -> str:
        """列出所有会话"""
        sessions = workflow_registry.list_sessions()
        if not sessions:
            return "📭 没有活跃会话\n\n使用 init_learn_code_workflow 创建"
        
        lines = ["═" * 45, "📋 活跃会话", "═" * 45, ""]
        
        for wf in sessions:
            current = wf.get_current_step()
            lines.append(f"🔹 {wf.session_id}")
            lines.append(f"   当前: {current.name if current else '已完成'}")
            lines.append(f"   进度: {wf.current_index}/{len(wf.steps)}")
            lines.append("")
        
        lines.append("═" * 45)
        return "\n".join(lines)
    
    logger.info("工具注册完成")
