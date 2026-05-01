# UNI 백엔드

비장애 형제 커뮤니티 **UNI**의 REST API 서버입니다.

---

## 기술 스택

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Auth**: JWT (python-jose)
- **Migration**: Alembic

---

## 시작하기

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 아래 내용을 입력합니다.

```env
DATABASE_URL=postgresql://유저명:비밀번호@localhost:5432/uni_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ADMIN_KEY=your-admin-key
```

### 3. 데이터베이스 생성

```sql
CREATE DATABASE uni_db;
```

### 4. 서버 실행

```bash
python -m uvicorn app.main:app --reload
```

서버 시작 시 테이블이 자동으로 생성됩니다.

API 문서: `http://localhost:8000/docs`

---

## API 엔드포인트

### 인증
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| GET | `/api/auth/me` | 내 정보 조회 |

### 커뮤니티
| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/api/posts` | ❌ | 게시글 목록 (검색, 페이지네이션) |
| POST | `/api/posts` | ✅ | 게시글 작성 |
| GET | `/api/posts/{id}` | ❌ | 게시글 상세 |
| POST | `/api/posts/{id}/like` | ✅ | 게시글 좋아요 토글 |
| POST | `/api/posts/{id}/comments` | ✅ | 댓글 작성 |
| POST | `/api/posts/{id}/comments/{cid}/like` | ✅ | 댓글 좋아요 토글 |

### 익명우편소
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/mail` | 고민 제출 |
| GET | `/api/mail` | 제출 목록 조회 (관리자 전용, `X-Admin-Key` 헤더 필요) |

---

## 주요 기능

- **익명 서비스**: 게시글 작성 시 랜덤 동물 닉네임 자동 부여, 댓글은 게시글 내에서 익명1~N 순서로 부여
- **좋아요**: 게시글·댓글 좋아요 토글 (로그인 필요)
- **익명우편소**: 비로그인 사용자도 고민 제출 가능, 관리자 키로 목록 조회
