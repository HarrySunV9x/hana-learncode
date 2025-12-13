"""代码索引器 - 扫描和索引代码库"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
import fnmatch


class CodeIndexer:
    """代码库索引器，用于扫描和索引代码文件"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.files: List[Path] = []
        self.functions: Dict[str, List[Dict]] = {}
        self.structs: Dict[str, List[Dict]] = {}
        self.includes: Dict[str, List[str]] = {}
        
        # 常见的要忽略的目录和文件
        self.ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            '*.pyc', '*.pyo', '*.so', '*.o', '*.a', '*.exe',
            '.DS_Store', 'Thumbs.db'
        ]
    
    def should_ignore(self, path: Path) -> bool:
        """检查路径是否应该被忽略"""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
            # 检查父目录
            for parent in path.parents:
                if fnmatch.fnmatch(parent.name, pattern):
                    return True
        return False
    
    def scan_repository(self, extensions: Optional[List[str]] = None) -> Dict:
        """
        扫描代码仓库
        
        Args:
            extensions: 要扫描的文件扩展名列表，如 ['.c', '.h', '.py']
        
        Returns:
            扫描结果统计信息
        """
        if extensions is None:
            extensions = ['.c', '.h', '.cpp', '.hpp', '.py', '.java', '.js', '.ts']
        
        self.files = []
        
        if not self.repo_path.exists():
            raise ValueError(f"路径不存在: {self.repo_path}")
        
        # 递归扫描所有文件
        for root, dirs, files in os.walk(self.repo_path):
            # 过滤要忽略的目录
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not self.should_ignore(file_path) and file_path.suffix in extensions:
                    self.files.append(file_path)
        
        return {
            "total_files": len(self.files),
            "extensions": {ext: len([f for f in self.files if f.suffix == ext]) 
                          for ext in extensions if any(f.suffix == ext for f in self.files)}
        }
    
    def index_c_file(self, file_path: Path) -> Dict:
        """索引 C/C++ 文件，提取函数和结构体定义"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        file_key = str(file_path.relative_to(self.repo_path))
        
        # 提取函数定义（简单的正则匹配）
        # 匹配形如: type function_name(params) {
        function_pattern = r'^\s*(?:static\s+)?(?:inline\s+)?(\w+\s*\*?\s+)(\w+)\s*\(([^)]*)\)\s*\{'
        functions = []
        
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            return_type = match.group(1).strip()
            func_name = match.group(2)
            params = match.group(3).strip()
            line_num = content[:match.start()].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "return_type": return_type,
                "parameters": params,
                "line": line_num,
                "file": file_key
            })
        
        self.functions[file_key] = functions
        
        # 提取结构体定义
        struct_pattern = r'^\s*struct\s+(\w+)\s*\{'
        structs = []
        
        for match in re.finditer(struct_pattern, content, re.MULTILINE):
            struct_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            structs.append({
                "name": struct_name,
                "line": line_num,
                "file": file_key
            })
        
        self.structs[file_key] = structs
        
        # 提取 include 语句
        include_pattern = r'^\s*#include\s+[<"]([^>"]+)[>"]'
        includes = []
        
        for match in re.finditer(include_pattern, content, re.MULTILINE):
            includes.append(match.group(1))
        
        self.includes[file_key] = includes
        
        return {
            "functions": len(functions),
            "structs": len(structs),
            "includes": len(includes)
        }
    
    def index_python_file(self, file_path: Path) -> Dict:
        """索引 Python 文件，提取函数和类定义"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        file_key = str(file_path.relative_to(self.repo_path))
        
        # 提取函数定义
        function_pattern = r'^\s*def\s+(\w+)\s*\(([^)]*)\)\s*(?:->.*)?:'
        functions = []
        
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            func_name = match.group(1)
            params = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "line": line_num,
                "file": file_key
            })
        
        self.functions[file_key] = functions
        
        # 提取类定义
        class_pattern = r'^\s*class\s+(\w+)\s*(?:\([^)]*\))?:'
        structs = []
        
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            structs.append({
                "name": class_name,
                "line": line_num,
                "file": file_key
            })
        
        self.structs[file_key] = structs
        
        # 提取 import 语句
        import_pattern = r'^\s*(?:from\s+[\w.]+\s+)?import\s+(.+)'
        includes = []
        
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            includes.append(match.group(1).strip())
        
        self.includes[file_key] = includes
        
        return {
            "functions": len(functions),
            "classes": len(structs),
            "imports": len(includes)
        }
    
    def index_all_files(self) -> Dict:
        """索引所有已扫描的文件"""
        results = {
            "indexed": 0,
            "errors": 0,
            "total_functions": 0,
            "total_structs": 0
        }
        
        for file_path in self.files:
            try:
                if file_path.suffix in ['.c', '.h', '.cpp', '.hpp']:
                    self.index_c_file(file_path)
                elif file_path.suffix == '.py':
                    self.index_python_file(file_path)
                results["indexed"] += 1
            except Exception as e:
                results["errors"] += 1
        
        results["total_functions"] = sum(len(funcs) for funcs in self.functions.values())
        results["total_structs"] = sum(len(structs) for structs in self.structs.values())
        
        return results
    
    def search_function(self, keyword: str) -> List[Dict]:
        """搜索函数名包含关键字的所有函数"""
        results = []
        for file_key, functions in self.functions.items():
            for func in functions:
                if keyword.lower() in func["name"].lower():
                    results.append(func)
        return results
    
    def search_struct(self, keyword: str) -> List[Dict]:
        """搜索结构体/类名包含关键字的所有定义"""
        results = []
        for file_key, structs in self.structs.items():
            for struct in structs:
                if keyword.lower() in struct["name"].lower():
                    results.append(struct)
        return results
    
    def get_file_content(self, file_key: str, start_line: Optional[int] = None, 
                        end_line: Optional[int] = None) -> str:
        """获取文件内容"""
        file_path = self.repo_path / file_key
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if start_line is None and end_line is None:
                    return f.read()
                
                lines = f.readlines()
                if start_line is not None and end_line is not None:
                    return ''.join(lines[start_line-1:end_line])
                elif start_line is not None:
                    return ''.join(lines[start_line-1:])
                else:
                    return ''.join(lines[:end_line])
        except Exception as e:
            return f"Error reading file: {e}"

