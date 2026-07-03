"""
交互式 Agent 命令行助理
"""

from agent import Agent


def main():
    print("=" * 60)
    print("🤖 智能助理已启动")
    print("   我能: 计算、查时间、上网搜索、读写文件、执行代码")
    print("   命令: 输入 'quit' 退出, 'reset' 清空记忆")
    print("=" * 60)
    
    agent = Agent()
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("再见!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("🔄 记忆已清空")
            continue
        
        # 处理(verbose=True 显示工具调用过程)
        answer = agent.chat(user_input, verbose=True)
        print(f"\n🤖 {answer}")


if __name__ == "__main__":
    main()