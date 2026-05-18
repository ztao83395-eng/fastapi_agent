import os
from pathlib import Path

# 优先加载项目根目录的 env 或 .env 文件（Docker 中不存在，环境变量由 compose 注入）
for _env_name in ("env", ".env"):
    _env_path = Path(_env_name)
    if _env_path.is_file():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=_env_path)
        break

# ========== 阿里云百炼配置 ==========
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", "sk-585fdc53eb1344c79a3b567aa35b1da4")
BAILIAN_BASE_URL = os.getenv("BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# ========== 模型选择 ==========
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))

# ========== 向量存储目录 ==========
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "./vector_store")
