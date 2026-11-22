from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from models import User, Project, Group, Task
from database import SessionLocal
from dependencies import get_current_user, is_admin

router = APIRouter()
VALID_PROJECT_STATUS = ["active", "completed", "archived", "restored"]

class ProjectCreation(BaseModel):
    name: str
    description: str

class UpdateProject(BaseModel):
    name: str | None = None
    description: str | None = None

@router.post("/projects")
def create_project(project_request: ProjectCreation, user = Depends(is_admin)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    db_project = db.query(Project).filter(Project.name == project_request.name).first()

    if db_project:
        db.close()
        raise HTTPException(
            status_code = 409,
            detail = f"{db_project.name} Project is already created"
        )

    add_project = Project(
        name = project_request.name,
        description = project_request.description,
        owner_id = db_user.id
    )

    owner = db_user.username
    project_name = add_project.name

    db.add(add_project)

    db.commit()
    db.refresh(add_project)
    db.close()


    return {
        "message": f"{project_name} is created by {owner}"
    }

@router.get("/projects")
def get_projects(user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    db_projects = db.query(Project).filter(Project.owner_id == db_user.id).all()
    
    db.close()

    return db_projects

@router.get("/projects/my-project")
def get_my_project(user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "User not found"
        )
    
    if db_user.group_id is None:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "user doesn't belong to any group"
        )

    db_group = db.query(Group).filter(Group.id == db_user.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The group doesn't exist"
        )

    db_project = db.query(Project).filter(Project.group_id == db_group.id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = f"No project is assigned to {db_group.id}"
        )

    project_details = {
        "project_id": db_project.id,
        "project_name": db_project.name,
        "project_description": db_project.description,
        "project_owner": db_project.owner_id,
        "project_status": db_project.status,
        "Assigned_group": db_project.group_id
    }

    db.close()

    return {
        "message": project_details
    }

@router.get("/projects/{project_id}")
def get_project(project_id: int, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    db_project = db.query(Project).filter(Project.id == project_id).first()
        
    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Project doesn't exist"
        )

    if db_user.role == "admin":
        
        the_project = db_project
        db.close()
        return the_project

    elif db_user.id != db_project.owner_id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    the_project = db_project

    db.close()

    return the_project

@router.get("/groups/developers")
def get_devs(user = Depends(get_current_user)):
    
    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "user not found"
        )

    if db_user.role == "admin" or db_user.role == "developer":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Unauthorized"
        )

    if db_user.group_id is None:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "User doesn't belong to any group"
        )

    db_group = db.query(Group).filter(Group.id == db_user.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group doesn't exist"
        )


    if db_user.role == "manager" or db_user.role == "tech lead":
        db_devs = db.query(User).filter(User.role.in_(["developer", "tech lead"]), User.group_id == db_group.id, User.account_status == "active").all()
        developers = [{"id": dev.id, "username": dev.username, "role": dev.role} for dev in db_devs]
        db.close()

        return{
            "message": "The developers are following",
            "Developers": developers
        }

@router.put("/projects/{project_id}")
def update_project(project_id: int, request: UpdateProject, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    elif not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Project doesn't exist"
        )
    
    if db_project.status == "archived" or db_project.status == "restored":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "this project can't be edited"
        )

    elif db_user.role == "admin" or db_project.owner_id == db_user.id:
        if request.name is not None:
            db_project.name = request.name

        if request.description is not None:
            db_project.description = request.description

        db_project.updated_at = datetime.utcnow()

        now_project = db_project
        db.commit()
        db.refresh(db_project)
        db.close()

        return {
            "message": "Project updated successfully",
            "Project": now_project
        }

    else:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )


@router.patch("/projects/{project_id}/archive")
def archive_project(project_id: int, user = Depends(is_admin)):

    db = SessionLocal()

    db_project = db.query(Project).filter(Project.id == project_id).first() # .first() trigger the execution

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "The Project doesn't exist"
        )
    project_name = db_project.name
    
    if db_project.status not in ["completed", "restored"]:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Project can't be archived"
        )


    db_project.status = "archived"
    db_project.group_id = None
    
    db.commit()
    db.refresh(db_project)
    db.close()

    return {
        "message": f"Project {project_name} Id: {project_id} is archived",
        "Done By": user['sub']
    }

@router.patch("/projects/{project_id}/restore")
def restore_project(project_id: int, user = Depends(is_admin)):

    db = SessionLocal()

    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The project doesn't exist"
        )

    if db_project.status != "archived":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The Project isn't archived"
        )

    project_name = db_project.name

    db_project.status = "restored"
    db.commit()
    db.refresh(db_project)
    db.close()

    return {
        "message": f"Project {project_name} Id: {project_id} is restored",
        "Done By": user['sub']
    }
