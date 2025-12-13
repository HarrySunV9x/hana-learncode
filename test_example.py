"""
测试示例 - 用于验证 MCP 服务器功能

这个脚本可以独立运行，不需要 MCP 客户端，用于快速测试核心功能。
"""

import asyncio
import json
from pathlib import Path

# 导入核心模块
from core.code_indexer import CodeIndexer
from core.code_analyzer import CodeAnalyzer
from core.flowchart_generator import FlowchartGenerator


async def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试 Hana LearnCode 基本功能")
    print("=" * 60)
    
    # 使用当前项目作为测试对象
    repo_path = Path(__file__).parent
    print(f"\n📁 测试项目路径: {repo_path}")
    
    # 1. 测试代码索引器
    print("\n" + "=" * 60)
    print("1. 测试代码索引器")
    print("=" * 60)
    
    indexer = CodeIndexer(str(repo_path))
    scan_result = indexer.scan_repository(['.py'])
    print(f"✓ 扫描完成: 找到 {scan_result['total_files']} 个 Python 文件")
    
    index_result = indexer.index_all_files()
    print(f"✓ 索引完成: {index_result['indexed']} 个文件")
    print(f"  - 函数总数: {index_result['total_functions']}")
    print(f"  - 类总数: {index_result['total_structs']}")
    
    # 2. 测试函数搜索
    print("\n" + "=" * 60)
    print("2. 测试函数搜索")
    print("=" * 60)
    
    search_keyword = "scan"
    functions = indexer.search_function(search_keyword)
    print(f"✓ 搜索关键字 '{search_keyword}' 找到 {len(functions)} 个函数:")
    for func in functions[:5]:  # 只显示前5个
        print(f"  - {func['name']} ({func['file']}:{func['line']})")
    
    # 3. 测试代码分析器
    print("\n" + "=" * 60)
    print("3. 测试代码分析器")
    print("=" * 60)
    
    analyzer = CodeAnalyzer(indexer)
    
    if functions:
        test_func = functions[0]['name']
        print(f"✓ 追踪函数 '{test_func}' 的调用流程...")
        
        try:
            flow = analyzer.trace_function_flow(test_func, max_depth=2)
            if "error" not in flow:
                print(f"  ✓ 成功追踪函数调用树")
                print(f"  - 函数: {flow['function']}")
                print(f"  - 文件: {flow['file']}")
                print(f"  - 行号: {flow['line']}")
            else:
                print(f"  ⚠ {flow['error']}")
        except Exception as e:
            print(f"  ⚠ 追踪失败: {e}")
    
    # 4. 测试概念分析
    print("\n" + "=" * 60)
    print("4. 测试概念分析")
    print("=" * 60)
    
    concept = "代码索引"
    keywords = ["index", "scan", "search"]
    analysis = analyzer.analyze_concept(concept, keywords)
    print(f"✓ 分析概念 '{concept}'")
    print(f"  - 相关函数数量: {analysis['total_functions']}")
    if analysis['functions']:
        print(f"  - 示例函数:")
        for func in analysis['functions'][:3]:
            print(f"    • {func['name']} ({func['file']}:{func['line']})")
    
    # 5. 测试流程图生成
    print("\n" + "=" * 60)
    print("5. 测试流程图生成")
    print("=" * 60)
    
    generator = FlowchartGenerator()
    
    # 生成简单流程图
    steps = [
        "用户发送请求",
        "扫描代码仓库",
        "建立索引",
        "分析代码",
        "生成流程图",
        "返回结果"
    ]
    
    flowchart = generator.generate_simple_flowchart(steps)
    print("✓ 生成简单流程图:")
    print("\n```mermaid")
    print(flowchart)
    print("```\n")
    
    # 如果有函数调用树，生成调用树流程图
    if functions and 'flow' in locals() and "error" not in flow:
        try:
            call_tree_chart = generator.generate_call_tree_flowchart(flow['call_tree'])
            print("✓ 生成函数调用树流程图:")
            print("\n```mermaid")
            print(call_tree_chart[:500] + "..." if len(call_tree_chart) > 500 else call_tree_chart)
            print("```\n")
        except Exception as e:
            print(f"⚠ 生成调用树流程图失败: {e}")
    
    # 6. 测试函数代码提取
    print("\n" + "=" * 60)
    print("6. 测试函数代码提取")
    print("=" * 60)
    
    if functions:
        test_func = functions[0]['name']
        func_code = analyzer.extract_function_code(test_func)
        
        if func_code and "error" not in func_code:
            print(f"✓ 提取函数 '{test_func}' 的代码:")
            print(f"  - 文件: {func_code['file']}")
            print(f"  - 行号: {func_code['start_line']} - {func_code['end_line']}")
            print(f"  - 代码长度: {len(func_code['code'])} 字符")
            print("\n代码预览（前200字符）:")
            print(func_code['code'][:200] + "..." if len(func_code['code']) > 200 else func_code['code'])
        else:
            print(f"⚠ 无法提取函数代码")
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
    print("\n🎉 核心功能运行正常，可以开始使用 MCP 服务器了！")
    print("\n下一步:")
    print("  1. 配置 Claude Desktop (参考 QUICKSTART.md)")
    print("  2. 重启 Claude Desktop")
    print("  3. 开始学习代码!")
    print()


async def test_with_custom_repo():
    """使用自定义仓库进行测试"""
    print("\n" + "=" * 60)
    print("自定义仓库测试")
    print("=" * 60)
    
    # 提示用户输入路径
    print("\n如果你想测试其他代码仓库，请输入路径（直接回车跳过）:")
    custom_path = input("代码仓库路径: ").strip()
    
    if not custom_path:
        print("跳过自定义仓库测试")
        return
    
    if not Path(custom_path).exists():
        print(f"⚠ 路径不存在: {custom_path}")
        return
    
    print(f"\n开始测试: {custom_path}")
    
    # 询问文件扩展名
    print("\n输入要扫描的文件扩展名（如 .c,.h 或直接回车使用默认）:")
    extensions_input = input("扩展名: ").strip()
    
    extensions = None
    if extensions_input:
        extensions = [ext.strip() if ext.strip().startswith('.') else f'.{ext.strip()}' 
                     for ext in extensions_input.split(',')]
    
    indexer = CodeIndexer(custom_path)
    
    print("\n扫描中...")
    scan_result = indexer.scan_repository(extensions)
    print(f"✓ 扫描完成: {scan_result['total_files']} 个文件")
    
    print("\n索引中...")
    index_result = indexer.index_all_files()
    print(f"✓ 索引完成:")
    print(f"  - 索引文件: {index_result['indexed']}")
    print(f"  - 函数总数: {index_result['total_functions']}")
    print(f"  - 结构体/类: {index_result['total_structs']}")
    
    # 让用户搜索函数
    print("\n输入要搜索的函数关键字（直接回车跳过）:")
    search_term = input("关键字: ").strip()
    
    if search_term:
        functions = indexer.search_function(search_term)
        print(f"\n找到 {len(functions)} 个函数:")
        for func in functions[:10]:
            print(f"  - {func['name']} ({func['file']}:{func['line']})")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         Hana LearnCode - 功能测试脚本                      ║
    ║         Code Learning Assistant - Test Script             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # 运行基本测试
    asyncio.run(test_basic_functionality())
    
    # 可选：测试自定义仓库
    try:
        asyncio.run(test_with_custom_repo())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n⚠ 发生错误: {e}")
    
    print("\n感谢使用！👋\n")

