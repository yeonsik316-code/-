"""config 이름 호환용 — settings 모듈 re-export."""
from settings import (  # noqa: F401
    BASE_DIR,
    DATA_DIR,
    DATA_ROOT,
    DATABASE_PATH,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_PHONE,
    DEFAULT_ADMIN_SETUP_CODE,
    DEFAULT_CATEGORIES,
    EMAIL_PATTERN,
    UPLOAD_DIR,
    ensure_dirs,
    get_admin_email,
    get_admin_password,
    get_admin_phone,
    get_admin_setup_code,
)
