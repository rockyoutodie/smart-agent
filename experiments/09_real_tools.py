"""
Day 4: 真实工具集 - 搜索、文件、代码执行
"""

import json
import io
import contextlib
from pathlib import Path

# 搜索库 import (根据你装的版本二选一)
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


# ============================================================
# 真实工具 1: 网络搜索
# ============================================================

def web_search(query: str, max_results: int = 3) -> str:
    """真实的网络搜索"""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"标题: {r.get('title', '')}\n摘要: {r.get('body', '')}\n来源: {r.get('href', '')}")
        
        if not results:
            return "没有搜索到相关结果"
        
        return "\n\n".join(results)
    except Exception as e:
        return f"搜索失败: {str(e)}"


# ============================================================
# 真实工具 2: 文件写入
# ============================================================

# 安全: 限制只能在指定目录操作
WORK_DIR = Path("./agent_workspace")
WORK_DIR.mkdir(exist_ok=True)

def write_file(filename: str, content: str) -> str:
    """把内容写入文件(仅限工作目录)"""
    try:
        # 安全检查: 防止路径穿越攻击
        safe_name = Path(filename).name  # 只取文件名,去掉路径
        file_path = WORK_DIR / safe_name
        
        file_path.write_text(content, encoding="utf-8")
        return f"已成功写入文件: {file_path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入失败: {str(e)}"


# ============================================================
# 真实工具 3: 文件读取
# ============================================================

def read_file(filename: str) -> str:
    """读取文件内容(仅限工作目录)"""
    try:
        safe_name = Path(filename).name
        file_path = WORK_DIR / safe_name
        
        if not file_path.exists():
            return f"文件不存在: {safe_name}"
        
        content = file_path.read_text(encoding="utf-8")
        return f"文件内容:\n{content}"
    except Exception as e:
        return f"读取失败: {str(e)}"


# ============================================================
# 真实工具 4: Python 代码执行
# ============================================================

def run_python(code: str) -> str:
    """执行 Python 代码并返回输出(有安全限制)"""
    try:
        # 捕获 print 输出
        output_buffer = io.StringIO()
        
        # 受限的执行环境(禁用危险操作)
        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range,
                "sum": sum, "min": min, "max": max, "abs": abs,
                "round": round, "sorted": sorted, "list": list,
                "dict": dict, "set": set, "tuple": tuple,
                "int": int, "float": float, "str": str, "bool": bool,
                "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
            }
        }
        # 允许用 math
        import math
        safe_globals["math"] = math
        
        with contextlib.redirect_stdout(output_buffer):
            exec(code, safe_globals, {})
        
        output = output_buffer.getvalue()
        return f"执行成功,输出:\n{output}" if output else "执行成功(无输出)"
    except Exception as e:
        return f"代码执行错误: {str(e)}"


# ============================================================
# 工具描述
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取实时信息。当用户询问最新新闻、当前事件、实时数据、你不知道的信息时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "返回结果数,默认 3"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "把内容保存到文件。当用户要求保存、记录、导出内容到文件时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "文件名,如 'notes.txt'"},
                    "content": {"type": "string", "description": "要写入的内容"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件内容。当用户要求查看、读取已保存的文件时使用。",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string", "description": "文件名"}},
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "执行 Python 代码。当需要复杂计算、数据处理、生成序列等用简单工具做不到的运算时使用。",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string", "description": "要执行的 Python 代码,用 print 输出结果"}},
                "required": ["code"]
            }
        }
    }
]

available_functions = {
    "web_search": web_search,
    "write_file": write_file,
    "read_file": read_file,
    "run_python": run_python,
}


# ============================================================
# 单独测试每个工具(先确认工具本身能用)
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("测试 1: 网络搜索")
    print("=" * 60)
    print(web_search("Python 3.13 新特性", max_results=2))
    
    print("\n" + "=" * 60)
    print("测试 2: 写文件")
    print("=" * 60)
    print(write_file("test.txt", "这是 Agent 写的第一个文件\n你好世界"))
    
    print("\n" + "=" * 60)
    print("测试 3: 读文件")
    print("=" * 60)
    print(read_file("test.txt"))
    
    print("\n" + "=" * 60)
    print("测试 4: 执行 Python")
    print("=" * 60)
    print(run_python("print(sum(range(1, 101)))"))  # 1 到 100 求和