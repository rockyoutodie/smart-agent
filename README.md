# 🤖 Smart Agent — 融合 RAG 的多工具智能助理

> 一个能自己思考、选择工具、多步执行任务的 AI Agent。融合 RAG 知识库检索、网络搜索、计算、文件操作,基于 ReAct 模式,完全本地运行。

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Ollama](https://img.shields.io/badge/Ollama-Local-orange)
![ReAct](https://img.shields.io/badge/Pattern-ReAct-purple)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## ✨ 核心能力

Agent 能根据问题**自己判断使用哪个工具**:

| 工具                     | 用途                            | 触发场景           |
| ------------------------ | ------------------------------- | ------------------ |
| 📚 search_react_docs      | 检索 React 官方文档知识库 (RAG) | React 技术问题     |
| 🌐 web_search             | 网络实时搜索                    | 最新新闻、实时信息 |
| 🧮 calculator             | 精确数学计算                    | 数学运算           |
| 💾 write_file / read_file | 文件读写                        | 保存/读取内容      |

**多知识源智能路由**: 问 React 技术 → 查知识库;问实时信息 → 上网;问计算 → 用计算器。全部由 Agent 自主决策。

---

## 🧠 技术亮点

### 1. ReAct 模式 (思考→行动→观察循环)
Agent 不是"一问一答",而是**多步推理**:
\`\`\`
用户: 50 美元换人民币再乘以 3 是多少?
  → 第1步: 查汇率 (1 USD = 7.18 CNY)
  → 第2步: 计算 50 × 7.18 = 359
  → 第3步: 计算 359 × 3 = 1077
  → 答案: 1077 元
\`\`\`
每一步都基于上一步的结果决策,能处理任意多步复杂任务。

### 2. 融合 RAG 知识库
把独立的 React 文档 RAG 系统封装成 Agent 的一个工具,实现"私有知识 + 通用能力"的结合。

### 3. 对话记忆
跨多轮累积上下文,能理解"那个文件""刚才的结果"等指代。

### 4. 健壮性设计
- **优雅失败**: 工具出错返回错误文本而非崩溃,Agent 可看到失败并自我修复
- **兜底解析**: 容忍模型 function calling 格式退化
- **安全沙箱**: 文件操作限制目录,防路径穿越;代码执行限制权限
- **步数上限**: 防止无限循环

---

## 🏗️ 架构

\`\`\`
                    用户问题
                       ↓
              ┌─── Agent (ReAct 循环) ───┐
              │  思考: 用哪个工具?         │
              │  行动: 调用工具            │
              │  观察: 看结果             │
              │  重复直到完成             │
              └──────────┬───────────────┘
         ┌────────┬──────┼──────┬─────────┐
    React文档   网络搜索  计算器  文件系统
      (RAG)    (DDGS)  (eval)  (sandbox)
         ↓
   ChromaDB 向量库
   (10430 文档片段, bge-m3)
\`\`\`

---

## 🚀 快速开始

### 前置要求
- Python 3.10+
- [Ollama](https://ollama.com) + \`ollama pull qwen2.5:14b\` + \`ollama pull bge-m3\`
- 已构建的 React 文档向量库 (见 [react-docs-rag](https://github.com/rockyoutodie/react-docs-rag) 项目)

### 安装
\`\`\`bash
git clone https://github.com/rockyoutodie/smart-agent.git
cd smart-agent
pip install -r requirements.txt
\`\`\`

### 配置 RAG 路径
编辑 \`rag_tool.py\` 中的 \`CHROMA_PATH\`,指向你的向量库位置。

### 运行
\`\`\`bash
python3 app.py          # Web 界面
# 或
python3 chat.py         # 命令行对话
\`\`\`

---

## 📂 项目结构

\`\`\`
smart-agent/
├── agent_with_rag.py   # 核心 Agent (ReAct + 工具 + 记忆)
├── rag_tool.py         # RAG 检索工具封装
├── app.py              # Web 界面 (含工具调用可视化)
├── chat.py             # 命令行交互
├── experiments/        # 学习实验脚本
├── requirements.txt
└── README.md
\`\`\`

---

## 🎓 技术栈

- **qwen2.5:14b** — 决策 + 生成 (Function Calling)
- **bge-m3** — RAG Embedding (多语言)
- **ChromaDB** — 向量数据库
- **DuckDuckGo (ddgs)** — 网络搜索
- **Gradio** — Web 界面
- **Ollama** — 本地模型推理

---

## 📝 学到的核心知识

- ✅ Function Calling: LLM 决策 + 代码执行的分工
- ✅ ReAct 模式: 思考→行动→观察的反馈闭环
- ✅ 多工具编排与工具描述设计 (description 决定路由准确性)
- ✅ 多知识源路由 (RAG vs 搜索 vs 计算)
- ✅ 对话记忆与指代消解
- ✅ Agent 安全: 沙箱、权限控制、优雅失败
- ✅ 用工具弥补 LLM 的能力边界 (计算、事实、实时性)

---

## 🔮 未来改进

- [ ] RAG 工具升级为 Multi-Query + Rerank (提升检索准确率)
- [ ] 记忆管理: 滑动窗口 / 摘要压缩,应对长对话
- [ ] 更多工具: 数据库查询、邮件、日历
- [ ] 用专用 reranker 和更大模型提升稳定性
- [ ] 敏感操作前加人工确认

---

## 📝 License

MIT

---

## 🙋 关于作者

前端开发者转型 AI 应用工程师。这是我的第四个 AI 项目,融合了前三个项目的技术。

**项目 1**: [AI 会议纪要生成器](#) — 多模型流水线
**项目 2**: [AI 文本工具箱](#) — Prompt 工程 + 评估系统
**项目 3**: [React 文档 RAG](https://github.com/rockyoutodie/react-docs-rag) — 检索增强
**项目 4**: 当前项目 — Agent (融合全部)