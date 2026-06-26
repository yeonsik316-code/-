# 엔지니어 현장 지원 플랫폼

고객사 공지, 고객 대응 가이드, 유지보수 매뉴얼 등을 엔지니어가 현장에서 확인할 수 있는 Streamlit 웹 플랫폼입니다.

## 기능

| 기능 | 설명 |
|------|------|
| 회원가입 | 성명, 소속(센터), 전화번호, 비밀번호 |
| 로그인/로그아웃 | 전화번호 + 비밀번호 |
| 게시판 카테고리 | 추가/수정/삭제 (관리자) |
| 기본 카테고리 | 공지사항, 매뉴얼/양식, 자주 묻는 질문 |
| 게시글 | 등록/삭제 (관리자), 조회 (전체 회원) |
| 파일 업로드 | 이미지, PDF, 문서 등 다중 업로드 |
| 파일 다운로드 | 게시글 조회 시 다운로드 및 이미지 미리보기 |
| 권한 분리 | 관리자(전체 권한) / 사용자(조회만) |

## 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

### 데이터 저장 위치

회원·게시글·업로드 파일은 **프로젝트 폴더가 아닌** 아래 경로에 저장됩니다.

```
C:\Users\본인계정\field_support_platform\
```

사이트를 닫아도 이 폴더의 데이터는 유지됩니다. (사이드바 **데이터 저장 위치**에서 확인 가능)

### 관리자 로그인 (Secrets 설정 불필요)

| 항목 | 값 |
|------|-----|
| 전화번호 | `01000000000` |
| 비밀번호 | `admin1234` |

로그인 후 사이드바에 **✏️ 글 작성**, **⚙️ 카테고리 관리**, **👥 회원/권한 관리**가 표시됩니다.

### 다른 계정을 관리자로 만들기

1. 회원가입 시 **관리자 등록 코드** 입력: `fieldadmin2024`
2. 또는 관리자로 로그인 → **회원/권한 관리**에서 지정
3. 시스템에 관리자가 없으면 **첫 회원가입 계정이 자동으로 관리자**

> 운영 전 기본 관리자 비밀번호를 변경하세요. (로그인 후 회원/권한 관리 또는 `.streamlit/secrets.toml`)

## GitHub 레포지토리 생성 및 배포

### 1. GitHub에 레포지토리 생성

1. [GitHub](https://github.com) 로그인
2. **New repository** 클릭
3. Repository name 입력 (예: `field-support-platform`)
4. **Public** 선택 (누구나 접속 가능)
5. **Create repository**

### 2. 코드 업로드

```bash
cd "게시용 웹 사이트 개설"
git init
git add .
git commit -m "Initial commit: Streamlit 현장 지원 플랫폼"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 3. Streamlit Community Cloud 배포 (무료, 공개)

1. [share.streamlit.io](https://share.streamlit.io) 접속 후 GitHub 연동
2. **New app** 클릭
3. Repository, Branch(`main`), Main file path(`app.py`) 선택
4. **Advanced settings > Secrets** (선택 — 없으면 기본값 사용)

```toml
[admin]
phone = "01012345678"
password = "변경할_비밀번호"
setup_code = "fieldadmin2024"
```

Secrets 메뉴가 없거나 설정하지 않아도, 앱 로그인 페이지의 **기본 관리자 계정**으로 이용 가능합니다.

5. **Deploy** 클릭 → 공개 URL 발급 (예: `https://your-app.streamlit.app`)

## 권한 구조

```
관리자 (admin)
  ├── 카테고리 추가/수정/삭제
  ├── 게시글 작성/삭제
  └── 모든 게시글 조회

사용자 (user) — 회원가입 시 기본 권한
  └── 게시글 조회 및 파일 다운로드
```

## 프로젝트 구조

```
├── app.py              # Streamlit 메인 UI
├── database.py         # SQLite DB 및 CRUD
├── config.py           # 설정
├── requirements.txt
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── data/               # (프로젝트 내 — 사용 안 함)
└── uploads/            # (프로젝트 내 — 사용 안 함)

실제 데이터: `%USERPROFILE%\field_support_platform\`
```

## 데이터 보존 참고

Streamlit Community Cloud는 **재배포 시 로컬 파일이 초기화**될 수 있습니다.  
장기 운영 시 PostgreSQL(Supabase 등) 외부 DB 연동을 권장합니다.

## 기술 스택

- Python 3.10+
- Streamlit
- SQLite
