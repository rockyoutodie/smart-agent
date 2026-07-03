"""
Day 3: ReAct Agent - 思考→行动→观察 循环
"""

import json
import re
import math
from datetime import datetime
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ============================================================
# 工具箱
# ============================================================

def calculator(expression: str) -> str:
    try:
        allowed = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi, "e": math.e}
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"计算错误: {e}"

def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    rates = {("USD","CNY"): 7.18, ("EUR","CNY"): 7.85, ("CNY","USD"): 0.139, ("JPY","CNY"): 0.048}
    rate = rates.get((from_currency.upper(), to_currency.upper()))
    return f"1 {from_currency.upper()} = {rate} {to_currency.upper()}" if rate else "无此汇率数据"

def get_weather(city: str) -> str:
    data = {"北京": "晴, 8°C", "上海": "多云, 15°C", "广州": "小雨, 22°C"}
    return data.get(city, f"没有 {city} 的天气数据")


available_functions = {
    "calculator": calculator,
    "get_exchange_rate": get_exchange_rate,
    "get_weather": get_weather,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式。需要精确数学运算时必须使用此工具,不要自己心算。支持 sqrt 开方。",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式,如 '50 * 7.18'"}},
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "查询两种货币之间的汇率。",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {"type": "string", "description": "源货币代码,如 USD"},
                    "to_currency": {"type": "string", "description": "目标货币代码,如 CNY"}
                },
                "required": ["from_currency", "to_currency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询城市天气。",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"]
            }
        }
    }
]


# ============================================================
# 兜底解析器(应对昨天的模型退化问题)
# ============================================================

def extract_tool_call_from_text(text: str):
    if not text:
        return None
    pattern = r'\{"name":\s*"(\w+)",\s*"arguments":\s*(\{[^}]*\})\}'
    match = re.search(pattern, text)
    if match:
        try:
            return {"name": match.group(1), "arguments": json.loads(match.group(2))}
        except:
            return None
    return None


# ============================================================
# ReAct 主循环
# ============================================================

REACT_SYSTEM_PROMPT = """你是一个善于解决问题的助手。你可以使用工具来完成任务。

重要原则:
1. 遇到多步任务时,一步一步来。先用工具获取信息,看到结果后再决定下一步。
2. 任何数学运算都必须用 calculator 工具,绝对不要自己心算。
3. 如果需要用上一步的结果做下一步计算,把上一步的实际数值代入。
4. 当你收集到足够信息、完成所有计算后,才给出最终答案。"""


def react_agent(user_message: str, max_steps: int = 8):
    print(f"\n{'='*70}")
    print(f"👤 用户: {user_message}")
    print(f"{'='*70}")
    
    messages = [
        {"role": "system", "content": REACT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    # ReAct 循环
    for step in range(1, max_steps + 1):
        print(f"\n--- 🔄 第 {step} 步 ---")
        
        response = client.chat.completions.create(
            model="qwen2.5:14b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0,
        )
        
        msg = response.choices[0].message
        
        # 收集本步要执行的工具调用(正常 + 兜底)
        tool_calls_to_run = []
        
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                tool_calls_to_run.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments)
                })
        else:
            # 兜底: 看 content 里有没有工具调用
            fallback = extract_tool_call_from_text(msg.content)
            if fallback:
                # 手动构造一个 assistant 消息
                messages.append({"role": "assistant", "content": msg.content})
                tool_calls_to_run.append({
                    "id": "fallback_" + str(step),
                    "name": fallback["name"],
                    "args": fallback["arguments"]
                })
            else:
                # 没有工具调用 = LLM 认为任务完成,给最终答案
                print(f"💡 思考: 任务完成")
                print(f"\n{'='*70}")
                print(f"✅ 最终答案: {msg.content}")
                print(f"{'='*70}")
                return msg.content
        
        # 执行所有工具调用
        for tc in tool_calls_to_run:
            name, args = tc["name"], tc["args"]
            print(f"🔧 行动: 调用 {name}({args})")
            
            if name in available_functions:
                result = available_functions[name](**args)
            else:
                result = f"错误: 未知工具 {name}"
            
            print(f"👁️  观察: {result}")
            
            # 把结果喂回去
            if tc["id"].startswith("fallback"):
                messages.append({"role": "user", "content": f"工具 {name} 的执行结果是: {result}。请根据这个结果继续。"})
            else:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
    
    print(f"\n⚠️ 达到最大步数 {max_steps},强制停止")
    return "任务未能在限定步数内完成"


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    tests = [
        "我有 50 美元,换成人民币后,再乘以 3 是多少?",   # 多步: 汇率→算→算
        "100 美元和 100 欧元换成人民币,哪个更多?多多少?",  # 多步: 两次汇率→比较→算差
    ]
    
    for msg in tests:
        react_agent(msg)
        input("\n按 Enter 继续下一个任务...")