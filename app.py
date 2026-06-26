"""Streamlit 메인 앱 — 엔지니어 현장 지원 플랫폼."""
import uuid
from pathlib import Path

import streamlit as st

from config import (
    DATA_ROOT,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_PHONE,
    UPLOAD_DIR,
    ensure_dirs,
    get_admin_setup_code,
)
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
    list_users,
    set_user_role,
    update_category,
)

st.set_page_config(
    page_title="현장 지원 플랫폼",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_dirs()
init_db()


def init_session():
    defaults = {
        "user": None,
        "page": "home",
        "view_post_id": None,
        "selected_category": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### 🔧 현장 지원 플랫폼")
    st.caption("공지 · 매뉴얼 · FAQ")

    if is_logged_in():
        user = st.session_state.user
        role_label = "🔴 관리자" if is_admin() else "🔵 사용자"
        st.success(f"**{user['name']}** ({user['center']})")
        st.caption(f"권한: {role_label}")

        if st.button("🏠 홈", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.view_post_id = None
            st.rerun()

        if st.button("📋 게시판", use_container_width=True):
            st.session_state.page = "board"
            st.session_state.view_post_id = None
            st.rerun()

        if is_admin():
            if st.button("✏️ 글 작성", use_container_width=True, type="primary"):
                st.session_state.page = "write"
                st.session_state.view_post_id = None
                st.rerun()
            if st.button("⚙️ 카테고리 관리", use_container_width=True):
                st.session_state.page = "categories"
                st.session_state.view_post_id = None
                st.rerun()
            if st.button("👥 회원/권한 관리", use_container_width=True):
                st.session_state.page = "users"
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

    with st.expander("💾 데이터 저장 위치"):
        st.code(str(DATA_ROOT), language=None)
        st.caption("회원·게시글은 위 폴더에 저장됩니다. 사이트를 닫아도 유지됩니다.")

st.markdown(
    """
    <div class="main-header">
        <h1>🔧 엔지니어 현장 지원 플랫폼</h1>
        <p>고객사 공지 · 대응 가이드 · 유지보수 매뉴얼을 한곳에서 확인하세요</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def page_home():
    st.subheader("📌 최근 게시글")
    if not is_logged_in():
        st.info("게시글을 보려면 로그인해 주세요. (사이드바 → 로그인)")

    posts = list_posts()
    if not posts:
        st.info("등록된 게시글이 없습니다. 관리자로 로그인 후 글을 작성해 주세요.")
        return

    for post in posts[:10]:
        created = post["created_at"][:10]
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"**[{post['category_name']}]** {post['title']}  \n"
                f"<small>{post['author_name']} · {created}</small>",
                unsafe_allow_html=True,
            )
        with col2:
            if is_logged_in() and st.button("보기", key=f"home_view_{post['id']}"):
                st.session_state.view_post_id = post["id"]
                st.session_state.page = "view_post"
                st.rerun()
        st.divider()


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

    with st.expander("관리자 최초 로그인 정보 (Secrets 설정 불필요)"):
        st.markdown(
            f"""
            앱을 처음 설치했을 때 자동 생성되는 관리자 계정입니다.

            | 항목 | 값 |
            |------|-----|
            | 전화번호 | `{DEFAULT_ADMIN_PHONE}` |
            | 비밀번호 | `{DEFAULT_ADMIN_PASSWORD}` |

            로그인 후 사이드바에 **🔴 관리자** 와 **✏️ 글 작성** 버튼이 보입니다.

            **다른 계정을 관리자로 만들기:** 회원가입 시 관리자 등록 코드 입력  
            → 기본 코드: `{get_admin_setup_code()}`
            """
        )


def page_register():
    st.subheader("📝 회원가입")
    with st.form("register_form"):
        name = st.text_input("성명", placeholder="홍길동")
        center = st.text_input("소속(센터)", placeholder="서울센터")
        phone = st.text_input("전화번호", placeholder="01012345678")
        password = st.text_input("비밀번호", type="password", help="6자 이상")
        password2 = st.text_input("비밀번호 확인", type="password")
        admin_code = st.text_input(
            "관리자 등록 코드 (선택)",
            placeholder="관리자로 등록할 때만 입력",
            help=f"관리자 권한이 필요하면 코드 입력: {get_admin_setup_code()}",
        )
        submitted = st.form_submit_button("회원가입", type="primary", use_container_width=True)

    if submitted:
        if password != password2:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            ok, msg, user = create_user(phone, password, name, center, admin_code)
            if ok:
                st.session_state.user = user
                st.session_state.page = "home"
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def page_board():
    if not is_logged_in():
        st.warning("게시판을 이용하려면 로그인이 필요합니다.")
        return

    categories = list_categories()
    cat_names = [c["name"] for c in categories]
    cat_ids = [c["id"] for c in categories]

    if is_admin():
        if st.button("✏️ 새 글 작성"):
            st.session_state.page = "write"
            st.rerun()

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

    files = get_post_files(post_id)
    if files:
        st.markdown("### 📎 첨부 파일")
        for f in files:
            path = Path(f["stored_path"])
            if path.exists():
                file_bytes = path.read_bytes()
                if f["file_type"].startswith("image/"):
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
        if is_admin() and st.button("🗑️ 삭제", type="secondary"):
            delete_post(post_id)
            st.session_state.page = "board"
            st.session_state.view_post_id = None
            st.rerun()


def page_write():
    if not is_admin():
        st.error("관리자만 글을 작성할 수 있습니다. 관리자로 로그인하거나 회원가입 시 관리자 코드를 입력하세요.")
        return

    st.subheader("✏️ 새 게시글 작성")
    categories = list_categories()
    if not categories:
        st.warning("먼저 카테고리를 추가해 주세요.")
        return

    title = st.text_input("제목", key="write_title")
    category_id = st.selectbox(
        "카테고리",
        options=[c["id"] for c in categories],
        format_func=lambda x: next(c["name"] for c in categories if c["id"] == x),
    )
    content = st.text_area("내용", height=300, key="write_content")
    uploaded = st.file_uploader(
        "파일/이미지 업로드",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "xls", "xlsx", "zip", "txt"],
    )

    if st.button("등록", type="primary", use_container_width=True):
        if not title.strip():
            st.error("제목을 입력해 주세요.")
        elif not content.strip():
            st.error("내용을 입력해 주세요.")
        else:
            post_id = create_post(category_id, title, content, st.session_state.user["id"])
            save_uploaded_files(post_id, uploaded)
            st.session_state.view_post_id = post_id
            st.session_state.page = "view_post"
            st.rerun()


def page_categories():
    if not is_admin():
        st.error("관리자만 카테고리를 관리할 수 있습니다.")
        return

    st.subheader("⚙️ 카테고리 관리")

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

    for cat in list_categories():
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


def page_users():
    if not is_admin():
        st.error("관리자만 회원을 관리할 수 있습니다.")
        return

    st.subheader("👥 회원 / 권한 관리")
    st.caption(f"관리자 등록 코드 (회원가입 시 사용): `{get_admin_setup_code()}`")

    for u in list_users():
        role_label = "관리자" if u["role"] == "admin" else "사용자"
        st.markdown(f"**{u['name']}** · {u['center']} · {u['phone']} · `{role_label}`")

        if u["id"] != st.session_state.user["id"]:
            col1, col2 = st.columns(2)
            with col1:
                if u["role"] != "admin" and st.button(
                    "관리자로 지정", key=f"promote_{u['id']}"
                ):
                    ok, msg = set_user_role(u["id"], "admin")
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)
            with col2:
                if u["role"] == "admin" and st.button(
                    "사용자로 변경", key=f"demote_{u['id']}"
                ):
                    ok, msg = set_user_role(u["id"], "user")
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)
        st.divider()


PAGES = {
    "home": page_home,
    "login": page_login,
    "register": page_register,
    "board": page_board,
    "view_post": page_view_post,
    "write": page_write,
    "categories": page_categories,
    "users": page_users,
}

current = st.session_state.page
if current not in PAGES:
    current = "home"

PAGES[current]()
