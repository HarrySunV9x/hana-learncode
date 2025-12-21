"""
工作流步骤定义
这个文件保留用于向后兼容
"""

# 步骤名称列表（用于参考）
LEARNCODE_STEP_NAMES = [
    "scan_repository",
    "search_functions",
    "trace_function_flow",
    "analyze_concept",
    "generate_flowchart",
]

# 工作流类型定义
WORKFLOW_TYPES = {
    "function_trace": {
        "name": "函数追踪",
        "description": "追踪函数调用关系并生成流程图",
        "steps": ["scan_repository", "search_functions", "trace_function_flow", "generate_flowchart"]
    },
    "concept_analysis": {
        "name": "概念分析",
        "description": "分析特定概念相关的代码",
        "steps": ["scan_repository", "analyze_concept", "generate_flowchart"]
    }
}

