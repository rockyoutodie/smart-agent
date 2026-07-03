"""
Day 3: 观察 ReAct 的完整推理轨迹
"""

import sys
sys.path.insert(0, ".")
from importlib import import_module
react_agent = import_module("07_react_agent").react_agent


if __name__ == "__main__":
    # 一个需要多步推理的复杂任务
    task = "如果北京现在的温度数字,加上 100 美元换算成人民币的整数部分,再开平方根,结果是多少?"
    
    react_agent(task, max_steps=10)