from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.deps import get_db
from database.models import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
def register_user(user: dict, db: Session = Depends(get_db)):
    trader = User(
        name=user["name"],
        whatsapp_number=user["whatsapp_number"],
        email=user.get("email", None),
        clerk_id=user.get("clerk_id", None)
    )

    db.add(trader)
    db.commit()
    db.refresh(trader)

    return {"status": "registered", "user_id": trader.id}
