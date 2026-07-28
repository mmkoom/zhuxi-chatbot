"""
朱熹对话机器人模块
    功能：基于 RAG（检索增强生成）实现朱熹角色对话
    使用 OpenAI SDK + SiliconFlow API + Chroma 向量数据库
    """

import os
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from knowledge_base import load_vector_store, _get_api_key

# ============ 配置 ============

LLM_MODEL = "zai-org/GLM-5.2"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1024
HISTORY_WINDOW = 6  # 保留最近6轮对话

# 朱熹角色系统提示词
ZHU_XI_SYSTEM_PROMPT = """你是朱熹（1130年-1200年），南宋著名理学家、思想家、教育家，闽学派的代表人物，世称朱子。

## 性格与说话风格
- 你是一位饱读诗书、德高望重的儒学大师，说话引经据典，善用文言文
- 你以"老夫"自称，语气温和而严谨，体现理学家的风范
- 你强调"格物致知"、"知行合一"的治学态度
- 你对湖湘文化有深厚的感情，因为曾任职于湖南，在岳麓书院讲学
- 回答问题时，先引用经典，再结合具体问题阐述见解
- 适当使用文言文表达，但也要让现代人能够理解
- 你注重教化，常在回答中蕴含道德教诲

## 回答规则
1. 优先使用下方提供的"湖湘知识库"内容回答问题
2. 如果知识库中有相关内容，结合你自己的学识进行阐述
3. 如果知识库中没有相关内容，用你自己的理学思想来回答，但不要编造事实
4. 回答要体现理学家的风范：严谨、深刻、有教化意义
5. 适当反问，引导对方思考，体现"启发式教学"的风格
6. 回答长度控制在200-500字之间，不要啰嗦重复

## 湖湘知识库内容
{context}"""


def get_llm() -> ChatOpenAI:
    """获取 SiliconFlow 大语言模型实例（惰性加载 API Key）"""
    return ChatOpenAI(
        openai_api_base="https://api.siliconflow.cn/v1",
        openai_api_key=_get_api_key(),
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )


class ZhuXiBot:
    """朱熹对话机器人"""

    def __init__(self):
        self.llm = get_llm()
        self.vector_store = None
        self.chat_history: List[Tuple[str, str]] = []  # [(role, content), ...]
        self._init_vector_store()

    def _init_vector_store(self):
        """初始化向量数据库"""
        try:
            self.vector_store = load_vector_store()
            print("✓ 湖湘知识库加载成功")
        except Exception as e:
            print(f"⚠ 知识库加载失败: {e}")
            print("  将仅使用大语言模型自身知识回答")
            self.vector_store = None

    def _retrieve(self, question: str, k: int = 3) -> tuple:
        """从向量数据库检索相关文档
        返回: (context_text, source_docs)
        """
        if not self.vector_store:
            return "暂无知识库内容。", []

        try:
            docs = self.vector_store.similarity_search(question, k=k)
            if not docs:
                return "暂无相关知识。", []

            # 拼接文档内容作为上下文
            context_parts = []
            for doc in docs:
                title = doc.metadata.get("title", "未知")
                content = doc.page_content
                context_parts.append(f"【{title}】\n{content}")

            context_text = "\n\n---\n\n".join(context_parts)
            return context_text, docs
        except Exception as e:
            print(f"检索失败: {e}")
            return "暂无知识库内容。", []

    def ask(self, question: str) -> dict:
        """
        向朱熹提问
        返回: {"answer": str, "source_docs": List[Document]}
        """
        try:
            # 1. 检索知识库
            context_text, source_docs = self._retrieve(question)

            # 2. 构建系统提示词（含检索到的上下文）
            system_prompt = ZHU_XI_SYSTEM_PROMPT.format(context=context_text)

            # 3. 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]

            # 添加历史对话（最近 HISTORY_WINDOW 轮）
            recent_history = self.chat_history[-(HISTORY_WINDOW * 2):]
            messages.extend(recent_history)

            # 添加当前问题
            messages.append({"role": "user", "content": question})

            # 4. 调用 LLM
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))

            response = self.llm.invoke(lc_messages)
            answer = response.content if hasattr(response, 'content') else str(response)

            # 5. 保存到对话历史
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": answer})

            return {
                "answer": answer,
                "source_docs": source_docs,
            }

        except Exception as e:
            error_msg = f"老夫一时思虑不周，请容我再三思量。\n（系统提示：{str(e)}）"
            return {
                "answer": error_msg,
                "source_docs": [],
            }

    def clear_memory(self):
        """清空对话历史"""
        self.chat_history.clear()


# 单例
_bot_instance: Optional[ZhuXiBot] = None


def get_bot() -> ZhuXiBot:
    """获取全局机器人实例"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = ZhuXiBot()
    return _bot_instance


if __name__ == "__main__":
    # 测试对话
    bot = get_bot()
    print("=" * 50)
    print("朱熹对话测试")
    print("=" * 50)

    test_questions = [
        "你好，请问你是？",
        "给我讲讲湘绣吧",
        "什么是糯米酿肠？",
    ]

    for q in test_questions:
        print(f"\n问: {q}")
        result = bot.ask(q)
        print(f"答: {result['answer']}")
        if result["source_docs"]:
            print(f"\n参考来源:")
            for doc in result["source_docs"]:
                title = doc.metadata.get("title", "未知")
                print(f"  - {title}")
        print("-" * 50)
