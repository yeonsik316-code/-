"""MongoDB Atlas 데이터베이스 CRUD."""
import hashlib
import re
from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from gridfs import GridFS
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from settings import (
    DEFAULT_CATEGORIES,
    EMAIL_PATTERN,
    get_admin_email,
    get_admin_password,
    get_admin_phone,
    get_admin_setup_code,
    get_mongodb_db_name,
    get_mongodb_uri,
)

_client: Optional[MongoClient] = None


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _normalize_phone(phone: str) -> str:
    return phone.strip().replace("-", "").replace(" ", "")


def _oid(id_value: str | ObjectId) -> ObjectId:
    if isinstance(id_value, ObjectId):
        return id_value
    return ObjectId(str(id_value))


def _id_str(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
    return doc


def get_db():
    global _client
    uri = get_mongodb_uri()
    if not uri:
        raise RuntimeError(
            "MongoDB URI가 설정되지 않았습니다. "
            ".streamlit/secrets.toml에 [mongodb] uri를 추가하세요."
        )
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    return _client[get_mongodb_db_name()]


def get_gridfs() -> GridFS:
    return GridFS(get_db())


def init_db():
    db = get_db()
    db.users.create_index("phone", unique=True)
    db.users.create_index("email", unique=True)
    db.categories.create_index("name", unique=True)
    db.posts.create_index("category_id")
    db.posts.create_index("created_at")

    now = datetime.now().isoformat()
    for name in DEFAULT_CATEGORIES:
        db.categories.update_one(
            {"name": name},
            {"$setOnInsert": {"name": name, "description": "", "created_at": now}},
            upsert=True,
        )

    if db.users.count_documents({"role": "admin"}) == 0:
        db.users.insert_one(
            {
                "phone": _normalize_phone(get_admin_phone()),
                "password_hash": _hash_password(get_admin_password()),
                "name": "관리자",
                "center": "본사",
                "email": get_admin_email().strip().lower(),
                "role": "admin",
                "created_at": now,
            }
        )


def count_admins() -> int:
    return get_db().users.count_documents({"role": "admin"})


def create_user(
    phone: str,
    password: str,
    name: str,
    center: str,
    email: str,
    admin_code: str = "",
) -> tuple[bool, str, Optional[dict[str, Any]]]:
    phone = _normalize_phone(phone)
    email = email.strip().lower()

    if len(phone) < 10:
        return False, "올바른 전화번호를 입력해 주세요.", None
    if len(password) < 6:
        return False, "비밀번호는 6자 이상이어야 합니다.", None
    if not name.strip() or not center.strip():
        return False, "성명과 소속을 입력해 주세요.", None
    if not email or not EMAIL_PATTERN.match(email):
        return False, "올바른 이메일을 입력해 주세요.", None

    role = "user"
    setup_code = get_admin_setup_code().strip()
    if admin_code.strip() and admin_code.strip() == setup_code:
        role = "admin"
    elif count_admins() == 0:
        role = "admin"

    doc = {
        "phone": phone,
        "password_hash": _hash_password(password),
        "name": name.strip(),
        "center": center.strip(),
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
    }
    try:
        result = get_db().users.insert_one(doc)
        user = {
            "id": str(result.inserted_id),
            "phone": phone,
            "name": doc["name"],
            "center": doc["center"],
            "email": email,
            "role": role,
        }
        role_msg = "관리자" if role == "admin" else "사용자"
        return True, f"회원가입 완료 ({role_msg} 권한).", user
    except DuplicateKeyError:
        return False, "이미 등록된 전화번호 또는 이메일입니다.", None


def authenticate(phone: str, password: str) -> Optional[dict[str, Any]]:
    phone = _normalize_phone(phone)
    row = get_db().users.find_one(
        {"phone": phone, "password_hash": _hash_password(password)},
        {"phone": 1, "name": 1, "center": 1, "email": 1, "role": 1},
    )
    if not row:
        return None
    return {
        "id": str(row["_id"]),
        "phone": row["phone"],
        "name": row["name"],
        "center": row["center"],
        "email": row.get("email", ""),
        "role": row["role"],
    }


def list_users() -> list[dict[str, Any]]:
    rows = get_db().users.find().sort("_id", 1)
    result = []
    for r in rows:
        result.append(
            {
                "id": str(r["_id"]),
                "phone": r["phone"],
                "name": r["name"],
                "center": r["center"],
                "email": r.get("email", ""),
                "role": r["role"],
                "created_at": r.get("created_at", ""),
            }
        )
    return result


def set_user_role(user_id: str, role: str) -> tuple[bool, str]:
    if role not in ("admin", "user"):
        return False, "잘못된 권한입니다."
    db = get_db()
    if role == "user":
        admin_count = db.users.count_documents({"role": "admin"})
        current = db.users.find_one({"_id": _oid(user_id)}, {"role": 1})
        if current and current.get("role") == "admin" and admin_count <= 1:
            return False, "최소 1명의 관리자가 필요합니다."
    db.users.update_one({"_id": _oid(user_id)}, {"$set": {"role": role}})
    return True, "권한이 변경되었습니다."


def list_categories() -> list[dict[str, Any]]:
    rows = get_db().categories.find().sort("_id", 1)
    return [
        {
            "id": str(r["_id"]),
            "name": r["name"],
            "description": r.get("description", ""),
            "created_at": r.get("created_at", ""),
        }
        for r in rows
    ]


def create_category(name: str, description: str = "") -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "카테고리 이름을 입력해 주세요."
    try:
        get_db().categories.insert_one(
            {
                "name": name,
                "description": description.strip(),
                "created_at": datetime.now().isoformat(),
            }
        )
        return True, "카테고리가 추가되었습니다."
    except DuplicateKeyError:
        return False, "이미 존재하는 카테고리입니다."


def update_category(category_id: str, name: str, description: str = "") -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "카테고리 이름을 입력해 주세요."
    try:
        get_db().categories.update_one(
            {"_id": _oid(category_id)},
            {"$set": {"name": name, "description": description.strip()}},
        )
        return True, "카테고리가 수정되었습니다."
    except DuplicateKeyError:
        return False, "이미 존재하는 카테고리 이름입니다."


def delete_category(category_id: str) -> tuple[bool, str]:
    db = get_db()
    count = db.posts.count_documents({"category_id": category_id})
    if count > 0:
        return False, f"이 카테고리에 게시글이 {count}개 있어 삭제할 수 없습니다."
    db.categories.delete_one({"_id": _oid(category_id)})
    return True, "카테고리가 삭제되었습니다."


def _enrich_post(post: dict) -> dict:
    db = get_db()
    cat = db.categories.find_one({"_id": _oid(post["category_id"])}, {"name": 1})
    author = db.users.find_one({"_id": _oid(post["author_id"])}, {"name": 1})
    return {
        "id": str(post["_id"]),
        "category_id": post["category_id"],
        "title": post["title"],
        "content": post["content"],
        "author_id": post["author_id"],
        "created_at": post.get("created_at", ""),
        "updated_at": post.get("updated_at", ""),
        "category_name": cat["name"] if cat else "",
        "author_name": author["name"] if author else "",
    }


def list_posts(category_id: Optional[str] = None) -> list[dict[str, Any]]:
    query = {}
    if category_id:
        query["category_id"] = category_id
    rows = get_db().posts.find(query).sort("created_at", -1)
    return [_enrich_post(r) for r in rows]


def get_post(post_id: str) -> Optional[dict[str, Any]]:
    try:
        row = get_db().posts.find_one({"_id": _oid(post_id)})
    except InvalidId:
        return None
    return _enrich_post(row) if row else None


def create_post(category_id: str, title: str, content: str, author_id: str) -> str:
    now = datetime.now().isoformat()
    result = get_db().posts.insert_one(
        {
            "category_id": category_id,
            "title": title.strip(),
            "content": content,
            "author_id": author_id,
            "created_at": now,
            "updated_at": now,
        }
    )
    return str(result.inserted_id)


def delete_post(post_id: str) -> None:
    fs = get_gridfs()
    for f in get_post_files(post_id):
        try:
            fs.delete(_oid(f["gridfs_id"]))
        except Exception:
            pass
    get_db().posts.delete_one({"_id": _oid(post_id)})


def add_post_file(post_id: str, filename: str, data: bytes, file_type: str) -> str:
    fs = get_gridfs()
    grid_id = fs.put(
        data,
        filename=filename,
        content_type=file_type,
        metadata={"post_id": post_id},
    )
    return str(grid_id)


def get_post_files(post_id: str) -> list[dict[str, Any]]:
    fs = get_gridfs()
    files = fs.find({"metadata.post_id": post_id})
    result = []
    for f in files:
        result.append(
            {
                "id": str(f._id),
                "gridfs_id": str(f._id),
                "post_id": post_id,
                "filename": f.filename,
                "file_type": f.content_type or "application/octet-stream",
                "data": f.read(),
            }
        )
    return result
