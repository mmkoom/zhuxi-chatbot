"""
湖湘知识库构建模块
功能：爬取湖湘文化内容、生成嵌入向量、存入 Chroma 向量数据库
"""

import os
import re
import json
import hashlib
from typing import List, Dict
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ============ 配置 ============

def _get_api_key() -> str:
    """从环境变量或 Streamlit Secrets 获取 API Key"""
    # 1. 优先从环境变量读取
    key = os.environ.get("SILICONFLOW_API_KEY")
    if key:
        return key
    # 2. 尝试从 Streamlit secrets 读取（部署到 Streamlit Cloud 时使用）
    try:
        import streamlit as st
        key = st.secrets.get("SILICONFLOW_API_KEY")
        if key:
            return key
    except Exception:
        pass
    # 3. 兜底提示
    raise ValueError(
        "未找到 SiliconFlow API Key。请设置环境变量 SILICONFLOW_API_KEY "
        "或在 .streamlit/secrets.toml 中配置。"
    )

SILICONFLOW_API_KEY = _get_api_key()
EMBEDDING_MODEL = "BAAI/bge-m3"
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "data", "documents")

# 湖湘文化知识来源 URL 列表
HUXIANG_URLS = [
    # 尝·味道
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685364.html", "地方名小吃：糯米酿肠"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685450.html", "地方名小吃：猪血团子"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685449.html", "地方名小吃：常德酱板鸭"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685448.html", "地方名小吃：皱纱馄饨"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685447.html", "地方名小吃：湘黄鸡"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685446.html", "地方名小吃：口味虾"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685445.html", "地方名小吃：萝卜丝饼"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685444.html", "地方名小吃：姊妹团子"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685443.html", "地方名小吃：刮凉粉"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cwd/201711/t20171111_4685442.html", "地方名小吃：冠顶饺"),
    # 品·文学
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/pwx/201711/t20171111_4685240.html", "湖南文学概览"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/pwx/201711/t20171111_4685239.html", "古代文学"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/pwx/201711/t20171111_4685238.html", "近代文学"),
    # 听·戏曲
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/txq/201711/t20171111_4685252.html", "湘剧"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/txq/201711/t20171111_4685251.html", "湘昆"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/txq/201711/t20171111_4685250.html", "花鼓戏"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/txq/201711/t20171111_4685249.html", "衡阳湘剧"),
    # 赏·工艺
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685293.html", "湘绣"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685292.html", "陶瓷艺术"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685291.html", "浏阳菊花石雕"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685290.html", "邵阳翻簧竹刻"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685289.html", "隆回滩头年画"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685288.html", "岳州扇制作技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685287.html", "溪砚制作工艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685286.html", "宝庆竹刻"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/sgy/201711/t20171111_4685285.html", "凤凰扎染技艺"),
    # 承·历史
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140822_4875000.html", "湘西土陶制作技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140822_4874999.html", "湘西竹编制作技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140822_4874997.html", "蔡伦古法造纸技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140822_4875001.html", "麻香糕传统手工技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140821_4874998.html", "古丈毛尖茶手工制作技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140820_4874994.html", "武冈卤菜制作技艺"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/cls/201408/t20140819_4874995.html", "雕花蜜饯制作技艺"),
    # 观·民俗
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/gms/201711/t20171111_4685362.html", "安仁赶分社"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/gms/201711/t20171111_4685361.html", "划旱舟"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/gms/201711/t20171111_4685360.html", "衡阳出天行"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/gms/201711/t20171111_4685359.html", "通道芦笙节"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/gms/201711/t20171111_4685358.html", "怀化侗年"),
    # 讲方言
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/jfy/201711/t20171111_4685284.html", "凤凰古城方言"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/jfy/201711/t20171111_4685283.html", "湘南土话"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/jfy/201711/t20171111_4685282.html", "湖南方言——湘剧"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/jfy/201305/t20130521_4685281.html", "湖南方言——地方戏曲花鼓戏"),
    ("https://www.hunan.gov.cn/hnszf/jxxx/hxwh/jfy/201711/t20171111_4685280.html", "湖南方言——地方戏曲祁剧"),
]


def get_embeddings() -> OpenAIEmbeddings:
    """获取 SiliconFlow 嵌入模型实例"""
    return OpenAIEmbeddings(
        openai_api_base="https://api.siliconflow.cn/v1",
        openai_api_key=SILICONFLOW_API_KEY,
        model=EMBEDDING_MODEL,
    )


def scrape_page(url: str, title: str) -> str:
    """爬取单个页面，提取正文内容"""
    # 先检查本地是否已有缓存文件
    cache_path = os.path.join(DOCUMENTS_DIR, f"{_sanitize_filename(title)}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # 禁用 SSL 验证（hunan.gov.cn 证书问题）
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 移除 script 和 style 标签
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # 提取正文
        text = soup.get_text(separator="\n", strip=True)

        # 清理多余空行
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        # 过滤掉太短的导航行
        lines = [line for line in lines if len(line) > 2]

        # 构建内容：标题 + 正文
        content = f"标题：{title}\n\n"
        content += "\n".join(lines)
        content += f"\n\n来源：{url}"

        return content
    except Exception as e:
        print(f"  爬取失败 [{title}]: {e}")
        return ""


def scrape_all_pages() -> List[Dict]:
    """爬取所有湖湘文化页面"""
    documents = []
    for i, (url, title) in enumerate(HUXIANG_URLS):
        print(f"[{i+1}/{len(HUXIANG_URLS)}] 正在爬取: {title}...")
        content = scrape_page(url, title)
        if content:
            doc = {
                "title": title,
                "url": url,
                "content": content,
            }
            documents.append(doc)
            # 保存为本地文件
            save_path = os.path.join(DOCUMENTS_DIR, f"{_sanitize_filename(title)}.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ 已保存: {title}")
        else:
            print(f"  ✗ 跳过: {title}")
    return documents


def _sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def build_vector_store(force_rebuild: bool = False) -> Chroma:
    """
    构建或加载 Chroma 向量数据库
    - force_rebuild=True: 重新爬取并构建
    - force_rebuild=False: 如果已存在则直接加载
    """
    if os.path.exists(CHROMA_PERSIST_DIR) and not force_rebuild:
        print("检测到已有 Chroma 数据库，正在加载...")
        embeddings = get_embeddings()
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )

    # 准备目录
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

    # 从本地文件加载文档
    docs = []
    if os.path.exists(DOCUMENTS_DIR):
        txt_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".txt")]
        if txt_files:
            print(f"检测到 {len(txt_files)} 个本地文档文件，直接从本地加载...")
            for filename in txt_files:
                filepath = os.path.join(DOCUMENTS_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # 从内容中提取标题
                title = filename.replace(".txt", "")
                # 尝试从内容第一行获取标题
                lines = content.strip().split("\n")
                if lines and lines[0].startswith("标题："):
                    title = lines[0].replace("标题：", "").strip()
                # 提取来源 URL
                source = ""
                for line in lines:
                    if line.startswith("来源："):
                        source = line.replace("来源：", "").strip()
                        break
                langchain_doc = Document(
                    page_content=content,
                    metadata={
                        "title": title,
                        "source": source or f"本地文件: {filename}",
                    },
                )
                docs.append(langchain_doc)
        else:
            print("本地无文档文件，尝试从网络爬取...")
            documents = scrape_all_pages()
            for doc in documents:
                if not doc["content"]:
                    continue
                langchain_doc = Document(
                    page_content=doc["content"],
                    metadata={
                        "title": doc["title"],
                        "source": doc["url"],
                    },
                )
                docs.append(langchain_doc)
    else:
        print("本地文档目录不存在，尝试从网络爬取...")
        documents = scrape_all_pages()
        for doc in documents:
            if not doc["content"]:
                continue
            langchain_doc = Document(
                page_content=doc["content"],
                metadata={
                    "title": doc["title"],
                    "source": doc["url"],
                },
            )
            docs.append(langchain_doc)

    if not docs:
        print("⚠ 没有获取到任何文档，知识库为空！")
        embeddings = get_embeddings()
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )

    print(f"\n共加载 {len(docs)} 个文档，正在生成嵌入向量...")

    embeddings = get_embeddings()

    # 分批处理，避免 API 限制
    batch_size = 10
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        print(f"  处理批次 {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1}...")
        vector_store = Chroma.from_documents(
            documents=batch,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )

    print(f"✓ 向量数据库构建完成，共 {len(docs)} 个文档")

    # 重新加载完整数据库
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )


def load_vector_store() -> Chroma:
    """加载已存在的向量数据库"""
    if not os.path.exists(CHROMA_PERSIST_DIR):
        return build_vector_store()
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )


def search_knowledge(query: str, k: int = 3) -> List[Document]:
    """搜索知识库中与查询最相关的文档"""
    vector_store = load_vector_store()
    results = vector_store.similarity_search(query, k=k)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="湖湘知识库构建工具")
    parser.add_argument("--rebuild", action="store_true", help="强制重新构建")
    args = parser.parse_args()

    build_vector_store(force_rebuild=args.rebuild)