"""
Day 2 实验 1: 多工具 Agent
任务: 给 LLM 装多个工具,看它自己选
"""

import json
import math
from datetime import datetime
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ============================================================
# 工具箱: 4 个真实函数
# ============================================================

def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        # 允许使用 math 模块的函数
        allowed = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi, "e": math.e}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def get_current_time(timezone: str = "本地") -> str:
    """获取当前时间"""
    now = datetime.now()
    return f"当前时间是 {now.strftime('%Y年%m月%d日 %H:%M:%S')} ({timezone})"


def get_weather(city: str) -> str:
    """查询天气(模拟数据,真实场景会调用天气 API)"""
    # 模拟数据 - 真实项目这里会调用真实 API
    fake_weather = {
        "北京": "晴, 8°C, 微风",
        "上海": "多云, 15°C, 东风 3 级",
        "广州": "小雨, 22°C, 湿度 80%",
        "深圳": "晴, 24°C, 微风",
    }
    return fake_weather.get(city, f"抱歉,没有 {city} 的天气数据")


def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """查询汇率(模拟数据)"""
    # 模拟汇率
    rates = {
        ("USD", "CNY"): 7.18,
        ("EUR", "CNY"): 7.85,
        ("CNY", "USD"): 0.139,
        ("JPY", "CNY"): 0.048,
    }
    rate = rates.get((from_currency.upper(), to_currency.upper()))
    if rate:
        return f"1 {from_currency.upper()} = {rate} {to_currency.upper()}"
    return f"抱歉,没有 {from_currency} 到 {to_currency} 的汇率数据"


# ============================================================
# 工具描述(给 LLM 看的"说明书")
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式的结果。当用户需要进行数学运算时使用,支持加减乘除、幂运算、开方(sqrt)等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式,Python 语法。例如 '100 * 5' 或 'sqrt(144)'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间。当用户询问现在几点、今天几号、当前时间等时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区,默认为本地时区"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气情况。当用户询问某地天气、温度、是否下雨等时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称,例如'北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "查询货币汇率。当用户询问货币兑换、汇率换算时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "源货币代码,例如 'USD'、'CNY'、'EUR'"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "目标货币代码,例如 'CNY'、'USD'"
                    }
                },
                "required": ["from_currency", "to_currency"]
            }
        }
    }
]


# ============================================================
# 函数映射表
# ============================================================

available_functions = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "get_exchange_rate": get_exchange_rate,
}


# ============================================================
# Agent 主循环
# ============================================================

def run_agent(user_message: str):
    print(f"\n{'='*60}")
    print(f"👤 用户: {user_message}")
    print(f"{'='*60}")
    
    messages = [{"role": "user", "content": user_message}]
    
    # 第一次调用: LLM 决定用哪个工具
    response = client.chat.completions.create(
        model="qwen2.5:14b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    
    response_message = response.choices[0].message
    
    if response_message.tool_calls:
        messages.append(response_message)
        
        # 可能调用多个工具
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"\n🔧 LLM 选择工具: {function_name}")
            print(f"   参数: {function_args}")
            
            # 执行
            function_to_call = available_functions[function_name]
            function_result = function_to_call(**function_args)
            
            print(f"   ⚙️  结果: {function_result}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_result,
            })
        
        # 第二次调用: 组织最终回答
        final_response = client.chat.completions.create(
            model="qwen2.5:14b",
            messages=messages,
        )
        print(f"\n💬 最终回答: {final_response.choices[0].message.content}")
    
    else:
        print(f"\n💬 直接回答(没用工具): {response_message.content}")


# ============================================================
# 测试: 看 LLM 怎么选工具
# ============================================================

if __name__ == "__main__":
    test_messages = [
        "现在几点了?",                      # → get_current_time
        "北京今天天气怎么样?",               # → get_weather
        "100 美元等于多少人民币?",           # → get_exchange_rate
        "256 的平方根是多少?",               # → calculator
        "你好,你能做什么?",                 # → 不用工具,直接回答
    ]
    
    for msg in test_messages:
        run_agent(msg)