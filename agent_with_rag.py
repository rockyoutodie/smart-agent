"""
Agent + RAG: 终极形态
在 Day 5 Agent 基础上,增加 search_react_docs 工具
"""

import json
import re
import io
import math
import contextlib
from pathlib import Path
from datetime import datetime
from openai import OpenAI

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# 导入 RAG 工具
from rag_tool import search_react_docs


WORK_DIR = Path("./agent_workspace")
WORK_DIR.mkdir(exist_ok=True)


# ============================================================
# 工具函数(Day 5 的 + RAG)
# ============================================================

def calculator(expression: str) -> str:
    try:
        allowed = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi, "e": math.e}
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"计算错误: {e}"

def web_search(query: str, max_results: int = 3) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                body = r.get('body', '').strip()
                if not body:
                    continue
                results.append(f"标题: {r.get('title','')}\n摘要: {body}")
        return "\n\n".join(results) if results else "没有有效搜索结果"
    except Exception as e:
        return f"搜索失败: {e}"

def write_file(filename: str, content: str) -> str:
    try:
        path = WORK_DIR / Path(filename).name
        path.write_text(content, encoding="utf-8")
        return f"已写入 {path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入失败: {e}"

def read_file(filename: str) -> str:
    try:
        path = WORK_DIR / Path(filename).name
        if not path.exists():
            return f"文件不存在: {Path(filename).name}"
        return f"文件内容:\n{path.read_text(encoding='utf-8')}"
    except Exception as e:
        return f"读取失败: {e}"


# ============================================================
# 工具 Schema(注意 search_react_docs 的描述!)
# ============================================================

TOOLS = [
    {"type": "function", "function": {
        "name": "search_react_docs",
        "description": "从 React 官方文档知识库检索内容。当用户询问 React 相关的技术问题时优先使用此工具,例如 Hooks、组件、状态管理、useState、useEffect、性能优化等。这个知识库是 React 官方文档,比网络搜索更准确权威。",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "检索关键词,用英文效果更好"},
            "top_k": {"type": "integer", "description": "返回文档数,默认 3"}
        }, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "搜索互联网实时信息。当用户问最新新闻、当前事件、非 React 的一般性问题、实时数据时使用。注意:React 技术问题应优先用 search_react_docs。",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "结果数,默认 3"}
        }, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "calculator",
        "description": "精确计算数学表达式。任何数学运算都用它。支持 sqrt。",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]}
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "保存内容到文件。",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "文件名"},
            "content": {"type": "string", "description": "内容"}
        }, "required": ["filename", "content"]}
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "读取文件内容。",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "文件名"}
        }, "required": ["filename"]}
    }},
]

AVAILABLE_FUNCTIONS = {
    "search_react_docs": search_react_docs,
    "web_search": web_search,
    "calculator": calculator,
    "write_file": write_file,
    "read_file": read_file,
}

SYSTEM_PROMPT = """你是一个能干的智能助理,拥有多个知识源和工具:
- search_react_docs: React 官方文档知识库(React 技术问题优先用这个,最权威)
- web_search: 互联网搜索(实时信息、非 React 的一般问题)
- calculator: 精确计算
- write_file / read_file: 文件读写

原则:
1. 根据问题选对知识源:React 技术问题用 search_react_docs,实时/一般信息用 web_search。
2. 多步任务一步步来,用工具获取信息后再决定下一步。
3. 数学运算必须用 calculator,不要心算。
4. 基于检索到的文档回答时,可以标注来源。
5. 充分利用对话历史理解"那个""刚才"等指代。
6. 完成后给出清晰总结。

特别重要 - 关于你的知识边界:
- 你的训练知识有截止日期。对于最新赛事、比分、排名、当前事件、2025年后发生的事,你的记忆很可能过时或错误。
- 遇到这类问题,必须调用 web_search 查证,即使你"觉得"自己知道答案。不要用记忆直接回答时效性问题。
- 判断标准:如果问题涉及"最新""当前""今年""最近""已经"等,或涉及可能变化的事实(赛事结果、人事任命、价格等),一律先搜索再回答。
"""



# ============================================================
# Agent 类(和 Day 5 一样,只是工具变多了)
# ============================================================

class Agent:
    def __init__(self, model="qwen2.5:14b", max_steps=8):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = model
        self.max_steps = max_steps
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    def _extract_fallback(self, text):
        if not text:
            return None
        m = re.search(r'\{"name":\s*"(\w+)",\s*"arguments":\s*(\{.*\})\}', text, re.DOTALL)
        if m:
            try:
                return {"name": m.group(1), "arguments": json.loads(m.group(2))}
            except:
                return None
        return None
    
    def chat(self, user_message: str, verbose=True):
        if verbose:
            print(f"\n👤 你: {user_message}")
        
        self.messages.append({"role": "user", "content": user_message})
        
        for step in range(1, self.max_steps + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=self.messages,
                    tools=TOOLS, tool_choice="auto", temperature=0,
                )
            except Exception as e:
                return f"❌ LLM 调用失败: {e}"
            
            msg = response.choices[0].message
            calls = []
            
            if msg.tool_calls:
                self.messages.append(msg)
                for tc in msg.tool_calls:
                    calls.append({"id": tc.id, "name": tc.function.name,
                                  "args": json.loads(tc.function.arguments)})
            else:
                fb = self._extract_fallback(msg.content)
                if fb:
                    self.messages.append({"role": "assistant", "content": msg.content})
                    calls.append({"id": f"fb_{step}", "name": fb["name"], "args": fb["arguments"]})
                else:
                    self.messages.append({"role": "assistant", "content": msg.content})
                    return msg.content
            
            for tc in calls:
                name, args = tc["name"], tc["args"]
                if verbose:
                    args_d = {k: (v[:50]+"..." if isinstance(v,str) and len(v)>50 else v) for k,v in args.items()}
                    print(f"  🔧 {name}({args_d})")
                
                result = AVAILABLE_FUNCTIONS[name](**args) if name in AVAILABLE_FUNCTIONS else f"未知工具 {name}"
                
                if verbose:
                    print(f"  👁️  {result[:120]}{'...' if len(result)>120 else ''}")
                
                if tc["id"].startswith("fb"):
                    self.messages.append({"role": "user", "content": f"工具 {name} 结果: {result}。请继续。"})
                else:
                    self.messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
        
        return "⚠️ 达到最大步数"
    
    def reset(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# ============================================================
# 测试: 见证 Agent 自己选知识源!
# ============================================================

if __name__ == "__main__":
    agent = Agent()
    
    tests = [
        "useState 和 useEffect 有什么区别?",     # 应该用 search_react_docs
        "2024 年 AI 领域有什么大新闻?",           # 应该用 web_search
        "1024 乘以 768 等于多少?",                # 应该用 calculator
        "React 里怎么做性能优化?把答案保存到 react_perf.txt",  # RAG + 文件, 多步!
    ]
    
    for task in tests:
        agent.chat(task)
        print()
        input("按 Enter 继续...")