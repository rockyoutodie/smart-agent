"""
Day 1 实验 1: 第一个 Function Calling
任务: 让 LLM 调用一个计算器函数
"""

import json
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ============================================================
# 1. 定义真正的函数(工具)
# ============================================================

def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        # 注意: eval 有安全风险,生产环境要用安全的解析器
        # 这里仅用于学习
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


# ============================================================
# 2. 用 JSON Schema 描述这个工具(给 LLM 看)
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式的结果。当用户需要进行数学运算(加减乘除、幂运算等)时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式,使用 Python 语法。例如 '3847 * 2913' 或 '2 ** 10'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


# ============================================================
# 3. 函数名 → 真实函数 的映射
# ============================================================

available_functions = {
    "calculator": calculator,
}


# ============================================================
# 4. 跑一个完整的 Function Calling 流程
# ============================================================

def run(user_message: str):
    print(f"\n{'='*60}")
    print(f"👤 用户: {user_message}")
    print(f"{'='*60}")
    
    messages = [
        {"role": "user", "content": user_message}
    ]
    
    # 第一次调用 LLM: 让它决定要不要用工具
    response = client.chat.completions.create(
        model="qwen2.5:14b",
        messages=messages,
        tools=tools,        # 告诉 LLM 有哪些工具
        tool_choice="auto", # 让 LLM 自己决定用不用
    )
    
    response_message = response.choices[0].message
    
    # 检查 LLM 是否想调用工具
    if response_message.tool_calls:
        print(f"\n🤖 LLM 决定调用工具:")
        
        # 把 LLM 的决定加入对话历史
        messages.append(response_message)
        
        # 执行每个工具调用
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"   工具: {function_name}")
            print(f"   参数: {function_args}")
            
            # 调用真实函数
            function_to_call = available_functions[function_name]
            function_result = function_to_call(**function_args)
            
            print(f"   ⚙️  执行结果: {function_result}")
            
            # 把工具执行结果加入对话历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_result,
            })
        
        # 第二次调用 LLM: 让它基于工具结果给最终回答
        final_response = client.chat.completions.create(
            model="qwen2.5:14b",
            messages=messages,
        )
        
        answer = final_response.choices[0].message.content
        print(f"\n💬 最终回答: {answer}")
    
    else:
        # LLM 没用工具,直接回答
        print(f"\n💬 LLM 直接回答(没用工具): {response_message.content}")


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    # 需要计算的问题 → 应该调用工具
    run("3847 乘以 2913 等于多少?")
    
    # 不需要计算的问题 → 不应该调用工具
    run("你好,你是谁?")
    
    # 复杂计算 → 应该调用工具
    run("2 的 20 次方是多少?")