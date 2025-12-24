"""代码索引器 - 使用 tree-sitter 扫描和索引代码库"""
import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Any

import tree_sitter_python as tspython
import tree_sitter_c as tsc
from tree_sitter import Language, Parser, Node

from core.logger import get_logger
from core.config import config

logger = get_logger("code_indexer")


class TreeSitterParser:
    """Tree-sitter 解析器封装（进程级单例，避免重复初始化）。"""

    _shared: "TreeSitterParser" = None

    @classmethod
    def shared(cls) -> "TreeSitterParser":
        """获取共享实例，降低多会话重复构建开销。"""
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    def __init__(self):
        self._parsers: Dict[str, Parser] = {}
        self._init_parsers()

    def _init_parsers(self):
        """初始化各语言的解析器"""
        # Python 解析器
        py_parser = Parser(Language(tspython.language()))
        self._parsers[".py"] = py_parser

        # C/C++ 解析器
        c_parser = Parser(Language(tsc.language()))
        self._parsers[".c"] = c_parser
        self._parsers[".h"] = c_parser
        self._parsers[".cpp"] = c_parser
        self._parsers[".hpp"] = c_parser

        logger.debug(f"初始化了 {len(self._parsers)} 个语言解析器")

    def get_parser(self, file_extension: str) -> Optional[Parser]:
        """获取指定扩展名的解析器"""
        return self._parsers.get(file_extension)

    def parse(self, content: str, file_extension: str) -> Optional[Node]:
        """解析代码内容，返回 AST 根节点"""
        parser = self.get_parser(file_extension)
        if not parser:
            return None

        tree = parser.parse(bytes(content, "utf-8"))
        return tree.root_node

    def supports(self, file_extension: str) -> bool:
        """检查是否支持该文件扩展名"""
        return file_extension in self._parsers


class CodeIndexer:
    """代码库索引器，用于扫描和索引代码文件"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.files: List[Path] = []
        self.functions: Dict[str, List[Dict[str, Any]]] = {}
        self.structs: Dict[str, List[Dict[str, Any]]] = {}
        self.includes: Dict[str, List[str]] = {}
        
        # 使用配置中的忽略模式
        self.ignore_patterns = config.get_ignore_patterns()
        
        # Tree-sitter 解析器（复用单例，减少资源占用）
        self._ts_parser = TreeSitterParser.shared()
        
        logger.info(f"初始化 CodeIndexer，仓库路径: {self.repo_path}")
    
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
    
    def scan_repository(self, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        扫描代码仓库
        
        Args:
            extensions: 要扫描的文件扩展名列表，如 ['.c', '.h', '.py']
        
        Returns:
            扫描结果统计信息
        """
        if extensions is None:
            extensions = config.get_extensions()
        
        self.files = []
        
        if not self.repo_path.exists():
            logger.error(f"路径不存在: {self.repo_path}")
            raise ValueError(f"路径不存在: {self.repo_path}")
        
        logger.info(f"开始扫描仓库: {self.repo_path}")
        logger.debug(f"扫描扩展名: {extensions}")
        
        # 递归扫描所有文件
        for root, dirs, files in os.walk(self.repo_path):
            # 过滤要忽略的目录
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not self.should_ignore(file_path) and file_path.suffix in extensions:
                    self.files.append(file_path)
        
        result = {
            "total_files": len(self.files),
            "extensions": {
                ext: len([f for f in self.files if f.suffix == ext])
                for ext in extensions if any(f.suffix == ext for f in self.files)
            }
        }
        
        logger.info(f"扫描完成，共 {result['total_files']} 个文件")
        return result
    
    def _extract_python_info(self, root_node: Node, content: str, file_key: str) -> Dict[str, Any]:
        """从 Python AST 提取函数和类信息"""
        functions = []
        classes = []
        imports = []
        
        def visit_node(node: Node):
            if node.type == 'function_definition':
                # 提取函数信息
                name_node = node.child_by_field_name('name')
                params_node = node.child_by_field_name('parameters')
                
                if name_node:
                    func_name = content[name_node.start_byte:name_node.end_byte]
                    params = ""
                    if params_node:
                        params = content[params_node.start_byte:params_node.end_byte]
                    
                    functions.append({
                        "name": func_name,
                        "parameters": params,
                        "line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "file": file_key
                    })
            
            elif node.type == 'class_definition':
                # 提取类信息
                name_node = node.child_by_field_name('name')
                if name_node:
                    class_name = content[name_node.start_byte:name_node.end_byte]
                    classes.append({
                        "name": class_name,
                        "line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "file": file_key
                    })
            
            elif node.type in ('import_statement', 'import_from_statement'):
                # 提取导入语句
                import_text = content[node.start_byte:node.end_byte]
                imports.append(import_text)
            
            # 递归访问子节点
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        
        return {
            "functions": functions,
            "classes": classes,
            "imports": imports
        }
    
    def _extract_c_info(self, root_node: Node, content: str, file_key: str) -> Dict[str, Any]:
        """从 C/C++ AST 提取函数和结构体信息"""
        functions = []
        structs = []
        includes = []
        
        def visit_node(node: Node):
            if node.type == 'function_definition':
                # 提取函数信息
                declarator = node.child_by_field_name('declarator')
                if declarator:
                    # 找到函数名
                    func_name = self._find_function_name(declarator, content)
                    if func_name:
                        # 获取返回类型
                        type_node = node.child_by_field_name('type')
                        return_type = ""
                        if type_node:
                            return_type = content[type_node.start_byte:type_node.end_byte]
                        
                        # 获取参数
                        params = self._find_parameters(declarator, content)
                        
                        functions.append({
                            "name": func_name,
                            "return_type": return_type,
                            "parameters": params,
                            "line": node.start_point[0] + 1,
                            "end_line": node.end_point[0] + 1,
                            "file": file_key
                        })
            
            elif node.type == 'struct_specifier':
                # 提取结构体信息
                name_node = node.child_by_field_name('name')
                if name_node:
                    struct_name = content[name_node.start_byte:name_node.end_byte]
                    structs.append({
                        "name": struct_name,
                        "line": node.start_point[0] + 1,
                        "file": file_key
                    })
            
            elif node.type == 'preproc_include':
                # 提取 include 语句
                path_node = node.child_by_field_name('path')
                if path_node:
                    include_path = content[path_node.start_byte:path_node.end_byte]
                    # 移除引号或尖括号
                    include_path = include_path.strip('"<>')
                    includes.append(include_path)
            
            # 递归访问子节点
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        
        return {
            "functions": functions,
            "structs": structs,
            "includes": includes
        }
    
    def _find_function_name(self, declarator: Node, content: str) -> Optional[str]:
        """从声明器中提取函数名"""
        if declarator.type == 'identifier':
            return content[declarator.start_byte:declarator.end_byte]
        
        if declarator.type == 'function_declarator':
            inner = declarator.child_by_field_name('declarator')
            if inner:
                return self._find_function_name(inner, content)
        
        if declarator.type == 'pointer_declarator':
            inner = declarator.child_by_field_name('declarator')
            if inner:
                return self._find_function_name(inner, content)
        
        # 遍历子节点查找
        for child in declarator.children:
            if child.type == 'identifier':
                return content[child.start_byte:child.end_byte]
            result = self._find_function_name(child, content)
            if result:
                return result
        
        return None
    
    def _find_parameters(self, declarator: Node, content: str) -> str:
        """从声明器中提取参数列表"""
        if declarator.type == 'function_declarator':
            params_node = declarator.child_by_field_name('parameters')
            if params_node:
                return content[params_node.start_byte:params_node.end_byte]
        
        for child in declarator.children:
            result = self._find_parameters(child, content)
            if result:
                return result
        
        return ""
    
    def index_file(self, file_path: Path) -> Dict[str, Any]:
        """索引单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return {"error": str(e)}
        
        file_key = str(file_path.relative_to(self.repo_path))
        suffix = file_path.suffix
        
        # 检查是否支持 tree-sitter 解析
        if self._ts_parser.supports(suffix):
            root_node = self._ts_parser.parse(content, suffix)
            if root_node:
                if suffix == '.py':
                    info = self._extract_python_info(root_node, content, file_key)
                    self.functions[file_key] = info["functions"]
                    self.structs[file_key] = info["classes"]
                    self.includes[file_key] = info["imports"]
                    return {
                        "functions": len(info["functions"]),
                        "classes": len(info["classes"]),
                        "imports": len(info["imports"])
                    }
                else:  # C/C++
                    info = self._extract_c_info(root_node, content, file_key)
                    self.functions[file_key] = info["functions"]
                    self.structs[file_key] = info["structs"]
                    self.includes[file_key] = info["includes"]
                    return {
                        "functions": len(info["functions"]),
                        "structs": len(info["structs"]),
                        "includes": len(info["includes"])
                    }
        
        # 回退到正则表达式解析（用于不支持的语言）
        return self._index_file_regex(file_path, content, file_key)
    
    def _index_file_regex(self, file_path: Path, content: str, file_key: str) -> Dict[str, Any]:
        """使用正则表达式索引文件（回退方案）"""
        import re
        
        suffix = file_path.suffix
        functions = []
        structs = []
        includes = []
        
        if suffix in ['.js', '.ts']:
            # JavaScript/TypeScript 函数
            func_patterns = [
                r'function\s+(\w+)\s*\(([^)]*)\)',  # function name()
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>',  # arrow function
                r'(\w+)\s*:\s*(?:async\s*)?function\s*\(([^)]*)\)',  # method: function()
            ]
            for pattern in func_patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    functions.append({
                        "name": match.group(1),
                        "parameters": match.group(2) if len(match.groups()) > 1 else "",
                        "line": line_num,
                        "file": file_key
                    })
            
            # 类定义
            class_pattern = r'class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                structs.append({
                    "name": match.group(1),
                    "line": line_num,
                    "file": file_key
                })
            
            # import 语句
            import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            for match in re.finditer(import_pattern, content):
                includes.append(match.group(1))
        
        elif suffix in ['.go']:
            # Go 函数
            func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(([^)]*)\)'
            for match in re.finditer(func_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                functions.append({
                    "name": match.group(1),
                    "parameters": match.group(2),
                    "line": line_num,
                    "file": file_key
                })
            
            # 结构体
            struct_pattern = r'type\s+(\w+)\s+struct'
            for match in re.finditer(struct_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                structs.append({
                    "name": match.group(1),
                    "line": line_num,
                    "file": file_key
                })
        
        elif suffix in ['.java']:
            # Java 方法
            method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+\w+(?:,\s*\w+)*)?\s*\{'
            for match in re.finditer(method_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                functions.append({
                    "name": match.group(1),
                    "parameters": match.group(2),
                    "line": line_num,
                    "file": file_key
                })
            
            # 类定义
            class_pattern = r'(?:public|private)?\s*class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                structs.append({
                    "name": match.group(1),
                    "line": line_num,
                    "file": file_key
                })
        
        self.functions[file_key] = functions
        self.structs[file_key] = structs
        self.includes[file_key] = includes
        
        return {
            "functions": len(functions),
            "structs": len(structs),
            "includes": len(includes)
        }
    
    def index_all_files(self) -> Dict[str, Any]:
        """索引所有已扫描的文件"""
        results = {
            "indexed": 0,
            "errors": 0,
            "total_functions": 0,
            "total_structs": 0
        }
        
        logger.info(f"开始索引 {len(self.files)} 个文件")
        
        for file_path in self.files:
            try:
                self.index_file(file_path)
                results["indexed"] += 1
            except Exception as e:
                logger.warning(f"索引文件失败 {file_path}: {e}")
                results["errors"] += 1
        
        results["total_functions"] = sum(len(funcs) for funcs in self.functions.values())
        results["total_structs"] = sum(len(structs) for structs in self.structs.values())
        
        logger.info(f"索引完成: {results['indexed']} 文件, "
                   f"{results['total_functions']} 函数, {results['total_structs']} 结构体/类")
        
        return results
    
    def search_function(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索函数名包含关键字的所有函数"""
        results = []
        keyword_lower = keyword.lower()
        
        for file_key, functions in self.functions.items():
            for func in functions:
                if keyword_lower in func["name"].lower():
                    results.append(func)
        
        logger.debug(f"搜索 '{keyword}' 找到 {len(results)} 个函数")
        return results
    
    def search_struct(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索结构体/类名包含关键字的所有定义"""
        results = []
        keyword_lower = keyword.lower()
        
        for file_key, structs in self.structs.items():
            for struct in structs:
                if keyword_lower in struct["name"].lower():
                    results.append(struct)
        
        logger.debug(f"搜索 '{keyword}' 找到 {len(results)} 个结构体/类")
        return results
    
    def get_file_content(
        self, 
        file_key: str, 
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> str:
        """获取文件内容"""
        file_path = self.repo_path / file_key
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if start_line is None and end_line is None:
                    return f.read()
                
                lines = f.readlines()
                if start_line is not None and end_line is not None:
                    return ''.join(lines[start_line - 1:end_line])
                elif start_line is not None:
                    return ''.join(lines[start_line - 1:])
                else:
                    return ''.join(lines[:end_line])
        except Exception as e:
            logger.error(f"读取文件内容失败 {file_key}: {e}")
            return f"Error reading file: {e}"
    
    def get_all_functions(self) -> List[Dict[str, Any]]:
        """获取所有函数列表"""
        all_functions = []
        for funcs in self.functions.values():
            all_functions.extend(funcs)
        return all_functions
    
    def get_all_structs(self) -> List[Dict[str, Any]]:
        """获取所有结构体/类列表"""
        all_structs = []
        for structs in self.structs.values():
            all_structs.extend(structs)
        return all_structs
