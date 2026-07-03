"""
Day 2 补充: 健壮的 Agent - 容忍模型把 tool_call 写进 content
"""

import json
import re
import math
from datetime import datetime
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ===== 工具(和 03 一样) =====
def calculator(expression: str) -> str:
    try:
        allowed = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi, "e": math.e}
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"计算错误: {e}"

def get_current_time(timezone: str = "本地") -> str:
    return f"当前时间是 {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"

def get_weather(city: str) -> str:
    data = {"北京": "晴, 8°C", "上海": "多云, 15°C", "广州": "小雨, 22°C"}
    return data.get(city, f"没有 {city} 的天气数据")

def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    rates = {("USD","CNY"): 7.18, ("EUR","CNY"): 7.85, ("CNY","USD"): 0.139}
    rate = rates.get((from_currency.upper(), to_currency.upper()))
    return f"1 {from_currency.upper()} = {rate} {to_currency.upper()}" if rate else "无此汇率"

available_functions = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "get_exchange_rate": get_exchange_rate,
}

# tools 定义和 03 完全一样,这里省略,实际要复制过来
from importlib import import_module
import sys
sys.path.insert(0, ".")
tools = import_module("03_multi_tools").tools


# ============================================================
# 关键: 兜底解析器
# ============================================================

def extract_tool_call_from_text(text: str):
    """
    当模型把 tool_call 错误地写进 content 时,从文本里把它捞出来
    """
    if not text:
        return None
    
    # 找 {"name": ..., "arguments": ...} 这样的 JSON
    pattern = r'\{"name":\s*"(\w+)",\s*"arguments":\s*(\{[^}]*\})\}'
    match = re.search(pattern, text)
    
    if match:
        function_name = match.group(1)
        try:
            function_args = json.loads(match.group(2))
            return {"name": function_name, "arguments": function_args}
        except:
            return None
    return None


# ============================================================
# 健壮的 Agent
# ============================================================

def run_agent(user_message: str):
    print(f"\n{'='*60}")
    print(f"👤 用户: {user_message}")
    print(f"{'='*60}")
    
    messages = [{"role": "user", "content": user_message}]
    
    response = client.chat.completions.create(
        model="qwen2.5:14b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    
    response_message = response.choices[0].message
    
    # ===== 路径 1: 正常的 tool_calls =====
    if response_message.tool_calls:
        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"\n🔧 [正常] 工具: {name} 参数: {args}")
            result = available_functions[name](**args)
            print(f"   ⚙️  结果: {result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
        final = client.chat.completions.create(model="qwen2.5:14b", messages=messages)
        print(f"\n💬 最终回答: {final.choices[0].message.content}")
        return
    
    # ===== 路径 2: 兜底 - 从 content 里捞 tool_call =====
    fallback = extract_tool_call_from_text(response_message.content)
    if fallback:
        name = fallback["name"]
        args = fallback["arguments"]
        print(f"\n🔧 [兜底] 从文本中捞出工具: {name} 参数: {args}")
        
        if name in available_functions:
            result = available_functions[name](**args)
            print(f"   ⚙️  结果: {result}")
            # 把结果给 LLM 组织语言
            messages.append({"role": "user", "content": f"工具返回结果: {result}。请用自然语言回答用户的问题: {user_message}"})
            final = client.chat.completions.create(model="qwen2.5:14b", messages=messages)
            print(f"\n💬 最终回答: {final.choices[0].message.content}")
        return
    
    # ===== 路径 3: 真的没用工具 =====
    print(f"\n💬 直接回答: {response_message.content}")


if __name__ == "__main__":
    tests = [
        "现在几点了?",
        "北京今天天气怎么样?",
        "256 的平方根是多少?",
        "你好,你能做什么?",
    ]
    for msg in tests:
        run_agent(msg)