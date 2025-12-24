"""代码分析器 - 分析代码流程和调用关系"""
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict, deque

from core.logger import get_logger
from core.config import config

logger = get_logger("code_analyzer")


class CodeAnalyzer:
    """代码流程分析器"""
    
    def __init__(self, indexer: "CodeIndexer"):
        """
        初始化代码分析器
        
        Args:
            indexer: CodeIndexer 实例
        """
        from core.code_indexer import CodeIndexer
        self.indexer: CodeIndexer = indexer
        self.call_graph: Dict[str, List[str]] = defaultdict(list)
        self.analyzed_functions: Set[str] = set()
        
        logger.debug("初始化 CodeAnalyzer")
    
    def find_function_calls(self, file_path: Path, function_name: str) -> List[str]:
        """
        在指定文件中查找函数调用
        
        Args:
            file_path: 文件路径
            function_name: 函数名
        
        Returns:
            被调用的函数名列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return []
        
        suffix = file_path.suffix
        
        # 根据文件类型选择不同的解析策略
        if suffix == '.py':
            return self._find_python_function_calls(content, function_name)
        elif suffix in ['.c', '.h', '.cpp', '.hpp']:
            return self._find_c_function_calls(content, function_name)
        else:
            return self._find_generic_function_calls(content, function_name)
    
    def _find_python_function_calls(self, content: str, function_name: str) -> List[str]:
        """查找 Python 函数调用"""
        # 找到函数定义
        func_pattern = rf'def\s+{re.escape(function_name)}\s*\([^)]*\)\s*(?:->.*?)?:'
        match = re.search(func_pattern, content)
        
        if not match:
            return []
        
        # 提取函数体（基于缩进）
        start = match.end()
        lines = content[start:].split('\n')
        
        function_body_lines = []
        base_indent = None
        
        for line in lines:
            if not line.strip():  # 空行
                function_body_lines.append(line)
                continue
            
            # 计算缩进
            stripped = line.lstrip()
            if not stripped:
                continue
                
            current_indent = len(line) - len(stripped)
            
            if base_indent is None:
                base_indent = current_indent
            
            if current_indent >= base_indent:
                function_body_lines.append(line)
            else:
                break
        
        function_body = '\n'.join(function_body_lines)
        
        # 查找函数调用
        call_pattern = r'\b([a-zA-Z_]\w*)\s*\('
        calls = re.findall(call_pattern, function_body)
        
        # 过滤关键字和内置函数
        keywords = {
            'if', 'while', 'for', 'with', 'elif', 'except', 'assert',
            'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
            'set', 'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'super', 'open', 'input', 'format', 'enumerate', 'zip',
            'map', 'filter', 'sorted', 'reversed', 'min', 'max', 'sum', 'any', 'all'
        }
        calls = [call for call in calls if call not in keywords]
        
        return list(set(calls))
    
    def _find_c_function_calls(self, content: str, function_name: str) -> List[str]:
        """查找 C/C++ 函数调用"""
        # 找到函数定义的位置
        func_pattern = rf'\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{'
        match = re.search(func_pattern, content)
        
        if not match:
            return []
        
        # 提取函数体（括号匹配）
        start = match.end() - 1
        brace_count = 1
        end = start + 1
        
        while end < len(content) and brace_count > 0:
            if content[end] == '{':
                brace_count += 1
            elif content[end] == '}':
                brace_count -= 1
            end += 1
        
        function_body = content[start:end]
        
        # 查找函数调用
        call_pattern = r'\b([a-zA-Z_]\w*)\s*\('
        calls = re.findall(call_pattern, function_body)
        
        # 过滤关键字和宏
        keywords = {
            'if', 'while', 'for', 'switch', 'sizeof', 'return', 'typeof',
            'else', 'case', 'default', 'break', 'continue', 'goto',
            'NULL', 'true', 'false', 'nullptr'
        }
        calls = [call for call in calls if call not in keywords]
        
        return list(set(calls))
    
    def _find_generic_function_calls(self, content: str, function_name: str) -> List[str]:
        """通用函数调用查找"""
        # 简单的函数调用模式匹配
        call_pattern = r'\b([a-zA-Z_]\w*)\s*\('
        calls = re.findall(call_pattern, content)
        
        keywords = {'if', 'while', 'for', 'switch', 'return', 'function', 'class'}
        calls = [call for call in calls if call not in keywords]
        
        return list(set(calls))
    
    def trace_function_flow(
        self, 
        function_name: str, 
        max_depth: int = None
    ) -> Dict[str, Any]:
        """
        追踪函数调用流程
        
        Args:
            function_name: 要追踪的函数名
            max_depth: 最大追踪深度
        
        Returns:
            函数调用树
        """
        if max_depth is None:
            max_depth = config.MAX_TRACE_DEPTH
        
        logger.info(f"开始追踪函数 '{function_name}'，最大深度: {max_depth}")
        
        # 查找函数定义
        functions = self.indexer.search_function(function_name)
        
        if not functions:
            logger.warning(f"未找到函数: {function_name}")
            return {"error": f"未找到函数: {function_name}"}
        
        # 使用第一个匹配的函数
        func_info = functions[0]
        
        # 构建调用树
        call_tree = self._build_call_tree(func_info, max_depth)
        
        result = {
            "function": func_info["name"],
            "file": func_info["file"],
            "line": func_info["line"],
            "call_tree": call_tree
        }
        
        logger.info(f"函数追踪完成: {function_name}")
        return result
    
    def _build_call_tree(
        self, 
        func_info: Dict[str, Any], 
        max_depth: int,
        current_depth: int = 0, 
        visited: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """递归构建调用树"""
        if visited is None:
            visited = set()
        
        func_key = f"{func_info['file']}:{func_info['name']}"
        
        if current_depth >= max_depth or func_key in visited:
            return {
                "name": func_info["name"],
                "file": func_info["file"],
                "line": func_info["line"],
                "calls": [],
                "truncated": current_depth >= max_depth
            }
        
        visited.add(func_key)
        
        # 获取文件路径
        file_path = self.indexer.repo_path / func_info["file"]
        
        # 查找该函数调用的其他函数
        called_functions = self.find_function_calls(file_path, func_info["name"])
        
        calls = []
        for called_func in called_functions:
            # 查找被调用函数的定义
            called_func_infos = self.indexer.search_function(called_func)
            if called_func_infos:
                # 使用第一个匹配项
                sub_tree = self._build_call_tree(
                    called_func_infos[0],
                    max_depth,
                    current_depth + 1,
                    visited.copy()
                )
                calls.append(sub_tree)
        
        return {
            "name": func_info["name"],
            "file": func_info["file"],
            "line": func_info["line"],
            "calls": calls
        }
    
    def analyze_concept(
        self, 
        concept: str, 
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        分析特定概念相关的代码
        
        Args:
            concept: 概念名称（如 "内存分配"）
            keywords: 相关关键字列表（如 ["malloc", "alloc", "kmalloc"]）
        
        Returns:
            分析结果
        """
        logger.info(f"开始分析概念 '{concept}'，关键词: {keywords}")
        
        # 搜索相关函数
        related_functions = []
        for keyword in keywords:
            functions = self.indexer.search_function(keyword)
            related_functions.extend(functions)
        
        # 去重
        unique_functions = {}
        for func in related_functions:
            key = f"{func['file']}:{func['name']}"
            if key not in unique_functions:
                unique_functions[key] = func
        
        # 分析每个函数
        analysis = {
            "concept": concept,
            "keywords": keywords,
            "total_functions": len(unique_functions),
            "functions": []
        }
        
        for func_key, func in unique_functions.items():
            # 获取函数的代码片段
            code_snippet = self.indexer.get_file_content(
                func["file"],
                max(1, func["line"] - 2),
                func["line"] + 10
            )
            
            analysis["functions"].append({
                "name": func["name"],
                "file": func["file"],
                "line": func["line"],
                "snippet": code_snippet[:config.MAX_SNIPPET_LENGTH]
            })
        
        logger.info(f"概念分析完成: 找到 {len(unique_functions)} 个相关函数")
        return analysis
    
    def find_call_path(
        self, 
        from_func: str, 
        to_func: str, 
        max_depth: int = 10
    ) -> List[List[str]]:
        """
        查找从一个函数到另一个函数的调用路径
        
        Args:
            from_func: 起始函数名
            to_func: 目标函数名
            max_depth: 最大搜索深度
        
        Returns:
            所有可能的调用路径列表
        """
        logger.info(f"查找调用路径: {from_func} -> {to_func}")
        
        from_functions = self.indexer.search_function(from_func)
        to_functions = self.indexer.search_function(to_func)
        
        if not from_functions or not to_functions:
            logger.warning("起始或目标函数未找到")
            return []
        
        paths = []
        to_func_names = {f["name"] for f in to_functions}
        
        for start_func in from_functions:
            # BFS 队列：(当前函数信息, 路径)
            queue = deque([(start_func, [start_func["name"]])])
            visited = set()
            
            while queue:
                current_func, path = queue.popleft()
                
                if len(path) > max_depth:
                    continue
                
                func_key = f"{current_func['file']}:{current_func['name']}"
                if func_key in visited:
                    continue
                visited.add(func_key)
                
                # 获取当前函数调用的所有函数
                file_path = self.indexer.repo_path / current_func["file"]
                called_functions = self.find_function_calls(file_path, current_func["name"])
                
                for called_func_name in called_functions:
                    # 检查是否到达目标
                    if called_func_name in to_func_names:
                        paths.append(path + [called_func_name])
                        continue
                    
                    # 继续搜索
                    called_func_infos = self.indexer.search_function(called_func_name)
                    for called_func_info in called_func_infos:
                        new_path = path + [called_func_name]
                        if called_func_name not in path:  # 避免循环
                            queue.append((called_func_info, new_path))
        
        logger.info(f"找到 {len(paths)} 条调用路径")
        return paths
    
    def extract_function_code(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        提取完整的函数代码
        
        Args:
            function_name: 函数名
        
        Returns:
            包含函数代码和元信息的字典
        """
        functions = self.indexer.search_function(function_name)
        
        if not functions:
            return None
        
        func_info = functions[0]
        file_path = self.indexer.repo_path / func_info["file"]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start_line = func_info["line"] - 1
            end_line = func_info.get("end_line", start_line + 50)
            
            # 如果有 end_line 信息，直接使用
            if "end_line" in func_info:
                code = ''.join(lines[start_line:func_info["end_line"]])
            else:
                # 否则尝试通过括号匹配找到结束位置
                end_line = start_line
                brace_count = 0
                found_start = False
                
                for i in range(start_line, min(len(lines), start_line + 200)):
                    line = lines[i]
                    for char in line:
                        if char == '{':
                            brace_count += 1
                            found_start = True
                        elif char == '}':
                            brace_count -= 1
                            if found_start and brace_count == 0:
                                end_line = i
                                break
                    if found_start and brace_count == 0:
                        break
                
                code = ''.join(lines[start_line:end_line + 1])
            
            return {
                "name": func_info["name"],
                "file": func_info["file"],
                "start_line": func_info["line"],
                "end_line": end_line + 1,
                "code": code
            }
        except Exception as e:
            logger.error(f"提取函数代码失败 {function_name}: {e}")
            return {
                "error": str(e),
                "name": func_info["name"],
                "file": func_info["file"]
            }
    
    def get_function_complexity(self, function_name: str) -> Dict[str, Any]:
        """
        分析函数复杂度
        
        Args:
            function_name: 函数名
        
        Returns:
            复杂度分析结果
        """
        func_code = self.extract_function_code(function_name)
        
        if not func_code or "error" in func_code:
            return {"error": "无法获取函数代码"}
        
        code = func_code["code"]
        
        # 计算各种指标
        lines = code.split('\n')
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith(('//', '#', '*'))])
        
        # 控制流语句数量（圈复杂度近似）
        control_keywords = ['if', 'else', 'elif', 'while', 'for', 'switch', 'case', 'except', 'catch']
        control_count = sum(len(re.findall(rf'\b{kw}\b', code)) for kw in control_keywords)
        
        # 函数调用数量
        call_pattern = r'\b([a-zA-Z_]\w*)\s*\('
        calls = len(re.findall(call_pattern, code))
        
        # 圈复杂度 = 1 + 控制流数量
        cyclomatic_complexity = 1 + control_count
        
        return {
            "function": function_name,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "control_structures": control_count,
            "function_calls": calls,
            "cyclomatic_complexity": cyclomatic_complexity,
            "complexity_level": self._get_complexity_level(cyclomatic_complexity)
        }
    
    def _get_complexity_level(self, complexity: int) -> str:
        """获取复杂度等级"""
        if complexity <= 5:
            return "低 (简单)"
        elif complexity <= 10:
            return "中 (适中)"
        elif complexity <= 20:
            return "高 (复杂)"
        else:
            return "非常高 (需要重构)"
