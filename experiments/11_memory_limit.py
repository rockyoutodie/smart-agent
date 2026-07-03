"""
Day 5: 观察对话记忆的累积
"""

import sys
sys.path.insert(0, "..")
from agent import Agent


agent = Agent()

# 连续问很多轮,观察 messages 怎么涨
questions = [
    "算一下 2 的 10 次方",
    "再算 3 的 5 次方",
    "100 的平方根呢",
    "现在几点",
    "把这些计算结果总结一下",
]

for i, q in enumerate(questions, 1):
    agent.chat(q, verbose=False)
    print(f"第 {i} 轮后, 记忆消息数: {agent.memory_size()}")

print(f"\n💡 观察: 记忆一直在涨。如果聊几百轮,会发生什么?")
print("   答案: messages 会超过模型的 context window,导致:")
print("   - 报错(超出长度)")
print("   - 或早期消息被截断(Agent'忘记'开头的事)")