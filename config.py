"""앱 설정."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_PATH = DATA_DIR / "app.db"

# 기본 카테고리
DEFAULT_CATEGORIES = [
    "공지사항",
    "매뉴얼/양식",
    "자주 묻는 질문",
]

# secrets.toml 또는 환경변수로 관리자 계정 설정
def get_admin_phone() -> str:
    try:
        import streamlit as st
        return st.secrets.get("admin", {}).get("phone", os.getenv("ADMIN_PHONE", "01000000000"))
    except Exception:
        return os.getenv("ADMIN_PHONE", "01000000000")


def get_admin_password() -> str:
    try:
        import streamlit as st
        return st.secrets.get("admin", {}).get("password", os.getenv("ADMIN_PASSWORD", "admin1234"))
    except Exception:
        return os.getenv("ADMIN_PASSWORD", "admin1234")


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
