"""
把第 3 周的 RAG 检索封装成 Agent 工具
"""

import chromadb
from chromadb import EmbeddingFunction, Embeddings
from openai import OpenAI

# 第 3 周向量库的路径(根据你的实际路径调整)
CHROMA_PATH = "/Users/houjiameng/ai-learning/week3-rag/chroma_db"
COLLECTION_NAME = "react_docs"


class OllamaBgeM3Embedding(EmbeddingFunction):
    """和第 3 周入库时用的 Embedding 完全一致(必须一致!)"""
    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = "bge-m3"
    
    def __call__(self, input: list[str]) -> Embeddings:
        embeddings = []
        for text in input:
            resp = self.client.embeddings.create(model=self.model, input=text)
            embeddings.append(resp.data[0].embedding)
        return embeddings


# 全局加载一次(不要每次调用都重连)
_collection = None

def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=OllamaBgeM3Embedding()
        )
    return _collection


def search_react_docs(query: str, top_k: int = 3) -> str:
    """
    从 React 官方文档知识库检索相关内容
    这就是要给 Agent 用的工具函数
    """
    try:
        collection = _get_collection()
        results = collection.query(query_texts=[query], n_results=top_k)
        
        if not results["documents"][0]:
            return "在 React 文档中没有找到相关内容"
        
        # 组装成 LLM 易读的格式
        output = []
        for i, (doc, meta) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0]
        ), 1):
            source = meta.get("source", "未知")
            # 标题路径
            path_parts = [meta.get(k, "") for k in ["h1", "h2", "h3"] if meta.get(k)]
            path = " > ".join(path_parts) if path_parts else ""
            
            output.append(f"[文档{i}] 来源: {source}" + (f" | {path}" if path else "") + f"\n{doc}")
        
        return "\n\n".join(output)
    
    except Exception as e:
        return f"检索 React 文档失败: {e}"


# ============================================================
# 先单独测试这个工具能不能用
# ============================================================

if __name__ == "__main__":
    print("测试 RAG 工具...")
    print("=" * 60)
    result = search_react_docs("what is useState", top_k=2)
    print(result)