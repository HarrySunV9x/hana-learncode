from typing import List, Optional
from pathlib import Path
import json
import uuid

# 导入步骤类
from workflow.step.scan_repository import ScanRepositoryStep
from workflow.step.search_functions import SearchFunctionsStep
from workflow.step.trace_function_flow import TraceFunctionFlowStep
from workflow.step.analyze_concept import AnalyzeConceptStep
from workflow.step.generate_flowchart import GenerateFlowchartStep

from workflow.workflow_manager import workflow_manager

from time import time
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
    async def init_learn_code_workflow(
        code_path: str,
        extensions: Optional[str] = None
    ) -> str:
        """
        初始化学习代码工作流
        
        Args:
            code_path: 代码仓库路径
            extensions: 要扫描的文件扩展名，逗号分隔（可选，如：.py,.js,.go）
        
        Returns:
            初始化结果和 session_id
        """
        # 创建会话
        learn_code_session_id = f"learn_code_{int(time() * 1000)}"
        session_id, context = get_or_create_session(learn_code_session_id)
        
        # 解析扩展名
        ext_list = None
        if extensions:
            ext_list = [ext.strip() for ext in extensions.split(",")]
        
        # 创建工作流
        learn_code_workflow = workflow_manager.create_workflow(session_id, "learn_code", "学习代码")
        
        # 添加第一步，扫描代码仓
        learn_code_workflow.add_step(ScanRepositoryStep(learn_code_workflow, code_path, ext_list))
        
        # 启动工作流
        learn_code_workflow.start()
        
        return f"""═══════════════════════════════════════════
🎯 工作流初始化成功
═══════════════════════════════════════════

会话 ID: {session_id}
代码路径: {code_path}
扫描扩展名: {extensions or "默认"}

接下来执行{workflow_manager.get_workflow(session_id).get_current_step().get_name()}

═══════════════════════════════════════════"""

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
            repo_path: 代码仓库路径（可选，使用初始化时的路径）
            extensions: 要扫描的文件扩展名，逗号分隔（可选，如：.py,.js,.go）
        
        Returns:
            扫描结果
        """
        workflow = workflow_manager.get_workflow(session_id)
        if not workflow:
            return f"❌ scan_repository时，工作流不存在：{session_id}\n"
        
        _, context = get_or_create_session(session_id)
        
        # 将参数放入 context（如果提供）
        if repo_path:
            context["repo_path"] = repo_path
        if extensions:
            context["extensions"] = [ext.strip() for ext in extensions.split(",")]
        
        # 执行扫描
        result = workflow.get_current_step().run(context)
        
        # 扫描完成后，添加后续步骤模板
        # 这样 scan 返回的 next_step="search_functions" 就能找到对应步骤
        if "indexer" in context:
            workflow.add_step(SearchFunctionsStep(workflow, None))
            workflow.add_step(TraceFunctionFlowStep(workflow, None))
            workflow.add_step(AnalyzeConceptStep(workflow, None, None))
            workflow.add_step(GenerateFlowchartStep(workflow, "call_tree"))
        
        return result
    
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
        workflow = workflow_manager.get_workflow(session_id)
        if not workflow:
            return f"❌ search_functions时工作流不存在：{session_id}\n"
        
        _, context = get_or_create_session(session_id)
        
        # 将参数放入 context
        if keyword:
            context["search_keyword"] = keyword
        
        # 检查当前步骤是否是 search_functions
        current_step = workflow.get_current_step()
        if current_step and current_step.get_name() == "search_functions":
            # 第一次调用，使用已有的 search_functions 步骤
            return current_step.run(context)
        else:
            # 不是第一次，添加新的 search 步骤
            step_index = len([s for s in workflow.steps if "search_functions" in s.get_name()])
            new_step = SearchFunctionsStep(workflow, keyword)
            new_step.name = f"search_functions_{step_index}"
            workflow.add_step(new_step)
            workflow.jump_to_step(new_step.name)
            return new_step.run(context)
    
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
        workflow = workflow_manager.get_workflow(session_id)
        if not workflow:
            return f"❌ trace_function_flow时工作流不存在：{session_id}\n"
        
        _, context = get_or_create_session(session_id)
 
        # 将参数放入 context
        if function_name:
            context["trace_function"] = function_name
        if max_depth != 3:  # 只在非默认值时设置
            context["max_depth"] = max_depth
        
        # 检查当前步骤是否是 trace_function_flow
        current_step = workflow.get_current_step()
        if current_step and current_step.get_name() == "trace_function_flow":
            # 第一次调用，使用已有的步骤
            return current_step.run(context)
        else:
            # 添加新的 trace 步骤
            step_index = len([s for s in workflow.steps if "trace_function_flow" in s.get_name()])
            new_step = TraceFunctionFlowStep(workflow, function_name, max_depth)
            new_step.name = f"trace_function_flow_{step_index}"
            workflow.add_step(new_step)
            workflow.jump_to_step(new_step.name)
            return new_step.run(context)
    
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
        workflow = workflow_manager.get_workflow(session_id)
        if not workflow:
            return f"❌ analyze_concept时工作流不存在：{session_id}\n"
        
        _, context = get_or_create_session(session_id)
 
        # 将参数放入 context
        context["concept"] = concept
        context["keywords"] = [kw.strip() for kw in keywords.split(",")]
        
        # 检查当前步骤是否是 analyze_concept
        current_step = workflow.get_current_step()
        if current_step and current_step.get_name() == "analyze_concept":
            # 第一次调用，使用已有的步骤
            return current_step.run(context)
        else:
            # 添加新的分析步骤
            step_index = len([s for s in workflow.steps if "analyze_concept" in s.get_name()])
            new_step = AnalyzeConceptStep(workflow, concept, keywords)
            new_step.name = f"analyze_concept_{step_index}"
            workflow.add_step(new_step)
            workflow.jump_to_step(new_step.name)
            return new_step.run(context)
    
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
        workflow = workflow_manager.get_workflow(session_id)
        if not workflow:
            return f"❌ generate_flowchart时工作流不存在：{session_id}\n"
        
        _, context = get_or_create_session(session_id)
 
        # 将参数放入 context
        if chart_type:
            context["chart_type"] = chart_type
        if direction != "TD":  # 只在非默认值时设置
            context["direction"] = direction
        
        # 检查当前步骤是否是 generate_flowchart
        current_step = workflow.get_current_step()
        if current_step and current_step.get_name() == "generate_flowchart":
            # 第一次调用，使用已有的步骤
            return current_step.run(context)
        else:
            # 添加新的生成流程图步骤
            step_index = len([s for s in workflow.steps if "generate_flowchart" in s.get_name()])
            new_step = GenerateFlowchartStep(workflow, chart_type or "call_tree")
            new_step.name = f"generate_flowchart_{step_index}"
            workflow.add_step(new_step)
            workflow.jump_to_step(new_step.name)
            return new_step.run(context)