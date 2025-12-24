"""流程图生成器 - 生成 Mermaid 格式的流程图"""
from typing import Dict, List, Optional, Any

from core.logger import get_logger

logger = get_logger("flowchart_generator")


class FlowchartGenerator:
    """流程图生成器，生成 Mermaid 格式的流程图"""
    
    def __init__(self):
        self.node_counter: int = 0
        self.node_map: Dict[str, str] = {}
    
    def _get_node_id(self, name: str) -> str:
        """获取或创建节点 ID"""
        if name not in self.node_map:
            self.node_counter += 1
            self.node_map[name] = f"node{self.node_counter}"
        return self.node_map[name]
    
    def _sanitize_label(self, text: str, max_length: int = 50) -> str:
        """
        清理标签文本，避免 Mermaid 语法错误
        
        Args:
            text: 原始文本
            max_length: 最大长度
        
        Returns:
            清理后的文本
        """
        # 移除或转义特殊字符
        text = text.replace('"', "'")
        text = text.replace('\n', ' ')
        text = text.replace('\r', '')
        text = text.replace('(', '[')
        text = text.replace(')', ']')
        return text[:max_length]
    
    def _reset(self):
        """重置生成器状态"""
        self.node_counter = 0
        self.node_map = {}
    
    def generate_call_tree_flowchart(
        self, 
        call_tree: Dict[str, Any], 
        direction: str = "TD"
    ) -> str:
        """
        从调用树生成流程图
        
        Args:
            call_tree: 函数调用树
            direction: 图的方向 (TD=上到下, LR=左到右)
        
        Returns:
            Mermaid 格式的流程图代码
        """
        self._reset()
        
        logger.debug(f"生成调用树流程图，方向: {direction}")
        
        mermaid = [f"graph {direction}"]
        
        # 递归生成节点和边
        self._add_call_tree_nodes(call_tree, mermaid)
        
        return "\n".join(mermaid)
    
    def _add_call_tree_nodes(
        self, 
        node: Dict[str, Any], 
        mermaid: List[str], 
        parent_id: Optional[str] = None
    ):
        """递归添加调用树节点"""
        name = node.get("name", "unknown")
        file = node.get("file", "")
        line = node.get("line", 0)
        
        # 创建节点
        node_id = self._get_node_id(f"{file}:{name}")
        
        # 文件名简化
        file_name = file.split('/')[-1] if file else ""
        label = f"{name}\\n({file_name}:{line})" if file_name else name
        label = self._sanitize_label(label)
        
        # 根节点使用不同的样式
        if parent_id is None:
            mermaid.append(f'    {node_id}["{label}"]')
            mermaid.append(f"    style {node_id} fill:#f9f,stroke:#333,stroke-width:4px")
        else:
            mermaid.append(f'    {node_id}["{label}"]')
            mermaid.append(f"    {parent_id} --> {node_id}")
        
        # 处理子调用
        calls = node.get("calls", [])
        for call in calls:
            self._add_call_tree_nodes(call, mermaid, node_id)
    
    def generate_function_path_flowchart(
        self, 
        paths: List[List[str]], 
        direction: str = "LR"
    ) -> str:
        """
        从函数调用路径生成流程图
        
        Args:
            paths: 函数调用路径列表
            direction: 图的方向
        
        Returns:
            Mermaid 格式的流程图代码
        """
        if not paths:
            return "graph LR\n    A[未找到路径]"
        
        self._reset()
        
        logger.debug(f"生成路径流程图，共 {len(paths)} 条路径")
        
        mermaid = [f"graph {direction}"]
        
        # 为每条路径生成节点和边
        for path_idx, path in enumerate(paths):
            if not path:
                continue
            
            # 添加路径子图（多条路径时）
            if len(paths) > 1:
                mermaid.append(f"    subgraph Path{path_idx + 1}")
            
            prev_id = None
            for func_name in path:
                node_id = self._get_node_id(f"path{path_idx}_{func_name}")
                label = self._sanitize_label(func_name)
                mermaid.append(f'    {node_id}["{label}"]')
                
                if prev_id:
                    mermaid.append(f"    {prev_id} --> {node_id}")
                
                prev_id = node_id
            
            if len(paths) > 1:
                mermaid.append("    end")
        
        return "\n".join(mermaid)
    
    def generate_concept_flowchart(
        self, 
        analysis: Dict[str, Any], 
        direction: str = "TD"
    ) -> str:
        """
        从概念分析生成流程图
        
        Args:
            analysis: 概念分析结果
            direction: 图的方向
        
        Returns:
            Mermaid 格式的流程图代码
        """
        concept = analysis.get("concept", "Concept")
        functions = analysis.get("functions", [])
        
        if not functions:
            return f"graph {direction}\n    A[{concept}]\n    B[未找到相关函数]"
        
        self._reset()
        
        logger.debug(f"生成概念流程图: {concept}, 函数数: {len(functions)}")
        
        mermaid = [f"graph {direction}"]
        
        # 中心概念节点
        concept_id = "concept"
        mermaid.append(f'    {concept_id}["{self._sanitize_label(concept)}"]')
        mermaid.append(f"    style {concept_id} fill:#ff9,stroke:#333,stroke-width:4px")
        
        # 按文件分组
        files: Dict[str, List[Dict]] = {}
        for func in functions:
            file = func.get("file", "unknown")
            if file not in files:
                files[file] = []
            files[file].append(func)
        
        # 为每个文件创建子图
        for file_idx, (file, file_funcs) in enumerate(files.items()):
            file_name = file.split('/')[-1]
            safe_name = self._sanitize_label(file_name).replace(' ', '_').replace('.', '_')
            mermaid.append(f"    subgraph {safe_name}")
            
            for func in file_funcs:
                func_name = func.get("name", "unknown")
                line = func.get("line", 0)
                
                node_id = self._get_node_id(f"{file}:{func_name}")
                label = f"{func_name}\\n[L{line}]"
                mermaid.append(f'    {node_id}["{self._sanitize_label(label)}"]')
                mermaid.append(f"    {concept_id} -.-> {node_id}")
            
            mermaid.append("    end")
        
        return "\n".join(mermaid)
    
    def generate_simple_flowchart(
        self, 
        steps: List[str], 
        direction: str = "TD"
    ) -> str:
        """
        生成简单的步骤流程图
        
        Args:
            steps: 步骤列表
            direction: 图的方向
        
        Returns:
            Mermaid 格式的流程图代码
        """
        if not steps:
            return "graph TD\n    A[空流程]"
        
        self._reset()
        
        mermaid = [f"graph {direction}"]
        
        prev_id = None
        for idx, step in enumerate(steps):
            node_id = f"step{idx + 1}"
            label = self._sanitize_label(step)
            
            # 第一步和最后一步使用特殊形状
            if idx == 0:
                mermaid.append(f'    {node_id}(["{label}"])')
                mermaid.append(f"    style {node_id} fill:#9f9,stroke:#333,stroke-width:2px")
            elif idx == len(steps) - 1:
                mermaid.append(f'    {node_id}(["{label}"])')
                mermaid.append(f"    style {node_id} fill:#f99,stroke:#333,stroke-width:2px")
            else:
                mermaid.append(f'    {node_id}["{label}"]')
            
            if prev_id:
                mermaid.append(f"    {prev_id} --> {node_id}")
            
            prev_id = node_id
        
        return "\n".join(mermaid)
    
    def generate_module_dependency_graph(
        self, 
        includes: Dict[str, List[str]],
        direction: str = "LR"
    ) -> str:
        """
        生成模块依赖关系图
        
        Args:
            includes: 文件的包含/导入关系字典
            direction: 图的方向
        
        Returns:
            Mermaid 格式的流程图代码
        """
        if not includes:
            return "graph LR\n    A[无依赖关系]"
        
        self._reset()
        
        logger.debug(f"生成依赖图，模块数: {len(includes)}")
        
        mermaid = [f"graph {direction}"]
        declared_nodes = set()
        
        # 创建所有节点和边
        for file, deps in includes.items():
            file_name = file.split('/')[-1]
            file_id = self._get_node_id(file)
            
            if file_id not in declared_nodes:
                mermaid.append(f'    {file_id}["{self._sanitize_label(file_name)}"]')
                declared_nodes.add(file_id)
            
            for dep in deps:
                dep_name = dep.split('/')[-1]
                dep_id = self._get_node_id(dep)
                
                if dep_id not in declared_nodes:
                    mermaid.append(f'    {dep_id}["{self._sanitize_label(dep_name)}"]')
                    declared_nodes.add(dep_id)
                
                mermaid.append(f"    {file_id} --> {dep_id}")
        
        return "\n".join(mermaid)
    
    def generate_sequence_diagram(self, call_sequence: List[Dict[str, Any]]) -> str:
        """
        生成时序图
        
        Args:
            call_sequence: 函数调用序列，每项包含 caller, callee, message
        
        Returns:
            Mermaid 格式的时序图代码
        """
        if not call_sequence:
            return "sequenceDiagram\n    participant A\n    A->>A: Empty"
        
        logger.debug(f"生成时序图，调用数: {len(call_sequence)}")
        
        mermaid = ["sequenceDiagram"]
        
        # 收集所有参与者
        participants = set()
        for call in call_sequence:
            participants.add(call.get("caller", "Unknown"))
            participants.add(call.get("callee", "Unknown"))
        
        # 声明参与者
        for participant in sorted(participants):
            safe_name = self._sanitize_label(participant).replace(' ', '_')
            mermaid.append(f"    participant {safe_name}")
        
        # 添加调用序列
        for call in call_sequence:
            caller = self._sanitize_label(call.get("caller", "Unknown")).replace(' ', '_')
            callee = self._sanitize_label(call.get("callee", "Unknown")).replace(' ', '_')
            message = self._sanitize_label(call.get("message", "call"), 30)
            
            mermaid.append(f"    {caller}->>{callee}: {message}")
        
        return "\n".join(mermaid)
    
    def generate_class_diagram(self, classes: List[Dict[str, Any]]) -> str:
        """
        生成类图
        
        Args:
            classes: 类信息列表，每项包含 name, methods, attributes
        
        Returns:
            Mermaid 格式的类图代码
        """
        if not classes:
            return "classDiagram\n    class Empty"
        
        logger.debug(f"生成类图，类数: {len(classes)}")
        
        mermaid = ["classDiagram"]
        
        for cls in classes:
            class_name = self._sanitize_label(cls.get("name", "Unknown"), 30)
            mermaid.append(f"    class {class_name} {{")
            
            # 添加属性
            for attr in cls.get("attributes", []):
                mermaid.append(f"        +{self._sanitize_label(attr, 40)}")
            
            # 添加方法
            for method in cls.get("methods", []):
                mermaid.append(f"        +{self._sanitize_label(method, 40)}()")
            
            mermaid.append("    }")
        
        return "\n".join(mermaid)
