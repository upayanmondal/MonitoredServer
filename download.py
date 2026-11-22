import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import mimetypes

from database import SessionLocal
from models import User, File
from dependencies import get_current_user


router = APIRouter()

@router.get("/download/{file_id}")
def download_file(file_id: int, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not Found"
        )

    db_file = db.query(File).filter(File.id == file_id).first()
    
    if not db_file:
        db.close()
        raise HTTPException(
            status_code = 404, # Resource not found
            detail = "File not found"
        )

    if db_file.owner_id != db_user.id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not authorized to download this file"
        )

    if not os.path.exists(db_file.storage_path):
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Physical File not found"
        )

    file_path = db_file.storage_path
    original_filename = db_file.original_filename

    media_type = mimetypes.guess_type(original_filename)[0]

    if media_type == None:
        media_type = "application/octet-stream"
        

    db.close()
    
    return FileResponse(
        path = file_path,
        filename = original_filename,
        media_type = media_type
    )