from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import SessionLocal
from models import User, File, RevokedToken
from dependencies import get_current_user

router = APIRouter()
security = HTTPBearer()

@router.get("/account")
def Account(user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    account_data = {
        "username": db_user.username,
        "role": db_user.role,
        "experience": db_user.experience,
        "account_status": db_user.account_status,
        "group_id": db_user.group_id
    }

    db.close()

    return account_data

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    
    token = credentials.credentials

    db = SessionLocal()

    existing_token = db.query(RevokedToken).filter(RevokedToken.token == token).first()

    if existing_token:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "Token already revoked"
        )

    revoked_token = RevokedToken(token = token)

    db.add(revoked_token)
    db.commit()

    db.close()

    return {
        "message": "Logged out successfully"
    }