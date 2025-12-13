"""代码分析器 - 分析代码流程和调用关系"""
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque


class CodeAnalyzer:
    """代码流程分析器"""
    
    def __init__(self, indexer):
        """
        初始化代码分析器
        
        Args:
            indexer: CodeIndexer 实例
        """
        self.indexer = indexer
        self.call_graph: Dict[str, List[str]] = defaultdict(list)
        self.analyzed_functions: Set[str] = set()
    
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
        except Exception:
            return []
        
        # 找到函数定义的位置
        func_pattern = rf'\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{'
        match = re.search(func_pattern, content)
        
        if not match:
            return []
        
        # 提取函数体（简单的括号匹配）
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
        
        # 查找函数调用（匹配标识符后跟括号）
        call_pattern = r'\b([a-zA-Z_]\w*)\s*\('
        calls = re.findall(call_pattern, function_body)
        
        # 过滤掉一些常见的关键字和宏
        keywords = {'if', 'while', 'for', 'switch', 'sizeof', 'return', 'typeof'}
        calls = [call for call in calls if call not in keywords]
        
        return list(set(calls))  # 去重
    
    def trace_function_flow(self, function_name: str, max_depth: int = 5) -> Dict:
        """
        追踪函数调用流程
        
        Args:
            function_name: 要追踪的函数名
            max_depth: 最大追踪深度
        
        Returns:
            函数调用树
        """
        # 查找函数定义
        functions = self.indexer.search_function(function_name)
        
        if not functions:
            return {"error": f"未找到函数: {function_name}"}
        
        # 使用第一个匹配的函数
        func_info = functions[0]
        
        # 构建调用树
        call_tree = self._build_call_tree(func_info, max_depth)
        
        return {
            "function": func_info["name"],
            "file": func_info["file"],
            "line": func_info["line"],
            "call_tree": call_tree
        }
    
    def _build_call_tree(self, func_info: Dict, max_depth: int, 
                        current_depth: int = 0, visited: Optional[Set[str]] = None) -> Dict:
        """递归构建调用树"""
        if visited is None:
            visited = set()
        
        func_key = f"{func_info['file']}:{func_info['name']}"
        
        if current_depth >= max_depth or func_key in visited:
            return {
                "name": func_info["name"],
                "file": func_info["file"],
                "line": func_info["line"],
                "calls": []
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
    
    def analyze_concept(self, concept: str, keywords: List[str]) -> Dict:
        """
        分析特定概念相关的代码
        
        Args:
            concept: 概念名称（如 "内存分配"）
            keywords: 相关关键字列表（如 ["malloc", "alloc", "kmalloc"]）
        
        Returns:
            分析结果
        """
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
            file_path = self.indexer.repo_path / func["file"]
            
            # 获取函数的代码片段（函数定义周围的几行）
            code_snippet = self.indexer.get_file_content(
                func["file"], 
                max(1, func["line"] - 2), 
                func["line"] + 10
            )
            
            analysis["functions"].append({
                "name": func["name"],
                "file": func["file"],
                "line": func["line"],
                "snippet": code_snippet[:500]  # 限制长度
            })
        
        return analysis
    
    def find_call_path(self, from_func: str, to_func: str, max_depth: int = 10) -> List[List[str]]:
        """
        查找从一个函数到另一个函数的调用路径
        
        Args:
            from_func: 起始函数名
            to_func: 目标函数名
            max_depth: 最大搜索深度
        
        Returns:
            所有可能的调用路径列表
        """
        # BFS 查找所有路径
        from_functions = self.indexer.search_function(from_func)
        to_functions = self.indexer.search_function(to_func)
        
        if not from_functions or not to_functions:
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
        
        return paths
    
    def extract_function_code(self, function_name: str) -> Optional[Dict]:
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
            
            # 找到函数开始
            start_line = func_info["line"] - 1
            
            # 简单查找函数结束（通过括号匹配）
            end_line = start_line
            brace_count = 0
            found_start = False
            
            for i in range(start_line, len(lines)):
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
            return {
                "error": str(e),
                "name": func_info["name"],
                "file": func_info["file"]
            }
    
    def get_function_complexity(self, function_name: str) -> Dict:
        """
        分析函数复杂度（简单指标）
        
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
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('//')])
        
        # 控制流语句数量
        control_keywords = ['if', 'else', 'while', 'for', 'switch', 'case']
        control_count = sum(len(re.findall(rf'\b{kw}\b', code)) for kw in control_keywords)
        
        # 函数调用数量
        call_pattern = r'\b([a-zA-Z_]\w*)\s*\('
        calls = len(re.findall(call_pattern, code))
        
        return {
            "function": function_name,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "control_structures": control_count,
            "function_calls": calls,
            "complexity_score": control_count + calls // 2  # 简单的复杂度评分
        }

