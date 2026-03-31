from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.core.auth_cookie import set_auth_cookie

router = APIRouter()

@router.post("/login")
def login(response: Response, username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == username).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    # ✅ FIX: sätt cookie korrekt
    set_auth_cookie(response, token)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
