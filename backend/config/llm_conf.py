import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

# Load the repository-local env file for local development. Docker injects env vars directly.
# The file stays in the project root after the backend is moved into its own directory.
for _env_path in (
    PROJECT_ROOT / ".env",
    BACKEND_DIR / ".env",
    Path("env"),
    Path(".env"),
):
    if _env_path.is_file():
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=_env_path)
        break



OPENAI_API_KEY =os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
).strip().rstrip("/")

LLM_API_KEY = OPENAI_API_KEY
LLM_BASE_URL = OPENAI_BASE_URL
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "").strip() or None

_temperature = os.getenv("TEMPERATURE", "").strip()
TEMPERATURE = float(_temperature) if _temperature else None


# OpenAI embedding models must be used to create and query the same vector store.
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "") or OPENAI_API_KEY
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "") or OPENAI_BASE_URL
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gpt-5.6-terra")


def get_chat_model_kwargs(model: str | None = None) -> dict:
    """Return only supported, explicitly configured ChatOpenAI parameters."""
    kwargs = {
        "api_key": LLM_API_KEY,
        "base_url": LLM_BASE_URL,
        "model": model or LLM_MODEL,
    }
    if TEMPERATURE is not None:
        kwargs["temperature"] = TEMPERATURE
    if REASONING_EFFORT:
        kwargs["reasoning_effort"] = REASONING_EFFORT
    return kwargs


def get_embedding_model_kwargs() -> dict:
    """Return embedding configuration compatible with third-party OpenAI APIs."""
    return {
        "model": EMBEDDING_MODEL,
        "api_key": EMBEDDING_API_KEY,
        "base_url": EMBEDDING_BASE_URL.rstrip("/"),
        # Send strings directly. Some compatible providers reject local
        # tokenized input or do not expose a matching tokenizer locally.
        "check_embedding_ctx_length": False,
    }


_vector_store_dir = Path(os.getenv("VECTOR_STORE_DIR", "vector_store"))
if not _vector_store_dir.is_absolute():
    _vector_store_dir = BACKEND_DIR / _vector_store_dir
VECTOR_STORE_DIR = str(_vector_store_dir)
# Keep GPT vectors in a separate collection from the previous vector collection.
VECTOR_COLLECTION_NAME = os.getenv("VECTOR_COLLECTION_NAME", "news_vectors_gpt")

AI_DAILY_TOKEN_LIMIT = int(os.getenv("AI_DAILY_TOKEN_LIMIT", "50000"))
