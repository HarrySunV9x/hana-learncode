from typing import List, Optional
from pathlib import Path
import json

from core.code_indexer import CodeIndexer
from core.code_analyzer import CodeAnalyzer
from core.flowchart_generator import FlowchartGenerator

# 全局实例
indexers = {}  # repo_path -> CodeIndexer
analyzers = {}  # repo_path -> CodeAnalyzer


def get_or_create_indexer(repo_path: str) -> tuple[CodeIndexer, CodeAnalyzer]:
    """获取或创建代码索引器和分析器"""
    if repo_path not in indexers:
        indexers[repo_path] = CodeIndexer(repo_path)
        analyzers[repo_path] = CodeAnalyzer(indexers[repo_path])
    return indexers[repo_path], analyzers[repo_path]


def register_tools(mcp):
    """注册所有工具到 MCP 服务器"""
    
    @mcp.tool()
    async def scan_code_repository(
        repo_path: str,
        extensions: Optional[str] = None
    ) -> str:
        """
        扫描代码仓库，建立索引
        
        Args:
            repo_path: 代码仓库的本地路径
            extensions: 要扫描的文件扩展名，用逗号分隔（如 ".c,.h,.py"）。不指定则使用默认扩展名
        
        Returns:
            扫描结果的 JSON 字符串
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            # 解析扩展名
            ext_list = None
            if extensions:
                ext_list = [ext.strip() if ext.strip().startswith('.') else f'.{ext.strip()}' 
                           for ext in extensions.split(',')]
            
            # 扫描仓库
            scan_result = indexer.scan_repository(ext_list)
            
            # 索引所有文件
            index_result = indexer.index_all_files()
            
            result = {
                "status": "success",
                "repo_path": repo_path,
                "scan": scan_result,
                "index": index_result,
                "message": f"成功扫描 {scan_result['total_files']} 个文件，索引了 {index_result['total_functions']} 个函数"
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def search_functions(
        repo_path: str,
        keyword: str
    ) -> str:
        """
        在代码库中搜索包含关键字的函数
        
        Args:
            repo_path: 代码仓库路径
            keyword: 搜索关键字
        
        Returns:
            搜索结果的 JSON 字符串
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            functions = indexer.search_function(keyword)
            
            result = {
                "status": "success",
                "keyword": keyword,
                "total_found": len(functions),
                "functions": functions[:50]  # 限制返回数量
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def trace_function_flow(
        repo_path: str,
        function_name: str,
        max_depth: int = 3
    ) -> str:
        """
        追踪函数调用流程，显示该函数调用了哪些其他函数
        
        Args:
            repo_path: 代码仓库路径
            function_name: 要追踪的函数名
            max_depth: 追踪深度（默认3层）
        
        Returns:
            函数调用树的 JSON 字符串
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            flow = analyzer.trace_function_flow(function_name, max_depth)
            
            if "error" in flow:
                return json.dumps({
                    "status": "error",
                    "error": flow["error"]
                }, ensure_ascii=False, indent=2)
            
            result = {
                "status": "success",
                "flow": flow
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def analyze_code_concept(
        repo_path: str,
        concept: str,
        keywords: str
    ) -> str:
        """
        分析特定概念相关的代码，帮助学习某个主题
        
        Args:
            repo_path: 代码仓库路径
            concept: 概念名称（如 "内存分配"）
            keywords: 相关关键字，用逗号分隔（如 "malloc,alloc,kmalloc"）
        
        Returns:
            分析结果的 JSON 字符串
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            keyword_list = [kw.strip() for kw in keywords.split(',')]
            analysis = analyzer.analyze_concept(concept, keyword_list)
            
            result = {
                "status": "success",
                "analysis": analysis
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def get_function_code(
        repo_path: str,
        function_name: str
    ) -> str:
        """
        获取完整的函数源代码
        
        Args:
            repo_path: 代码仓库路径
            function_name: 函数名
        
        Returns:
            函数代码的 JSON 字符串
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            code = analyzer.extract_function_code(function_name)
            
            if not code:
                return json.dumps({
                    "status": "error",
                    "error": f"未找到函数: {function_name}"
                }, ensure_ascii=False, indent=2)
            
            result = {
                "status": "success",
                "function_code": code
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def generate_flowchart(
        repo_path: str,
        function_name: str,
        chart_type: str = "call_tree",
        max_depth: int = 3,
        direction: str = "TD"
    ) -> str:
        """
        生成函数调用流程图（Mermaid 格式）
        
        Args:
            repo_path: 代码仓库路径
            function_name: 函数名
            chart_type: 图表类型（call_tree=调用树）
            max_depth: 追踪深度
            direction: 图的方向（TD=上到下，LR=左到右）
        
        Returns:
            Mermaid 格式的流程图代码
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            generator = FlowchartGenerator()
            
            if chart_type == "call_tree":
                # 获取调用树
                flow = analyzer.trace_function_flow(function_name, max_depth)
                
                if "error" in flow:
                    return json.dumps({
                        "status": "error",
                        "error": flow["error"]
                    }, ensure_ascii=False, indent=2)
                
                # 生成流程图
                flowchart = generator.generate_call_tree_flowchart(flow["call_tree"], direction)
            else:
                return json.dumps({
                    "status": "error",
                    "error": f"不支持的图表类型: {chart_type}"
                }, ensure_ascii=False, indent=2)
            
            result = {
                "status": "success",
                "function": function_name,
                "flowchart": flowchart,
                "format": "mermaid"
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def generate_concept_flowchart(
        repo_path: str,
        concept: str,
        keywords: str,
        direction: str = "TD"
    ) -> str:
        """
        生成概念相关的流程图，展示相关函数和它们的关系
        
        Args:
            repo_path: 代码仓库路径
            concept: 概念名称
            keywords: 相关关键字，用逗号分隔
            direction: 图的方向（TD=上到下，LR=左到右）
        
        Returns:
            Mermaid 格式的流程图代码
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            # 分析概念
            keyword_list = [kw.strip() for kw in keywords.split(',')]
            analysis = analyzer.analyze_concept(concept, keyword_list)
            
            # 生成流程图
            generator = FlowchartGenerator()
            flowchart = generator.generate_concept_flowchart(analysis, direction)
            
            result = {
                "status": "success",
                "concept": concept,
                "flowchart": flowchart,
                "format": "mermaid",
                "total_functions": analysis["total_functions"]
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def find_function_path(
        repo_path: str,
        from_function: str,
        to_function: str,
        max_depth: int = 10
    ) -> str:
        """
        查找从一个函数到另一个函数的调用路径
        
        Args:
            repo_path: 代码仓库路径
            from_function: 起始函数名
            to_function: 目标函数名
            max_depth: 最大搜索深度
        
        Returns:
            调用路径的 JSON 字符串
        """
        try:
            indexer, analyzer = get_or_create_indexer(repo_path)
            
            if not indexer.files:
                return json.dumps({
                    "status": "error",
                    "error": "请先使用 scan_code_repository 扫描仓库"
                }, ensure_ascii=False, indent=2)
            
            paths = analyzer.find_call_path(from_function, to_function, max_depth)
            
            if not paths:
                return json.dumps({
                    "status": "success",
                    "from": from_function,
                    "to": to_function,
                    "paths": [],
                    "message": "未找到调用路径"
                }, ensure_ascii=False, indent=2)
            
            # 生成流程图
            generator = FlowchartGenerator()
            flowchart = generator.generate_function_path_flowchart(paths)
            
            result = {
                "status": "success",
                "from": from_function,
                "to": to_function,
                "total_paths": len(paths),
                "paths": paths,
                "flowchart": flowchart,
                "format": "mermaid"
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False, indent=2)