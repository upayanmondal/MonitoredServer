from fastapi import APIRouter, Depends, HTTPException

from database import SessionLocal
from models import User, File
from dependencies import get_current_user

router = APIRouter()


@router.get("/files")
def get_files(user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    db_files = db.query(File).filter(File.owner_id == db_user.id).all()

    if not db_files:
        db.close()
        raise HTTPException(
            status_code = 404, # Resource not found
            detail = f"No Files available for {user['sub']}"
        )

    files = []

    for db_file in db_files:
        files.append({
            "id": db_file.id,
            "filename": db_file.original_filename,
            "original_filename": db_file.original_filename,
            "file_type": db_file.file_type,
            "file_size": db_file.file_size
        })

    db.close()

    return {
        "files": files
    }