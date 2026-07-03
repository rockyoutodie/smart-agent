"""
Day 2 实验 2: 一个任务,多个工具
任务: 测试需要连续/组合调用工具的复杂问题
"""

# 复用上一个文件的工具(实际项目会拆成模块,这里为了简单直接导入)
from importlib import import_module
import sys
sys.path.insert(0, ".")
mod = import_module("03_multi_tools")

run_agent = mod.run_agent


if __name__ == "__main__":
    complex_messages = [
        # 需要两个工具: 汇率 + 计算
        "我有 50 美元,换成人民币后,再乘以 3 是多少?",
        
        # 需要两个工具: 天气 + 时间
        "现在几点了?顺便告诉我上海天气",
        
        # 一个工具但要算多步
        "100 的平方根,再加上 50 的平方根等于多少?",
    ]
    
    for msg in complex_messages:
        run_agent(msg)