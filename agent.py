"""
完整智能助理 Agent - 整合所有工具 + 对话记忆
"""

import json
import re
import io
import math
import contextlib
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# 搜索库
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


# ============================================================
# 工具定义
# ============================================================

WORK_DIR = Path("./agent_workspace")
WORK_DIR.mkdir(exist_ok=True)


def calculator(expression: str) -> str:
    try:
        allowed = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi, "e": math.e}
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"计算错误: {e}"


def get_current_time() -> str:
    return f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def web_search(query: str, max_results: int = 3) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                body = r.get('body', '').strip()
                if not body:   # 过滤空摘要(Day 4 学到的清洗)
                    continue
                results.append(f"标题: {r.get('title','')}\n摘要: {body}")
        return "\n\n".join(results) if results else "没有有效搜索结果"
    except Exception as e:
        return f"搜索失败: {e}"


def write_file(filename: str, content: str) -> str:
    try:
        safe = Path(filename).name
        path = WORK_DIR / safe
        path.write_text(content, encoding="utf-8")
        return f"已写入 {path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入失败: {e}"


def read_file(filename: str) -> str:
    try:
        safe = Path(filename).name
        path = WORK_DIR / safe
        if not path.exists():
            return f"文件不存在: {safe}"
        return f"文件内容:\n{path.read_text(encoding='utf-8')}"
    except Exception as e:
        return f"读取失败: {e}"


def run_python(code: str) -> str:
    try:
        buf = io.StringIO()
        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range, "sum": sum,
                "min": min, "max": max, "abs": abs, "round": round,
                "sorted": sorted, "list": list, "dict": dict, "set": set,
                "tuple": tuple, "int": int, "float": float, "str": str,
                "bool": bool, "enumerate": enumerate, "zip": zip,
                "map": map, "filter": filter,
            },
            "math": math,
        }
        with contextlib.redirect_stdout(buf):
            exec(code, safe_globals, {})
        out = buf.getvalue()
        return f"执行成功:\n{out}" if out else "执行成功(无输出)"
    except Exception as e:
        return f"代码错误: {e}"


# ============================================================
# 工具 Schema
# ============================================================

TOOLS = [
    {"type": "function", "function": {
        "name": "calculator",
        "description": "精确计算数学表达式。任何数学运算都用它,不要心算。支持 sqrt 开方。",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式,如 '50 * 7.18'"}
        }, "required": ["expression"]}
    }},
    {"type": "function", "function": {
        "name": "get_current_time",
        "description": "获取当前日期和时间。",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "搜索互联网实时信息。问最新消息、当前事件、未知信息时用。",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "结果数,默认 3"}
        }, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "保存内容到文件。要求保存、记录、导出时用。",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "文件名,如 notes.txt"},
            "content": {"type": "string", "description": "写入内容"}
        }, "required": ["filename", "content"]}
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "读取已保存的文件内容。",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "文件名"}
        }, "required": ["filename"]}
    }},
    {"type": "function", "function": {
        "name": "run_python",
        "description": "执行 Python 代码做复杂计算/数据处理。用 print 输出结果。",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "Python 代码"}
        }, "required": ["code"]}
    }},
]

AVAILABLE_FUNCTIONS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "web_search": web_search,
    "write_file": write_file,
    "read_file": read_file,
    "run_python": run_python,
}

SYSTEM_PROMPT = """你是一个能干的智能助理,可以计算、查时间、上网搜索、读写文件、执行 Python 代码。

原则:
1. 多步任务一步步来,用工具获取信息后再决定下一步。
2. 数学运算必须用 calculator 或 run_python,不要心算。
3. 需要实时信息用 web_search。
4. 充分利用对话历史:如果用户说"那个文件""刚才的结果"等,从历史中理解他们指的是什么。
5. 完成任务后给出清晰简洁的总结。

特别重要 - 关于你的知识边界:
- 你的训练知识有截止日期。对于最新赛事、比分、排名、当前事件、2025年后发生的事,你的记忆很可能过时或错误。
- 遇到这类问题,必须调用 web_search 查证,即使你"觉得"自己知道答案。不要用记忆直接回答时效性问题。
- 判断标准:如果问题涉及"最新""当前""今年""最近""已经"等,或涉及可能变化的事实(赛事结果、人事任命、价格等),一律先搜索再回答。
"""


# ============================================================
# Agent 类(带记忆)
# ============================================================

class Agent:
    def __init__(self, model="qwen2.5:14b", max_steps=8):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = model
        self.max_steps = max_steps
        # 关键: messages 作为成员变量,跨多轮对话累积 = 记忆
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
        """处理一轮用户消息(内部可能多步 ReAct)"""
        if verbose:
            print(f"\n👤 你: {user_message}")
        
        # 把用户消息加入记忆
        self.messages.append({"role": "user", "content": user_message})
        
        # ReAct 循环
        for step in range(1, self.max_steps + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0,
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
                    # 完成,把回答存入记忆并返回
                    self.messages.append({"role": "assistant", "content": msg.content})
                    return msg.content
            
            # 执行工具
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
        
        return "⚠️ 达到最大步数,任务未完成"
    
    def memory_size(self):
        """返回当前记忆里有多少条消息"""
        return len(self.messages)
    
    def reset(self):
        """清空记忆,开始新对话"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# ============================================================
# 测试: 连续对话,验证记忆
# ============================================================

if __name__ == "__main__":
    agent = Agent()
    
    # 第 1 轮: 搜索并保存
    print("=" * 70)
    answer1 = agent.chat("搜索一下什么是向量数据库,总结成两三句话保存到 vectordb.txt")
    print(f"\n🤖 {answer1}")
    print(f"\n[记忆中有 {agent.memory_size()} 条消息]")
    
    # 第 2 轮: 用"那个文件"测试记忆!
    print("\n" + "=" * 70)
    answer2 = agent.chat("把那个文件的内容读出来给我看看")
    print(f"\n🤖 {answer2}")
    print(f"\n[记忆中有 {agent.memory_size()} 条消息]")
    
    # 第 3 轮: 继续基于上下文
    print("\n" + "=" * 70)
    answer3 = agent.chat("根据刚才读到的内容,用一句话告诉我向量数据库最大的用途")
    print(f"\n🤖 {answer3}")
    print(f"\n[记忆中有 {agent.memory_size()} 条消息]")