"""
智能助理 Agent - Web 界面
展示 Agent 的工具调用过程 (思考→行动→观察)
"""

import gradio as gr
import json
from agent_with_rag import (
    Agent, TOOLS, AVAILABLE_FUNCTIONS, SYSTEM_PROMPT
)
from openai import OpenAI


# 工具名 → 友好显示名 + emoji
TOOL_DISPLAY = {
    "search_react_docs": "📚 查询 React 文档",
    "web_search": "🌐 网络搜索",
    "calculator": "🧮 计算器",
    "write_file": "💾 保存文件",
    "read_file": "📖 读取文件",
}


class WebAgent(Agent):
    """在 Agent 基础上,把工具调用过程 yield 出来给界面显示"""
    
    def chat_stream(self, user_message: str):
        """处理消息,逐步产出工具调用过程"""
        self.messages.append({"role": "user", "content": user_message})
        
        process_log = ""  # 累积的过程日志
        
        for step in range(1, self.max_steps + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=self.messages,
                    tools=TOOLS, tool_choice="auto", temperature=0,
                )
            except Exception as e:
                yield process_log, f"❌ 出错: {e}"
                return
            
            msg = response.choices[0].message
            calls = []
            
            if msg.tool_calls:
                self.messages.append(msg)
                for tc in msg.tool_calls:
                    calls.append({"id": tc.id, "name": tc.function.name,
                                  "args": json.loads(tc.function.arguments)})
            else:
                fb = self._extract_fallback(msg.content)
                if fb:
                    self.messages.append({"role": "assistant", "content": msg.content})
                    calls.append({"id": f"fb_{step}", "name": fb["name"], "args": fb["arguments"]})
                else:
                    # 完成
                    self.messages.append({"role": "assistant", "content": msg.content})
                    yield process_log, msg.content
                    return
            
            # 执行工具,更新过程日志
            for tc in calls:
                name, args = tc["name"], tc["args"]
                display_name = TOOL_DISPLAY.get(name, name)
                
                # 显示参数(简化)
                arg_str = ", ".join(f"{k}={str(v)[:40]}" for k, v in args.items())
                process_log += f"**{display_name}**\n`{arg_str}`\n\n"
                yield process_log, "🤔 思考中..."  # 实时更新界面
                
                result = AVAILABLE_FUNCTIONS[name](**args) if name in AVAILABLE_FUNCTIONS else f"未知工具"
                
                # 显示结果预览
                result_preview = result[:150] + "..." if len(result) > 150 else result
                process_log += f"↳ {result_preview}\n\n---\n\n"
                yield process_log, "🤔 思考中..."
                
                if tc["id"].startswith("fb"):
                    self.messages.append({"role": "user", "content": f"工具 {name} 结果: {result}。请继续。"})
                else:
                    self.messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
        
        yield process_log, "⚠️ 达到最大步数"


# 全局 Agent 实例(保持记忆)
agent = WebAgent()


def respond(message, history):
    """Gradio 聊天回调"""
    if not message.strip():
        return history, "", ""
    
    final_answer = ""
    process = ""
    
    for process_log, answer in agent.chat_stream(message):
        process = process_log
        final_answer = answer
    
    # 字典格式(Gradio 6.0)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": final_answer}
    ]
    return history, "", process


def reset_agent():
    agent.reset()
    return [], "", "记忆已清空 🔄"


# ============================================================
# 界面
# ============================================================

with gr.Blocks(title="智能助理 Agent") as demo:
    gr.Markdown("""
    # 🤖 智能助理 Agent
    
    > 融合 RAG + 多工具 + ReAct 的智能助理 · 完全本地运行
    
    我能自己判断用哪个能力: **📚 React 文档知识库** · **🌐 网络搜索** · **🧮 计算** · **💾 文件读写**
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="对话", height=450)
            with gr.Row():
                msg = gr.Textbox(
                    label="", placeholder="问我任何问题...(试试'useState怎么用'或'算下123*456')",
                    scale=5
                )
                send = gr.Button("发送", variant="primary", scale=1)
            reset = gr.Button("🔄 清空记忆", size="sm")
        
        with gr.Column(scale=2):
            gr.Markdown("### 🔬 Agent 工作过程")
            process_display = gr.Markdown("等待任务...")
    
    gr.Markdown("""
    ### 💡 试试这些
    - `useState 和 useEffect 有什么区别?` → 会查 React 文档
    - `2024 年有什么 AI 大新闻?` → 会上网搜索
    - `帮我算 1234 乘以 5678` → 会用计算器
    - `React 性能优化的方法,保存到 perf.txt` → 多步:查文档+存文件
    """)
    
    send.click(respond, [msg, chatbot], [chatbot, msg, process_display])
    msg.submit(respond, [msg, chatbot], [chatbot, msg, process_display])
    reset.click(reset_agent, outputs=[chatbot, msg, process_display])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7863, inbrowser=True)