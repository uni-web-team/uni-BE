import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.comment import Comment, CommentLike, PostCommentAuthor
from app.models.post import Post, PostLike
from app.models.user import User
from app.schemas.post import (
    CommentCreate,
    CommentResponse,
    LikeResponse,
    PostCreate,
    PostListResponse,
    PostResponse,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])

ANIMAL_NICKS = [
    "하늘다람쥐", "초록거북이", "분홍고양이", "노란강아지",
    "보라고슴도치", "파란펭귄", "빨간여우", "흰토끼",
    "금빛나비", "은빛물고기", "솜사탕곰", "달빛올빼미",
    "꽃잎개구리", "무지개햄스터", "새벽별고양이",
]


def fmt_date(dt: datetime) -> str:
    return dt.strftime("%Y.%m.%d %H:%M")


def build_comment_response(c: Comment, user: User | None, db: Session) -> CommentResponse:
    liked = False
    if user:
        liked = db.query(CommentLike).filter_by(comment_id=c.id, user_id=user.id).first() is not None
    return CommentResponse(
        id=c.id,
        text=c.text,
        nick=f"익명{c.anon_number}",
        date=fmt_date(c.created_at),
        likes=c.likes_count,
        liked=liked,
    )


def build_post_response(post: Post, user: User | None, db: Session) -> PostResponse:
    liked = False
    if user:
        liked = db.query(PostLike).filter_by(post_id=post.id, user_id=user.id).first() is not None
    comments = [build_comment_response(c, user, db) for c in post.comments]
    return PostResponse(
        id=post.id,
        title=post.title,
        author=post.author_nick,
        date=fmt_date(post.created_at),
        body=post.body,
        likes=post.likes_count,
        liked=liked,
        comments=comments,
    )


@router.get("", response_model=PostListResponse)
def list_posts(
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=8, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    query = db.query(Post)
    if search:
        query = query.filter(Post.title.contains(search) | Post.body.contains(search))
    total = query.count()
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, -(-total // per_page))  # ceil division
    return PostListResponse(
        posts=[build_post_response(p, user, db) for p in posts],
        total=total,
        page=page,
        total_pages=total_pages,
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력해주세요")
    if not body.body.strip():
        raise HTTPException(status_code=400, detail="내용을 입력해주세요")
    post = Post(
        title=body.title.strip(),
        body=body.body.strip(),
        author_id=user.id,
        author_nick=random.choice(ANIMAL_NICKS),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return build_post_response(post, user, db)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없어요")
    return build_post_response(post, user, db)


@router.post("/{post_id}/like", response_model=LikeResponse)
def toggle_post_like(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없어요")

    existing = db.query(PostLike).filter_by(post_id=post_id, user_id=user.id).first()
    if existing:
        db.delete(existing)
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=user.id))
        post.likes_count += 1
        liked = True

    db.commit()
    return LikeResponse(liked=liked, likes=post.likes_count)


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없어요")
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="댓글을 입력해주세요")

    # 익명 번호 부여: 기존 매핑 조회 or 새로 할당
    mapping = db.query(PostCommentAuthor).filter_by(post_id=post_id, user_id=user.id).first()
    if mapping is None:
        max_num = db.query(func.max(PostCommentAuthor.anon_number)).filter_by(post_id=post_id).scalar() or 0
        mapping = PostCommentAuthor(post_id=post_id, user_id=user.id, anon_number=max_num + 1)
        db.add(mapping)
        db.flush()

    comment = Comment(
        post_id=post_id,
        author_id=user.id,
        text=body.text.strip(),
        anon_number=mapping.anon_number,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return build_comment_response(comment, user, db)


@router.post("/{post_id}/comments/{comment_id}/like", response_model=LikeResponse)
def toggle_comment_like(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없어요")

    existing = db.query(CommentLike).filter_by(comment_id=comment_id, user_id=user.id).first()
    if existing:
        db.delete(existing)
        comment.likes_count = max(0, comment.likes_count - 1)
        liked = False
    else:
        db.add(CommentLike(comment_id=comment_id, user_id=user.id))
        comment.likes_count += 1
        liked = True

    db.commit()
    return LikeResponse(liked=liked, likes=comment.likes_count)
