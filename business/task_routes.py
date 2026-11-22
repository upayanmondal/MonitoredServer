from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models import User, Group, Task, Project
from database import SessionLocal
from dependencies import get_current_user

router = APIRouter()

ALLOWED_STATUSES = ["created", "assigned", "in_progress", "on_hold", "completed", "cancelled"]
ALLOWED_PRIORITIES = ["critical", "high", "medium", "low"]

class CreateTask(BaseModel):
    project_id: int
    title: str
    description: str

class AssignTask(BaseModel):
    dev_id: int

class AssignPriority(BaseModel):
    priority: str

class AssignStatus(BaseModel):
    status: str

@router.post("/groups/{group_id}/tasks")
def create_task(group_id: int, request: CreateTask, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    if db_user.role != "tech lead":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    db_group = db.query(Group).filter(Group.id == group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group doesn't exist"
        )

    if db_user.group_id != db_group.id:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The tech lead doesn't beling to this group"
        )
    
    project_Id = request.project_id

    db_project = db.query(Project).filter(Project.id == project_Id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Project doesn't exist"
        )

    if db_project.status != "active":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Can't create a task for a project which is not active" 
        )
    
    if db_project.group_id != group_id:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = f"The project doesn't belong to group id {group_id}"
        )

    db_task = Task(
        project_id = request.project_id,
        created_by = db_user.id,
        title = request.title,
        description = request.description
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    db.close()

    return {
        "message": "Task is created",
        "Creator": user["sub"]
    }

@router.post("/tasks/{task_id}/assign")
def assign_task(task_id: int, request: AssignTask, user = Depends(get_current_user)):

    assigned_roles = ["developer", "tech lead"]
    
    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "user doesn't exist"
        )
    
    if db_user.role != "tech lead":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    db_task = db.query(Task).filter(Task.id == task_id).first()

    if not db_task:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Task doesn't exist"
        )
    if db_task.priority is None or db_task.priority not in ALLOWED_PRIORITIES:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Task without priority can't be assigned"
        )

    prohibited = ["assigned", "in_progress", "completed", "cancelled"]
    if db_task.status in prohibited:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "This task can't be assigned"
        )

    db_project = db.query(Project).filter(Project.id == db_task.project_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Project associated with this Task not found"
        )

    if db_project.status != "active":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Project associated with this Task is no more active"
        )

    db_group = db.query(Group).filter(Group.id == db_project.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The group associated with the project not found"
        )

    if db_user.group_id != db_group.id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    db_dev = db.query(User).filter(User.id == request.dev_id).first()

    if not db_dev:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The developer not found"
        )
    
    if db_dev.group_id != db_group.id:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The developer doesn't belong to the proper group"
        )
    if db_dev.role not in assigned_roles:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The assigned person is not a developer"
        )

    if db_dev.role == "tech lead" and db_dev.id != db_user.id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "One tech lead can't assign to a task to another tech lead"
        )

    db_dev_total_task = db.query(Task).filter(Task.assigned_to == db_dev.id, Task.status.in_(["assigned", "in_progress", "on_hold"])).all()

    if db_dev.role == "developer" and len(db_dev_total_task) >= 5:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The developer already has the maximum number of task"
        )

    if db_dev.role == "tech lead" and len(db_dev_total_task) >= 2:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The developer already has the maximum number of task"
        )
    
    if db_dev.role == "developer" and (db_task.priority == "high" or db_task.priority == "critical"):
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Priority doesn't match"
        )

    if db_dev.role == "tech lead" and (db_task.priority == "low" or db_task.priority == "medium"):
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Priority doesn't match"
        )
    

    db_task.assigned_to = request.dev_id
    db_task.status = "assigned"

    dev_name = db_dev.username

    db.commit()
    db.refresh(db_task)
    db.close()

    return {
        "message": f"{task_id} is assigned to {dev_name} by {user['sub']}"
    }

@router.get("/groups/{group_id}/tasks")
def get_tasks(group_id: int, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )
    
    if db_user.role not in ["manager", "tech lead"]:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    db_group = db.query(Group).filter(Group.id == group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Group not found"
        )

    if db_user.group_id != group_id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "User doesn't belong to this group"
        )

    db_project = db.query(Project).filter(Project.group_id == group_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Project not found or Group is not associated with any project"
        )

    db_tasks = db.query(Task).filter(Task.project_id == db_project.id).all()
    db.close()

    return {
        "Tasks": db_tasks
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: int, user = Depends(get_current_user)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    db_task = db.query(Task).filter(Task.id == task_id).first()

    if not db_task:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Task doesn't exist"
        )

    if db_user.role == "developer" and db_user.id != db_task.assigned_to:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "The developer doesn't have the authorization to asscess the task"
        )

    db_project = db.query(Project).filter(Project.id == db_task.project_id).first()
    
    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "The task doesn't belong to any project"
        )
    
    db_group = db.query(Group).filter(Group.id == db_project.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group not found"
        )


    if db_user.role == "tech lead" and  db_user.group_id != db_project.group_id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = f"Tech Lead {db_user.username} is not authorized"
        )

    if db_user.role == "manager" and  db_user.group_id != db_project.group_id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = f"Manager {db_user.username} is not authorized"
        )

    if db_user.role not in ["tech lead", "admin", "developer", "manager"]:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized"
        )

    person_name = db_user.username
    person_role = db_user.role
    person_id = db_user.id

    db.close()

    return{
        "Task": db_task,
        "message": f"The Task is requested by {person_role} {person_name}, Id: {person_id}"
    }

@router.patch("/tasks/{task_id}/priority")
def reassign_task_priority(task_id: int, request: AssignPriority, user = Depends(get_current_user)):
    db = SessionLocal()

    db_task = db.query(Task).filter(Task.id == task_id).first()

    if not db_task:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Task doesn't exist"
        )

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )
    
    if db_user.role != "tech lead":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    if db_user.group_id is None:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "tech lead is not associated with any group"
        )

    db_group = db.query(Group).filter(Group.id == db_user.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group doesn't exist"
        )
    
    db_project = db.query(Project).filter(Project.id == db_task.project_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Project not found"
        )

    if db_project.status != "active":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "project is not active"
        )
    
    if db_project.group_id != db_group.id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Project's group and tech lead's group don't match"
        )
    
    if request.priority not in ALLOWED_PRIORITIES:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Priority is not allowed"
        )

    if db_task.assigned_to is not None:
        db_assignee = db.query(User).filter(User.id == db_task.assigned_to).first()

        if not db_assignee:
            db.close()
            raise HTTPException(
                status_code = 400,
                detail = "Assigned user not found"
            )

        if db_assignee.role == "developer" and request.priority in ["critical", "high"]:
            db.close()
            raise HTTPException(
                status_code = 400,
                detail = "Developers can only have medium and low priority taska"
            )

        if db_assignee.role == "tech lead" and request.priority in ["medium", "low"]:
            db.close()
            raise HTTPException(
                status_code = 400,
                detail = "Tech leads can only have critical and high priority tasks"
            )
        

    db_task.priority = request.priority
    lead = db_user.username

    db.commit()
    db.refresh(db_task)
    db.close()

    return {
        "message": f"Task {task_id} priority updated to {request.priority}",
        "Tech Lead": lead,
    }

@router.patch("/tasks/{task_id}/status")
def reassign_task_status(task_id: int, request: AssignStatus, user = Depends(get_current_user)):
    
    db = SessionLocal()

    db_task = db.query(Task).filter(Task.id == task_id).first()

    if not db_task:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Task doesn't exist"
        )
    
    if request.status not in ALLOWED_STATUSES:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Status is not allowed"
        )
    
    if db_task.status == request.status:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The Status is same as the current status"
        )

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    if db_user.role != "tech lead":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "User not authorized to perform the action"
        )

    if db_user.group_id is None:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to perform this action"
        )

    db_project = db.query(Project).filter(Project.id == db_task.project_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Project doesn't exist"
        )

    if db_project.status != "active":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "the project is not active"
        )
    
    if db_project.group_id != db_user.group_id:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Unauthorized to perform this action"
        )
    
    db_group = db.query(Group).filter(Group.id == db_project.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group not found"
        )

    db_task.status = request.status
    tech_lead = db_user.username

    db.commit()
    db.refresh(db_task)
    db.close()

    return {
        "message": f"Task {task_id} status is updated to {request.status}",
        "Tech Lead": tech_lead
    }

@router.get("/users/me/tasks")
def get_my_tasks(user = Depends(get_current_user)):
    
    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 401,
            detail = "User not found"
        )

    if db_user.role not in ["developer", "tech lead"]:
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized"
        )

    if db_user.group_id is None:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "The user doesn't belong to any group"
        )
    
    db_project = db.query(Project).filter(Project.group_id == db_user.group_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "project isn't associated with the user's group or project doesn't exist"
        )

    db_tasks = db.query(Task).filter(Task.assigned_to == db_user.id).all()

    if not db_tasks:
        db.close()
        raise HTTPException(
            status_code = 200,
            detail = []
        )
    
    username = db_user.username
    db.close()

    return {
        "message": f"All Tasks assigned to {username}",
        "Tasks": db_tasks
    }