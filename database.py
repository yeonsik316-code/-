"""SQLite 데이터베이스 초기화 및 CRUD."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import DATABASE_PATH, DEFAULT_CATEGORIES, ensure_dirs, get_admin_phone, get_admin_password


def _hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@contextmanager
def get_connection():
    ensure_dirs()
    conn = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                center TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (author_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS post_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            );
            """
        )

        # 기본 카테고리
        now = datetime.now().isoformat()
        for name in DEFAULT_CATEGORIES:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name, description, created_at) VALUES (?, '', ?)",
                (name, now),
            )

        # 기본 관리자 계정
        admin_phone = get_admin_phone()
        row = conn.execute("SELECT id FROM users WHERE phone = ?", (admin_phone,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (phone, password_hash, name, center, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    admin_phone,
                    _hash_password(get_admin_password()),
                    "관리자",
                    "본사",
                    "admin",
                    now,
                ),
            )


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row) if row else {}


def create_user(phone: str, password: str, name: str, center: str) -> tuple[bool, str]:
    phone = phone.strip().replace("-", "")
    if len(phone) < 10:
        return False, "올바른 전화번호를 입력해 주세요."
    if len(password) < 6:
        return False, "비밀번호는 6자 이상이어야 합니다."
    if not name.strip() or not center.strip():
        return False, "성명과 소속을 입력해 주세요."

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (phone, password_hash, name, center, role, created_at) VALUES (?, ?, ?, ?, 'user', ?)",
                (phone, _hash_password(password), name.strip(), center.strip(), datetime.now().isoformat()),
            )
        return True, "회원가입이 완료되었습니다."
    except sqlite3.IntegrityError:
        return False, "이미 등록된 전화번호입니다."


def authenticate(phone: str, password: str) -> Optional[dict[str, Any]]:
    phone = phone.strip().replace("-", "")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, phone, name, center, role FROM users WHERE phone = ? AND password_hash = ?",
            (phone, _hash_password(password)),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, phone, name, center, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_categories() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, description, created_at FROM categories ORDER BY id"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def create_category(name: str, description: str = "") -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "카테고리 이름을 입력해 주세요."
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO categories (name, description, created_at) VALUES (?, ?, ?)",
                (name, description.strip(), datetime.now().isoformat()),
            )
        return True, "카테고리가 추가되었습니다."
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 카테고리입니다."


def update_category(category_id: int, name: str, description: str = "") -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "카테고리 이름을 입력해 주세요."
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE categories SET name = ?, description = ? WHERE id = ?",
                (name, description.strip(), category_id),
            )
        return True, "카테고리가 수정되었습니다."
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 카테고리 이름입니다."


def delete_category(category_id: int) -> tuple[bool, str]:
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE category_id = ?",
            (category_id,),
        ).fetchone()[0]
        if count > 0:
            return False, f"이 카테고리에 게시글이 {count}개 있어 삭제할 수 없습니다."
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    return True, "카테고리가 삭제되었습니다."


def list_posts(category_id: Optional[int] = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if category_id:
            rows = conn.execute(
                """
                SELECT p.id, p.category_id, p.title, p.content, p.author_id, p.created_at, p.updated_at,
                       c.name AS category_name, u.name AS author_name
                FROM posts p
                JOIN categories c ON p.category_id = c.id
                JOIN users u ON p.author_id = u.id
                WHERE p.category_id = ?
                ORDER BY p.created_at DESC
                """,
                (category_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT p.id, p.category_id, p.title, p.content, p.author_id, p.created_at, p.updated_at,
                       c.name AS category_name, u.name AS author_name
                FROM posts p
                JOIN categories c ON p.category_id = c.id
                JOIN users u ON p.author_id = u.id
                ORDER BY p.created_at DESC
                """
            ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_post(post_id: int) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.id, p.category_id, p.title, p.content, p.author_id, p.created_at, p.updated_at,
                   c.name AS category_name, u.name AS author_name
            FROM posts p
            JOIN categories c ON p.category_id = c.id
            JOIN users u ON p.author_id = u.id
            WHERE p.id = ?
            """,
            (post_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def create_post(category_id: int, title: str, content: str, author_id: int) -> int:
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO posts (category_id, title, content, author_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (category_id, title.strip(), content, author_id, now, now),
        )
        return cursor.lastrowid


def delete_post(post_id: int) -> None:
    files = get_post_files(post_id)
    with get_connection() as conn:
        conn.execute("DELETE FROM post_files WHERE post_id = ?", (post_id,))
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    for f in files:
        path = Path(f["stored_path"])
        if path.exists():
            path.unlink()


def add_post_file(post_id: int, filename: str, stored_name: str, file_type: str) -> int:
    from config import UPLOAD_DIR

    stored_path = UPLOAD_DIR / stored_name
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO post_files (post_id, filename, stored_name, file_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (post_id, filename, stored_name, file_type, datetime.now().isoformat()),
        )
        return cursor.lastrowid


def get_post_files(post_id: int) -> list[dict[str, Any]]:
    from config import UPLOAD_DIR

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, post_id, filename, stored_name, file_type, created_at FROM post_files WHERE post_id = ?",
            (post_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["stored_path"] = str(UPLOAD_DIR / d["stored_name"])
        result.append(d)
    return result
