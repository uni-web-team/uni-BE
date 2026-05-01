from pydantic import BaseModel


class MailCreate(BaseModel):
    content: str


class MailResponse(BaseModel):
    id: int
    message: str = "고민이 접수되었어요! 곧 따뜻한 답장이 올 거예요 📮"


class MailItemResponse(BaseModel):
    id: int
    content: str
    date: str

    model_config = {"from_attributes": True}


class MailListResponse(BaseModel):
    mails: list[MailItemResponse]
    total: int
