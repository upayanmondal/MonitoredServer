import os
from fastapi import APIRouter, HTTPException, Depends

from database import SessionLocal
from models import User, File
from dependencies import get_current_user

router = APIRouter()

@router.delete("/delete/{file_id}")
def delete_the_file(file_id: int, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    db_file = db.query(File).filter(File.id == file_id).first()

    if not db_file:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "File doesn't exist"
        )

    if db_file.owner_id != db_user.id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "User is not authorized for this action on this file"
        )

    file_path = db_file.storage_path

    if not os.path.exists(file_path):
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "File not Found"
        )

    os.remove(file_path)

    db.delete(db_file)
    db.commit()

    db.close()

    return {
        "message": "file deleted successfully",
        "file_id": file_id
    }