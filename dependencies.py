from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth import verify_access_token
from models import RevokedToken, User
from database import SessionLocal

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials

    payload = verify_access_token(token)

    if payload == False:
        raise HTTPException(
            status_code = 401,
            detail = "Invalid or Expired token"
        )

    db = SessionLocal()

    is_db_token_revoked = db.query(RevokedToken).filter(RevokedToken.token == token).first()

    db.close()

    if is_db_token_revoked:
        raise HTTPException(
            status_code = 401,
            detail = "Token Revoked"
        )

    return payload

def is_admin(user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    if db_user.role != "admin":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not authorized to perform this action"
        )

    db.close()

    return user