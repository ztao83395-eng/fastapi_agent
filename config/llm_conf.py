import os
from pathlib import Path

# 优先加载项目根目录的 env 或 .env 文件（Docker 中不存在，环境变量由 compose 注入）
for _env_name in ("env", ".env"):
    _env_path = Path(_env_name)
    if _env_path.is_file():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=_env_path)
        break

# ========== 大语言模型（对话 / Agent / 评测判定）—— DeepSeek ==========
# DeepSeek 官方 OpenAI 兼容接口：https://api.deepseek.com/v1
# 注意：deepseek-reasoner 不支持 function calling，Agent 工具调用请用 deepseek-chat
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_API_KEY = DEEPSEEK_API_KEY or os.getenv("BAILIAN_API_KEY", "")  # 兼容旧配置，未配 DeepSeek 时回退百炼
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))

# ========== Embedding 模型（向量化检索）—— 保留阿里云百炼 ==========
# DeepSeek 官方 API 不提供 embedding 服务，RAG 向量化继续走百炼 text-embedding-v4
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", "")
BAILIAN_BASE_URL = os.getenv("BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", BAILIAN_API_KEY)
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", BAILIAN_BASE_URL)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")

# ========== 向量存储目录 ==========
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "./vector_store")

# ========== AI 每日 Token 消费限额（按用户） ==========
AI_DAILY_TOKEN_LIMIT = int(os.getenv("AI_DAILY_TOKEN_LIMIT", "50000"))
