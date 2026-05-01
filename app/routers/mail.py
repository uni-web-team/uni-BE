from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.mail import MailMessage
from app.schemas.mail import MailCreate, MailItemResponse, MailListResponse, MailResponse

router = APIRouter(prefix="/api/mail", tags=["mail"])


def fmt_date(dt) -> str:
    return dt.strftime("%Y.%m.%d %H:%M")


@router.post("", response_model=MailResponse, status_code=201)
def submit_mail(body: MailCreate, db: Session = Depends(get_db)):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="고민을 입력해주세요")
    msg = MailMessage(content=body.content.strip())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MailResponse(id=msg.id)


@router.get("", response_model=MailListResponse)
def list_mails(
    x_admin_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if x_admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="관리자 키가 올바르지 않아요")
    mails = db.query(MailMessage).order_by(MailMessage.created_at.desc()).all()
    return MailListResponse(
        mails=[MailItemResponse(id=m.id, content=m.content, date=fmt_date(m.created_at)) for m in mails],
        total=len(mails),
    )
