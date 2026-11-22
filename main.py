import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File as FastAPIFile, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import jwt
from sqlalchemy import inspect
import json

from database import Base, engine, SessionLocal
from models import User, File, ActivityLog
from auth import create_Access_token, verify_access_token
from dependencies import get_current_user

from download import router as download_router
from list_files import router as files_router
from detele_file import router as delete_router
from account import router as account_router
from admin.admin_routes import router as admin_router_to_access_all_users
from business.business_routes import router as business_router
from business.task_routes import router as task_router

app = FastAPI(title = "Monitored Business Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_methods = ["*"],
    allow_headers = ["*"]
)

Base.metadata.create_all(bind = engine)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx"}

class SignupRequest(BaseModel):
    username: str
    password: str
    experience: int
    
class LoginRequest(BaseModel):
    username: str
    password: str

class ProfileUpdateRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    experience: int | None = Field(default = None, ge = 0)

@app.post("/signup")
def signup(user: SignupRequest, request: Request):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.username == user.username).first()
    Source_IP = request.client.host if request.client else None

    if existing_user:
        db_activity_log = ActivityLog(
            actor_id = None,
            actor_username = user.username,
            action = "signup",
            target_type = "user",
            target_id = None,
            description = "Signup Failed: username already exists",
            outcome = "failure",
            severity = "low",
            source_ip = Source_IP,
            before_data = None,
            after_data = None,
            correlation_id = None
        )

        try:
            db.add(db_activity_log)
            db.commit()
        except Exception:
            db.rollback()

        finally:
            db.close()
        
        raise HTTPException(
            status_code = 409,
            detail = "Username Already Exists"
        )

    db_user = User(
        username = user.username,
        password = user.password,
        experience = user.experience
    )

    try:
        db.add(db_user)
        db.flush()

        After_Data = {
            "id": db_user.id,
            "username": db_user.username,
            "experience": db_user.experience
        }

        db_activity_log = ActivityLog(
            actor_id = db_user.id,
            actor_username = user.username,
            action = "signup",
            target_type = "user",
            target_id = db_user.id,
            description = "New user registration",
            outcome = "success",
            severity = "low",
            source_ip = Source_IP,
            before_data = None,
            after_data = json.dumps(After_Data),
            correlation_id = None
        )

        db.add(db_activity_log)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


    return {
        "message": "user registered successfully",
        "username": user.username
    }

@app.post("/login")
def login(user: LoginRequest, request: Request):

    db = SessionLocal()

    Source_IP = request.client.host if request.client else None

    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user:

        db_activity_log = ActivityLog(
            actor_id = None,
            actor_username = user.username,
            action = "login",
            target_type = "user",
            target_id = None,
            description = "Login Failed: username doesn't exists",
            outcome = "failure",
            severity = "low",
            source_ip = Source_IP,
            before_data = None,
            after_data = None,
            correlation_id = None
        )

        try:
            db.add(db_activity_log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        raise HTTPException(
            status_code = 401,
            detail = "user doesn't exists"
        )
    
    if db_user.password != user.password:

        db_activity_log = ActivityLog(
            actor_id = db_user.id,
            actor_username = user.username,
            action = "login",
            target_type = "user",
            target_id = db_user.id,
            description = "Login Failed: incorrect password",
            outcome = "failure",
            severity = "low",
            source_ip = Source_IP,
            before_data = None,
            after_data = None,
            correlation_id = None
        )

        try:
            db.add(db_activity_log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        raise HTTPException(
            status_code = 401,
            detail = "Invalid password"
        )

    token = create_Access_token(db_user.username)
    After_Data = {
        "id": db_user.id,
        "username": db_user.username,
        "experience": db_user.experience
    }

    db_activity_log = ActivityLog(
            actor_id = db_user.id,
            actor_username = user.username,
            action = "login",
            target_type = "user",
            target_id = db_user.id,
            description = "User Logged in successfully",
            outcome = "success",
            severity = "low",
            source_ip = Source_IP,
            before_data = None,
            after_data = json.dumps(After_Data),
            correlation_id = None
        )
    
    try:
        db.add(db_activity_log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return {
        "message": "Login Successfull",
        "username": user.username,
        "access_token": token
        }

@app.get("/")
def home():
    return {"message": "Business server is running"}


@app.get("/profile")
def profile(user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()

        raise HTTPException(
            status_code = 401,
            detail = "User not Found"
        )

    profile_data = {
        "id": db_user.id,
        "username": db_user.username
    }

    db.close()

    return profile_data

@app.put("/profile")
def update_profile(data: ProfileUpdateRequest, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()

        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    token = None

    if data.username != None:
        db_user.username = data.username
        token = create_Access_token(db_user.username)

    if data.password != None:
        db_user.password = data.password

    if data.experience != None:
        db_user.experience = data.experience
    
    uname = db_user.username
    db.commit()
    db.refresh(db_user)
    db.close()

    return {
        "message": "profile updated successfully",
        "username": uname,
        "access_token": token
    }


@app.post("/upload")
def upload_file(uploaded_file: UploadFile, user = Depends(get_current_user)):

    if not uploaded_file.filename:
        raise HTTPException(
            status_code = 400,
            detail = "Filename is Missing"
        )

    original_filename = uploaded_file.filename

    time_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    name, extension = os.path.splitext(original_filename)


    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code = 400,
            detail = "file type is not allowed"
        )

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User Not Found or Session expired"
        )

    stored_filename = f"{name}_{time_stamp}{extension}"
    
    storage_path = os.path.join("uploads", stored_filename)

    file_data = uploaded_file.file.read()
    file_size = len(file_data)

    with open(storage_path, "wb") as file:
        file.write(file_data)
        
    
    db_file = File(
        filename = stored_filename,
        file_type = extension,
        file_size = file_size,
        owner_id = db_user.id,
        storage_path = storage_path,
        original_filename = original_filename
    )

    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    db.close()

    return {
        "message": "File uploaded successfully",
        "filename": stored_filename,
        "file_type": extension,
        "file_size": file_size
    }

app.include_router(download_router)
app.include_router(files_router)
app.include_router(delete_router)
app.include_router(account_router)
app.include_router(admin_router_to_access_all_users)
app.include_router(business_router)
app.include_router(task_router)
