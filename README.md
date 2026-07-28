# 朱熹对话 - 湖湘文化 AI 助手

基于 RAG（检索增强生成）的朱熹角色对话系统，融合湖湘文化知识库，通过 Streamlit 提供交互式对话界面。

## 技术架构

| 组件 | 技术 |
|------|------|
| 大语言模型 | Qwen2.5-7B-Instruct (SiliconFlow) |
| 文本嵌入 | BAAI/bge-m3 (SiliconFlow) |
| 向量数据库 | Chroma |
| RAG 框架 | LangChain |
| 前端界面 | Streamlit |

## 快速开始

### 1. 环境准备

```bash
# 克隆项目后进入目录
cd zhuxi_chatbot

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

**方式一：环境变量（推荐用于本地开发）**

```bash
# Windows PowerShell
$env:SILICONFLOW_API_KEY="sk-your-key-here"

# Windows CMD
set SILICONFLOW_API_KEY=sk-your-key-here

# Linux/macOS
export SILICONFLOW_API_KEY=sk-your-key-here
```

**方式二：Streamlit Secrets（用于 Streamlit Cloud 部署）**

部署到 Streamlit Community Cloud 时，在 Dashboard > App > Manage app > Secrets 中配置 `SILICONFLOW_API_KEY`。

### 3. 构建知识库

```bash
python knowledge_base.py
```

首次运行会自动加载 `data/documents/` 下的湖湘文化文档，生成嵌入向量并存储到 Chroma 数据库。

### 4. 启动应用

```bash
streamlit run app.py
```

打开浏览器访问 `http://localhost:8510`。

---

## 部署方案

### 方案一：Streamlit Community Cloud（推荐）

免费、无需服务器维护，适合个人项目和学习。

**前置条件**
- GitHub 账号
- Streamlit 账号（可用 GitHub 登录）

**部署步骤**

1. **将代码推送到 GitHub 公开仓库**

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/zhuxi-chatbot.git
git push -u origin main
```

2. **登录 [Streamlit Community Cloud](https://streamlit.io/cloud)**

3. **点击 "New app"，选择你的 GitHub 仓库**
   - Repository: `yourusername/zhuxi-chatbot`
   - Branch: `main`
   - Main file path: `app.py`

4. **配置 Secrets**
   - 部署后进入 App Dashboard
   - 点击右上角 "⋮" → "Settings" → "Secrets"
   - 添加：`SILICONFLOW_API_KEY = "sk-your-key-here"`

5. **点击 "Deploy"**

> **注意**：首次部署需要构建向量数据库。由于 Streamlit Cloud 的文件系统是临时的，建议：
> - 将 `chroma_db/` 文件夹提交到 GitHub（已持久化的向量数据）
> - 或在 `app.py` 启动时自动构建（首次启动较慢）

---

### 方案二：自有服务器 / 云服务器部署

适合需要完全控制、私有化部署的场景。

**以 Ubuntu 服务器为例**

```bash
# 1. 连接服务器并更新
ssh user@your-server-ip
sudo apt update && sudo apt upgrade -y

# 2. 安装 Python 和依赖
sudo apt install -y python3-pip python3-venv git

# 3. 克隆项目
git clone https://github.com/yourusername/zhuxi-chatbot.git
cd zhuxi-chatbot

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 设置环境变量
export SILICONFLOW_API_KEY="sk-your-key-here"

# 7. 构建知识库（首次运行）
python knowledge_base.py

# 8. 使用 systemd 或服务管理器运行 Streamlit
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

**使用 Nginx 反向代理（可选）**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### 方案三：Docker 部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 构建知识库
RUN python knowledge_base.py

EXPOSE 8510

CMD ["streamlit", "run", "app.py", "--server.port=8510", "--server.address=0.0.0.0"]
```

```bash
# 构建镜像
docker build -t zhuxi-chatbot .

# 运行容器
docker run -d -p 8510:8510 -e SILICONFLOW_API_KEY=sk-your-key-here zhuxi-chatbot
```

---

## 项目结构

```
zhuxi_chatbot/
├── app.py                  # Streamlit 前端
├── zhuxi_bot.py           # 朱熹对话机器人（RAG 逻辑）
├── knowledge_base.py      # 知识库构建（嵌入 + Chroma）
├── requirements.txt       # Python 依赖
├── README.md              # 项目说明
├── .streamlit/
│   ├── config.toml        # Streamlit 主题配置
│   └── secrets.toml       # 密钥配置（本地模板，不提交到 Git）
├── data/
│   └── documents/         # 湖湘文化知识文本
└── chroma_db/             # Chroma 向量数据库
```

## 许可证

MIT License