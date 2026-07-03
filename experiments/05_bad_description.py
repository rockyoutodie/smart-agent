"""
Day 2 实验 3: 工具描述的重要性
对比: 清晰描述 vs 模糊描述
"""

import json
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def search_docs(query: str) -> str:
    return f"[文档搜索结果] 关于'{query}'的内容..."


def search_web(query: str) -> str:
    return f"[网络搜索结果] 关于'{query}'的最新信息..."


# ===== 版本 A: 模糊描述(两个工具描述几乎一样) =====
tools_vague = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "搜索信息",   # ← 太模糊!
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索信息",   # ← 和上面一模一样!
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }
]

# ===== 版本 B: 清晰描述 =====
tools_clear = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "搜索本地 React 技术文档。当用户问 React 相关的技术问题、API 用法、组件知识时使用。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索互联网获取实时信息。当用户问最新新闻、当前事件、实时数据等本地文档没有的内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }
]


def test_tool_selection(tools, label, query):
    response = client.chat.completions.create(
        model="qwen2.5:14b",
        messages=[{"role": "user", "content": query}],
        tools=tools,
        tool_choice="auto",
    )
    
    msg = response.choices[0].message
    if msg.tool_calls:
        chosen = msg.tool_calls[0].function.name
        print(f"  [{label}] 问题: '{query}' → LLM 选了: {chosen}")
    else:
        print(f"  [{label}] 问题: '{query}' → 没选工具")


if __name__ == "__main__":
    queries = [
        "useState 怎么用?",        # 应该选 search_docs
        "今天有什么科技新闻?",      # 应该选 search_web
    ]
    
    print("=" * 70)
    print("对比实验: 模糊描述 vs 清晰描述")
    print("=" * 70)
    
    for query in queries:
        print(f"\n问题: {query}")
        test_tool_selection(tools_vague, "模糊", query)
        test_tool_selection(tools_clear, "清晰", query)