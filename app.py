"""Streamlit 메인 앱 — 엔지니어 현장 지원 플랫폼."""
import uuid
from pathlib import Path

import streamlit as st

from config import UPLOAD_DIR, ensure_dirs
from database import (
    add_post_file,
    authenticate,
    create_category,
    create_post,
    create_user,
    delete_category,
    delete_post,
    get_post,
    get_post_files,
    init_db,
    list_categories,
    list_posts,
    update_category,
)

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="현장 지원 플랫폼",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_dirs()
init_db()


# ── 세션 상태 ────────────────────────────────────────────────
def init_session():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "view_post_id" not in st.session_state:
        st.session_state.view_post_id = None
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None


init_session()


def is_logged_in() -> bool:
    return st.session_state.user is not None


def is_admin() -> bool:
    return is_logged_in() and st.session_state.user.get("role") == "admin"


def logout():
    st.session_state.user = None
    st.session_state.page = "home"
    st.session_state.view_post_id = None


def save_uploaded_files(post_id: int, uploaded_files) -> None:
    if not uploaded_files:
        return
    for uf in uploaded_files:
        ext = Path(uf.name).suffix
        stored_name = f"{post_id}_{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_DIR / stored_name
        dest.write_bytes(uf.getvalue())
        file_type = uf.type or "application/octet-stream"
        add_post_file(post_id, uf.name, stored_name, file_type)


# ── CSS ──────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #e2e8f0; margin: 0.3rem 0 0 0; }
    .post-card {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        background: #f8fafc;
    }
    .badge-admin { background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
    .badge-user { background: #2563eb; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 현장 지원 플랫폼")
    st.caption("공지 · 매뉴얼 · FAQ")

    if is_logged_in():
        user = st.session_state.user
        role_badge = "관리자" if is_admin() else "사용자"
        st.success(f"**{user['name']}** ({user['center']})")
        st.caption(f"권한: {role_badge}")

        if st.button("🏠 홈", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.view_post_id = None
            st.rerun()

        if st.button("📋 게시판", use_container_width=True):
            st.session_state.page = "board"
            st.session_state.view_post_id = None
            st.rerun()

        if is_admin():
            if st.button("⚙️ 카테고리 관리", use_container_width=True):
                st.session_state.page = "categories"
                st.session_state.view_post_id = None
                st.rerun()
            if st.button("✏️ 글 작성", use_container_width=True):
                st.session_state.page = "write"
                st.session_state.view_post_id = None
                st.rerun()

        st.divider()
        if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
    else:
        st.info("로그인 후 이용 가능합니다.")
        if st.button("🔑 로그인", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
        if st.button("📝 회원가입", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()


# ── 헤더 ─────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">
        <h1>🔧 엔지니어 현장 지원 플랫폼</h1>
        <p>고객사 공지 · 대응 가이드 · 유지보수 매뉴얼을 한곳에서 확인하세요</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── 페이지: 홈 ───────────────────────────────────────────────
def page_home():
    st.subheader("📌 최근 게시글")
    posts = list_posts()
    if not posts:
        st.info("등록된 게시글이 없습니다.")
        return

    for post in posts[:10]:
        created = post["created_at"][:10]
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"**[{post['category_name']}]** {post['title']}  \n"
                    f"<small>{post['author_name']} · {created}</small>",
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("보기", key=f"home_view_{post['id']}"):
                    st.session_state.view_post_id = post["id"]
                    st.session_state.page = "view_post"
                    st.rerun()
            st.divider()


# ── 페이지: 로그인 ───────────────────────────────────────────
def page_login():
    st.subheader("🔑 로그인")
    with st.form("login_form"):
        phone = st.text_input("전화번호", placeholder="01012345678")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", type="primary", use_container_width=True)

    if submitted:
        user = authenticate(phone, password)
        if user:
            st.session_state.user = user
            st.session_state.page = "home"
            st.success(f"{user['name']}님, 환영합니다!")
            st.rerun()
        else:
            st.error("전화번호 또는 비밀번호가 올바르지 않습니다.")

    st.caption("계정이 없으신가요? 사이드바에서 회원가입을 진행해 주세요.")


# ── 페이지: 회원가입 ─────────────────────────────────────────
def page_register():
    st.subheader("📝 회원가입")
    with st.form("register_form"):
        name = st.text_input("성명", placeholder="홍길동")
        center = st.text_input("소속(센터)", placeholder="서울센터")
        phone = st.text_input("전화번호", placeholder="01012345678")
        password = st.text_input("비밀번호", type="password", help="6자 이상")
        password2 = st.text_input("비밀번호 확인", type="password")
        submitted = st.form_submit_button("회원가입", type="primary", use_container_width=True)

    if submitted:
        if password != password2:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            ok, msg = create_user(phone, password, name, center)
            if ok:
                st.success(msg)
                st.info("로그인 페이지에서 로그인해 주세요.")
            else:
                st.error(msg)


# ── 페이지: 게시판 ───────────────────────────────────────────
def page_board():
    if not is_logged_in():
        st.warning("게시판을 이용하려면 로그인이 필요합니다.")
        return

    categories = list_categories()
    cat_names = [c["name"] for c in categories]
    cat_ids = [c["id"] for c in categories]

    selected_name = st.selectbox("카테고리 선택", ["전체"] + cat_names)
    if selected_name == "전체":
        posts = list_posts()
    else:
        idx = cat_names.index(selected_name)
        posts = list_posts(cat_ids[idx])

    st.subheader(f"📋 {selected_name} 게시글 ({len(posts)}건)")

    if not posts:
        st.info("게시글이 없습니다.")
        return

    for post in posts:
        created = post["created_at"][:10]
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"**{post['title']}**  \n"
                f"<small>[{post['category_name']}] {post['author_name']} · {created}</small>",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("보기", key=f"board_view_{post['id']}"):
                st.session_state.view_post_id = post["id"]
                st.session_state.page = "view_post"
                st.rerun()
        st.divider()


# ── 페이지: 게시글 보기 ───────────────────────────────────────
def page_view_post():
    if not is_logged_in():
        st.warning("로그인이 필요합니다.")
        return

    post_id = st.session_state.view_post_id
    if not post_id:
        st.warning("게시글을 선택해 주세요.")
        return

    post = get_post(post_id)
    if not post:
        st.error("게시글을 찾을 수 없습니다.")
        return

    st.subheader(post["title"])
    st.caption(
        f"카테고리: {post['category_name']} | "
        f"작성자: {post['author_name']} | "
        f"작성일: {post['created_at'][:16].replace('T', ' ')}"
    )
    st.markdown("---")
    st.markdown(post["content"])

    # 첨부 파일
    files = get_post_files(post_id)
    if files:
        st.markdown("### 📎 첨부 파일")
        for f in files:
            path = Path(f["stored_path"])
            if path.exists():
                file_bytes = path.read_bytes()
                is_image = f["file_type"].startswith("image/")
                if is_image:
                    st.image(file_bytes, caption=f["filename"], use_container_width=True)
                st.download_button(
                    label=f"⬇️ {f['filename']} 다운로드",
                    data=file_bytes,
                    file_name=f["filename"],
                    mime=f["file_type"],
                    key=f"dl_{f['id']}",
                )
            else:
                st.warning(f"{f['filename']} — 파일을 찾을 수 없습니다.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 목록으로"):
            st.session_state.page = "board"
            st.session_state.view_post_id = None
            st.rerun()
    with col2:
        if is_admin():
            if st.button("🗑️ 삭제", type="secondary"):
                delete_post(post_id)
                st.success("게시글이 삭제되었습니다.")
                st.session_state.page = "board"
                st.session_state.view_post_id = None
                st.rerun()


# ── 페이지: 글 작성 (관리자) ─────────────────────────────────
def page_write():
    if not is_admin():
        st.error("관리자만 글을 작성할 수 있습니다.")
        return

    st.subheader("✏️ 새 게시글 작성")
    categories = list_categories()

    with st.form("write_form"):
        title = st.text_input("제목")
        category_id = st.selectbox(
            "카테고리",
            options=[c["id"] for c in categories],
            format_func=lambda x: next(c["name"] for c in categories if c["id"] == x),
        )
        content = st.text_area("내용", height=300)
        uploaded = st.file_uploader(
            "파일/이미지 업로드",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "xls", "xlsx", "zip", "txt"],
        )
        submitted = st.form_submit_button("등록", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("제목을 입력해 주세요.")
        elif not content.strip():
            st.error("내용을 입력해 주세요.")
        else:
            post_id = create_post(category_id, title, content, st.session_state.user["id"])
            save_uploaded_files(post_id, uploaded)
            st.success("게시글이 등록되었습니다.")
            st.session_state.view_post_id = post_id
            st.session_state.page = "view_post"
            st.rerun()


# ── 페이지: 카테고리 관리 (관리자) ───────────────────────────
def page_categories():
    if not is_admin():
        st.error("관리자만 카테고리를 관리할 수 있습니다.")
        return

    st.subheader("⚙️ 카테고리 관리")

    # 추가
    with st.expander("➕ 카테고리 추가", expanded=False):
        with st.form("add_cat"):
            new_name = st.text_input("카테고리 이름")
            new_desc = st.text_input("설명 (선택)")
            if st.form_submit_button("추가"):
                ok, msg = create_category(new_name, new_desc)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    categories = list_categories()
    for cat in categories:
        with st.container():
            st.markdown(f"#### {cat['name']}")
            if cat["description"]:
                st.caption(cat["description"])

            with st.form(f"edit_cat_{cat['id']}"):
                edit_name = st.text_input("이름", value=cat["name"], key=f"name_{cat['id']}")
                edit_desc = st.text_input("설명", value=cat["description"], key=f"desc_{cat['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("수정"):
                        ok, msg = update_category(cat["id"], edit_name, edit_desc)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with col2:
                    if st.form_submit_button("삭제"):
                        ok, msg = delete_category(cat["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            st.divider()


# ── 페이지 라우팅 ────────────────────────────────────────────
PAGES = {
    "home": page_home,
    "login": page_login,
    "register": page_register,
    "board": page_board,
    "view_post": page_view_post,
    "write": page_write,
    "categories": page_categories,
}

current = st.session_state.page
if current not in PAGES:
    current = "home"

PAGES[current]()
