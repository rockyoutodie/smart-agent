"""
Day 4: 真实工具 + ReAct Agent
"""

import json
import re
import sys
sys.path.insert(0, ".")
from importlib import import_module
from openai import OpenAI

# 复用真实工具
real_tools = import_module("09_real_tools")
tools = real_tools.tools
available_functions = real_tools.available_functions

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def extract_tool_call_from_text(text: str):
    if not text:
        return None
    # 支持更复杂的参数(含嵌套)
    pattern = r'\{"name":\s*"(\w+)",\s*"arguments":\s*(\{.*\})\}'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return {"name": match.group(1), "arguments": json.loads(match.group(2))}
        except:
            return None
    return None


SYSTEM_PROMPT = """你是一个能干的智能助理,可以上网搜索、读写文件、执行 Python 代码。

原则:
1. 多步任务一步步来,用工具获取信息后再决定下一步。
2. 需要实时信息时用 web_search。
3. 复杂计算用 run_python。
4. 要保存内容时用 write_file。
5. 完成任务后给出清晰的总结。"""


def real_agent(user_message: str, max_steps: int = 8):
    print(f"\n{'='*70}")
    print(f"👤 用户: {user_message}")
    print(f"{'='*70}")
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    for step in range(1, max_steps + 1):
        print(f"\n--- 🔄 第 {step} 步 ---")
        
        try:
            response = client.chat.completions.create(
                model="qwen2.5:14b",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0,
            )
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            return
        
        msg = response.choices[0].message
        tool_calls_to_run = []
        
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                tool_calls_to_run.append({
                    "id": tc.id, "name": tc.function.name,
                    "args": json.loads(tc.function.arguments)
                })
        else:
            fallback = extract_tool_call_from_text(msg.content)
            if fallback:
                messages.append({"role": "assistant", "content": msg.content})
                tool_calls_to_run.append({
                    "id": "fb_" + str(step), "name": fallback["name"],
                    "args": fallback["arguments"]
                })
            else:
                print(f"\n{'='*70}")
                print(f"✅ 最终答案: {msg.content}")
                print(f"{'='*70}")
                return msg.content
        
        for tc in tool_calls_to_run:
            name, args = tc["name"], tc["args"]
            # 长参数截断显示
            args_display = {k: (v[:60] + "..." if isinstance(v, str) and len(v) > 60 else v) for k, v in args.items()}
            print(f"🔧 行动: {name}({args_display})")
            
            if name in available_functions:
                result = available_functions[name](**args)
            else:
                result = f"未知工具: {name}"
            
            # 截断显示结果
            result_display = result[:200] + "..." if len(result) > 200 else result
            print(f"👁️  观察: {result_display}")
            
            if tc["id"].startswith("fb"):
                messages.append({"role": "user", "content": f"工具 {name} 结果: {result}。请继续。"})
            else:
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
    
    print(f"\n⚠️ 达到最大步数")


if __name__ == "__main__":
    tasks = [
        # 任务 1: 搜索 + 保存
        "搜索一下什么是 RAG 技术,然后把结果总结成 3 句话保存到 rag_summary.txt 文件里",
        
        # 任务 2: 复杂计算
        "用 Python 算出斐波那契数列的前 15 项",
        
        # 任务 3: 读文件 + 处理
        "读取 rag_summary.txt 的内容,告诉我里面讲了什么",
    ]
    
    for task in tasks:
        real_agent(task)
        input("\n按 Enter 继续下一个任务...")