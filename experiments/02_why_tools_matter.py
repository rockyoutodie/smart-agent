"""
Day 1 实验 2: 为什么需要工具?
对比: LLM 自己算 vs 用计算器工具
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# 几个容易算错的大数运算
test_cases = [
    ("3847 * 2913", 3847 * 2913),
    ("98765 * 43210", 98765 * 43210),
    ("123456789 + 987654321", 123456789 + 987654321),
    ("2 ** 30", 2 ** 30),
]

print("=" * 70)
print("测试: LLM 自己算数,准确率如何?")
print("=" * 70)

correct = 0
for expression, true_answer in test_cases:
    # 让 LLM 直接算(不给工具)
    response = client.chat.completions.create(
        model="qwen2.5:14b",
        messages=[
            {"role": "user", "content": f"计算 {expression} 等于多少? 只回答数字,不要其他内容。"}
        ],
        temperature=0,
    )
    
    llm_answer = response.choices[0].message.content.strip()
    
    # 检查对不对
    is_correct = str(true_answer) in llm_answer.replace(",", "")
    if is_correct:
        correct += 1
    
    status = "✅" if is_correct else "❌"
    print(f"\n{status} {expression}")
    print(f"   正确答案: {true_answer}")
    print(f"   LLM 答案: {llm_answer}")

print(f"\n{'='*70}")
print(f"LLM 自己算的准确率: {correct}/{len(test_cases)} = {correct/len(test_cases)*100:.0f}%")
print(f"{'='*70}")
print("\n💡 结论: 大数运算 LLM 经常算错,这就是为什么需要计算器工具!")
print("   工具的准确率是 100%,因为是真的在算。")