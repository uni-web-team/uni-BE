from pydantic import BaseModel


class CommentResponse(BaseModel):
    id: int
    text: str
    nick: str
    date: str
    likes: int
    liked: bool = False

    model_config = {"from_attributes": True}


class PostResponse(BaseModel):
    id: int
    title: str
    author: str
    date: str
    body: str
    likes: int
    liked: bool = False
    comments: list[CommentResponse] = []

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    posts: list[PostResponse]
    total: int
    page: int
    total_pages: int


class PostCreate(BaseModel):
    title: str
    body: str


class CommentCreate(BaseModel):
    text: str


class LikeResponse(BaseModel):
    liked: bool
    likes: int
