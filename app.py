"""
朱熹对话 - Streamlit 前端界面
基于 RAG 的朱熹角色对话系统
"""

import os
import sys
import streamlit as st

# 将项目目录加入路径
sys.path.insert(0, os.path.dirname(__file__))

from zhuxi_bot import get_bot

# ============ 页面配置 ============

st.set_page_config(
    page_title="朱熹对话",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============ 自定义 CSS ============

PAGE_CSS = """
<style>
    /* 全局样式 */
    .stApp {
        background-color: #faf8f5;
    }

    /* 标题区域 */
    .header-container {
        text-align: left;
        padding: 1.5rem 0 0.5rem 0;
        margin-bottom: 1rem;
    }

    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c2c2c;
        margin: 0;
        padding: 0;
        letter-spacing: 2px;
    }

    .header-subtitle {
        font-size: 0.9rem;
        color: #888;
        margin-top: 4px;
    }

    /* 对话卡片 */
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
    }

    .user-message {
        background-color: #f0ece8;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 8px 0;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .user-avatar {
        background-color: #e74c3c;
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
    }

    .user-content {
        flex: 1;
        color: #333;
        font-size: 1rem;
        line-height: 1.6;
    }

    .bot-message {
        background-color: #fdf6e3;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 8px 0;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .bot-avatar {
        background-color: #d4a017;
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }

    .bot-content {
        flex: 1;
        color: #3a3a3a;
        font-size: 0.95rem;
        line-height: 1.8;
    }

    .bot-content p {
        margin: 0 0 8px 0;
    }

    /* 来源引用 */
    .source-tag {
        display: inline-block;
        background-color: #e8e0d0;
        color: #6b5b3e;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px 4px 2px 0;
    }

    /* 输入区域 */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(transparent, #faf8f5 20%);
        padding: 20px 16px 16px;
        z-index: 100;
    }

    .stTextInput > div > div > input {
        border-radius: 24px !important;
        border: 1px solid #ddd !important;
        padding: 10px 18px !important;
        font-size: 0.95rem !important;
        background-color: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #d4a017 !important;
        box-shadow: 0 2px 12px rgba(212,160,23,0.15) !important;
    }

    /* 按钮 */
    .stButton > button {
        border-radius: 24px !important;
        background-color: #d4a017 !important;
        color: white !important;
        border: none !important;
        padding: 8px 24px !important;
        font-weight: 500 !important;
    }

    .stButton > button:hover {
        background-color: #b8890f !important;
    }

    /* 清除按钮 */
    .clear-btn {
        position: fixed;
        top: 16px;
        right: 16px;
        z-index: 100;
    }

    .clear-btn > button {
        background: transparent !important;
        border: 1px solid #ddd !important;
        color: #888 !important;
        font-size: 0.8rem !important;
        padding: 4px 12px !important;
        border-radius: 16px !important;
    }

    /* 底部留白 */
    .bottom-spacer {
        height: 100px;
    }

    /* 加载动画 */
    .loading-dots:after {
        content: '...';
        animation: dots 1.5s steps(4, end) infinite;
    }

    @keyframes dots {
        0%, 20% { content: '˙'; }
        40% { content: '˙˙'; }
        60% { content: '˙˙˙'; }
        80%, 100% { content: ''; }
    }

    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "bot_error" not in st.session_state:
        st.session_state.bot_error = None

    if "bot" not in st.session_state and not st.session_state.bot_error:
        with st.spinner("老夫正在准备中..."):
            try:
                st.session_state.bot = get_bot()
            except ValueError as e:
                err_msg = str(e)
                if "API Key" in err_msg or "SILICONFLOW" in err_msg:
                    st.session_state.bot_error = err_msg
                else:
                    raise

    if "first_load" not in st.session_state:
        st.session_state.first_load = True


def render_header():
    """渲染页面头部"""
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">朱熹对话</h1>
        <p class="header-subtitle">南宋理学家 · 湖湘文化 · 格物致知</p>
    </div>
    """, unsafe_allow_html=True)


def render_welcome():
    """渲染欢迎消息"""
    welcome_msg = (
        "老夫朱熹，字元晦，号晦庵，南宋理学家也。"
        "曾讲学于岳麓书院，与湖湘渊源颇深。"
        "今日与君相遇，可谓有缘。"
        "若君有问于湖湘风物、儒家义理，老夫愿与君共论之。"
    )
    with st.chat_message("assistant", avatar="📜"):
        st.markdown(welcome_msg)
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})


def render_source_docs(source_docs):
    """渲染知识来源标签"""
    if not source_docs:
        return
    titles = set()
    for doc in source_docs:
        title = doc.metadata.get("title", "")
        if title:
            titles.add(title)
    if titles:
        html = '<div style="margin-top: 8px;">'
        html += '<span style="font-size:0.75rem;color:#888;margin-right:4px;">📖 参考：</span>'
        for t in titles:
            html += f'<span class="source-tag">{t}</span>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)


def render_chat_history():
    """渲染对话历史"""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🍲"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="📜"):
                st.markdown(msg["content"])


def render_api_key_error():
    """渲染 API Key 配置错误提示"""
    st.markdown("""
    <div style="padding: 2rem; background: #fff3cd; border-radius: 12px;
                border: 1px solid #ffc107; margin-top: 2rem;">
        <h3 style="color: #856404; margin-bottom: 1rem;">
            ⚠️ 未配置 SiliconFlow API Key
        </h3>
        <p style="color: #856404; font-size: 1rem; line-height: 1.6;">
            部署到 Streamlit Community Cloud 时，需要在 Dashboard 中配置 Secrets。
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("配置步骤")
    st.markdown("""
    1. 打开你的 App 页面 (`https://share.streamlit.io/...`)
    2. 点击右下角 **⋮ → Settings**（或访问 Streamlit Cloud Dashboard）
    3. 切换到 **Secrets** 标签页
    4. 添加以下内容：
    """)

    st.code("SILICONFLOW_API_KEY = \"你的API密钥\"", language="toml")

    st.markdown("""
    5. 点击 **Save** 保存
    6. 回到 App 页面，点击 **⋮ → Reboot** 重启应用

    ---
    **本地开发时**：通过环境变量配置即可，无需上述步骤。
    ```bash
    set SILICONFLOW_API_KEY=你的API密钥
    ```
    """)


def main():
    """主函数"""
    init_session_state()
    render_header()

    # 如果有 API Key 错误，显示配置指南
    if st.session_state.get("bot_error"):
        render_api_key_error()
        return

    # 清空对话按钮
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("清空对话", type="secondary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.bot.clear_memory()
            st.rerun()

    # 首次加载显示欢迎语
    if st.session_state.first_load and not st.session_state.messages:
        render_welcome()
        st.session_state.first_load = False

    # 渲染历史消息
    render_chat_history()

    # 聊天输入框
    if prompt := st.chat_input("请问朱熹先生...", key="chat_input"):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🍲"):
            st.markdown(prompt)

        # 获取机器人回复
        with st.chat_message("assistant", avatar="📜"):
            with st.spinner("老夫正在思索..."):
                result = st.session_state.bot.ask(prompt)
                answer = result["answer"]
                source_docs = result.get("source_docs", [])

            st.markdown(answer)
            render_source_docs(source_docs)

        # 保存到历史
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()