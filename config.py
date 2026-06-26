"""앱 설정."""
import os
from pathlib import Path

# 프로젝트 폴더 (코드 위치)
BASE_DIR = Path(__file__).resolve().parent

# 데이터는 사용자 홈 폴더에 저장 → 브라우저/터미널 위치와 무관하게 유지
DATA_ROOT = Path(
    os.environ.get(
        "FIELD_PLATFORM_DATA",
        str(Path.home() / "field_support_platform"),
    )
)
DATA_DIR = DATA_ROOT / "data"
UPLOAD_DIR = DATA_ROOT / "uploads"
DATABASE_PATH = DATA_DIR / "app.db"

# 기본 카테고리
DEFAULT_CATEGORIES = [
    "공지사항",
    "매뉴얼/양식",
    "자주 묻는 질문",
]

# 회원가입 시 이 코드를 입력하면 관리자로 등록 (Secrets 불필요)
DEFAULT_ADMIN_SETUP_CODE = "fieldadmin2024"

# 최초 설치 시 자동 생성되는 관리자 (로그인 페이지에 표시)
DEFAULT_ADMIN_PHONE = "01000000000"
DEFAULT_ADMIN_PASSWORD = "admin1234"


def get_admin_setup_code() -> str:
    env = os.getenv("ADMIN_SETUP_CODE")
    if env:
        return env
    try:
        import streamlit as st
        return st.secrets.get("admin", {}).get("setup_code", DEFAULT_ADMIN_SETUP_CODE)
    except Exception:
        return DEFAULT_ADMIN_SETUP_CODE


def get_admin_phone() -> str:
    env = os.getenv("ADMIN_PHONE")
    if env:
        return env
    try:
        import streamlit as st
        return st.secrets.get("admin", {}).get("phone", DEFAULT_ADMIN_PHONE)
    except Exception:
        return DEFAULT_ADMIN_PHONE


def get_admin_password() -> str:
    env = os.getenv("ADMIN_PASSWORD")
    if env:
        return env
    try:
        import streamlit as st
        return st.secrets.get("admin", {}).get("password", DEFAULT_ADMIN_PASSWORD)
    except Exception:
        return DEFAULT_ADMIN_PASSWORD


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
