# UNI Backend 🌱

> 비장애 형제를 위한 익명 커뮤니티 플랫폼의 REST API 서버

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue?logo=postgresql)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📑 목차

- [개요](#개요)
- [기술 스택](#기술-스택)
- [설치 및 실행](#설치-및-실행)
- [환경변수](#환경변수)
- [API 엔드포인트](#api-엔드포인트)
- [프로젝트 구조](#프로젝트-구조)
- [주요 기능](#주요-기능)
- [OAuth 설정](#oauth-설정)
- [배포](#배포)

---

## 개요

UNI 백엔드는 비장애 형제들을 위한 익명 커뮤니티 플랫폼입니다. 사용자는 자신의 고민을 익명으로 공유하고, 커뮤니티에서 다양한 경험을 나눌 수 있습니다.

**핵심 기능:**
- 🔐 **소셜 로그인** (카카오, 구글 OAuth 2.0)
- 👥 **익명 커뮤니티** (게시글, 댓글, 좋아요)
- 📮 **익명우편소** (고민 제출)
- 🔑 **JWT 기반 인증**

---

## 기술 스택

| 계층 | 기술 |
|------|------|
| **언어** | Python 3.10+ |
| **프레임워크** | FastAPI |
| **데이터베이스** | PostgreSQL 14+ |
| **ORM** | SQLAlchemy |
| **인증** | JWT (python-jose) |
| **마이그레이션** | Alembic |
| **HTTP 클라이언트** | httpx |
| **배포** | Render |

---

## 설치 및 실행

### 1️⃣ 패키지 설치

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2️⃣ 환경변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 아래 내용을 입력합니다.

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/uni_db

# JWT
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 카카오 OAuth
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret
KAKAO_REDIRECT_URI=https://www.uni-us.site/api/auth/kakao/callback

# 구글 OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://www.uni-us.site/api/auth/google/callback
```

### 3️⃣ 데이터베이스 초기화

```sql
CREATE DATABASE uni_db;
```

서버 시작 시 테이블이 자동으로 생성됩니다.

### 4️⃣ 서버 실행

```bash
python -m uvicorn app.main:app --reload
```

- API 서버: http://localhost:8000
- **Swagger UI** (API 문서): http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API 엔드포인트

### 인증 (`/api/auth`)

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| `POST` | `/register` | 회원가입 (이메일/비밀번호) | ❌ |
| `POST` | `/login` | 로그인 (이메일/비밀번호) | ❌ |
| `GET` | `/kakao` | 카카오 OAuth 로그인 | ❌ |
| `GET` | `/kakao/callback` | 카카오 콜백 처리 | ❌ |
| `GET` | `/google` | 구글 OAuth 로그인 | ❌ |
| `GET` | `/google/callback` | 구글 콜백 처리 | ❌ |
| `GET` | `/me` | 현재 사용자 정보 | ✅ |

### 게시글 (`/api/posts`)

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| `GET` | `/` | 게시글 목록 (검색, 페이지네이션) | ❌ |
| `POST` | `/` | 게시글 작성 | ✅ |
| `GET` | `/{id}` | 게시글 상세 | ❌ |
| `PATCH` | `/{id}` | 게시글 수정 | ✅ |
| `DELETE` | `/{id}` | 게시글 삭제 | ✅ |
| `POST` | `/{id}/like` | 게시글 좋아요 토글 | ✅ |

### 댓글 (`/api/posts/{post_id}/comments`)

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| `GET` | `/` | 댓글 목록 | ❌ |
| `POST` | `/` | 댓글 작성 | ✅ |
| `DELETE` | `/{id}` | 댓글 삭제 | ✅ |
| `POST` | `/{id}/like` | 댓글 좋아요 토글 | ✅ |

### 익명우편소 (`/api/mail`)

| 메서드 | 경로 | 설명 | 인증 | 권한 |
|--------|------|------|------|------|
| `POST` | `/` | 고민 제출 | ❌ | - |
| `GET` | `/` | 제출 목록 조회 | ❌ | Admin Key 필요 |

---

## 프로젝트 구조

```
app/
├── models/
│   └── user.py              # User 모델 (id, email, password_hash, provider, social_id)
├── schemas/
│   ├── auth.py              # 인증 스키마 (LoginRequest, TokenResponse)
│   └── ...                  # 다른 도메인 스키마
├── routers/
│   ├── auth.py              # 인증 라우트 (로그인, OAuth, JWT)
│   ├── posts.py             # 게시글 라우트
│   ├── comments.py          # 댓글 라우트
│   └── mail.py              # 익명우편소 라우트
├── config.py                # 환경변수 로드 및 Settings
├── database.py              # SQLAlchemy 설정 및 DB 세션
├── dependencies.py          # 의존성 주입 (get_current_user 등)
├── main.py                  # FastAPI 앱 초기화 및 라우트 등록
└── requirements.txt         # 의존성 목록
```

---

## 주요 기능

### 🔐 소셜 로그인

**카카오 OAuth 플로우:**
1. 사용자가 "카카오로 로그인" 클릭
2. 백엔드가 카카오 인증 페이지로 리다이렉트
3. 사용자가 카카오에서 로그인 및 동의
4. 카카오가 인증 코드를 백엔드로 전달
5. 백엔드가 카카오 API에서 토큰 획득
6. 사용자 정보 조회 및 DB 저장/업데이트
7. JWT 토큰 발급 후 프론트엔드로 리다이렉트

**구글도 동일한 플로우를 따릅니다.**

### 👥 익명 커뮤니티

- **게시글**: 작성 시 랜덤 동물 닉네임 자동 부여
- **댓글**: 게시글 내에서 익명1~N 순서로 부여
- **좋아요**: 게시글/댓글 좋아요 토글 (로그인 필요)

### 🔑 JWT 인증

- 로그인 시 `access_token` 발급
- 요청 헤더에 `Authorization: Bearer <token>` 포함
- 토큰 만료 시 재로그인 필요 (유효기간: 7일)

### 📮 익명 우편소

- 비로그인 사용자도 고민 제출 가능
- 관리자 키로 제출 목록 조회 가능