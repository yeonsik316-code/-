"""앱 설정."""
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_ROOT = Path(
    os.environ.get(
        "FIELD_PLATFORM_DATA",
        str(Path.home() / "field_support_platform"),
    )
)
UPLOAD_DIR = DATA_ROOT / "uploads"

DEFAULT_CATEGORIES = [
    "공지사항",
    "매뉴얼/양식",
    "자주 묻는 질문",
]

DEFAULT_ADMIN_SETUP_CODE = "fieldadmin2024"
DEFAULT_ADMIN_PHONE = "01000000000"
DEFAULT_ADMIN_PASSWORD = "admin1234"
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_MONGODB_DB = "field_support_platform"

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _secrets_get(section: str, key: str, default: str = "") -> str:
    env_key = f"{section.upper()}_{key.upper()}"
    env_val = os.getenv(env_key)
    if env_val:
        return env_val
    try:
        import streamlit as st
        return st.secrets.get(section, {}).get(key, default)
    except Exception:
        return default


def get_admin_setup_code() -> str:
    return _secrets_get("admin", "setup_code", DEFAULT_ADMIN_SETUP_CODE)


def get_admin_phone() -> str:
    return _secrets_get("admin", "phone", DEFAULT_ADMIN_PHONE)


def get_admin_password() -> str:
    return _secrets_get("admin", "password", DEFAULT_ADMIN_PASSWORD)


def get_admin_email() -> str:
    return _secrets_get("admin", "email", DEFAULT_ADMIN_EMAIL)


def get_mongodb_uri() -> str:
    uri = os.getenv("MONGODB_URI", "")
    if not uri:
        uri = _secrets_get("mongodb", "uri", "")
    return uri.strip()


def get_mongodb_db_name() -> str:
    name = os.getenv("MONGODB_DB", "")
    if not name:
        name = _secrets_get("mongodb", "db_name", DEFAULT_MONGODB_DB)
    return name.strip() or DEFAULT_MONGODB_DB


def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "") or _secrets_get("openai", "api_key", "")


def ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
