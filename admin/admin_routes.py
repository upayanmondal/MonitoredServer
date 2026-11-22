from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from dependencies import get_current_user, is_admin
from database import SessionLocal
from models import User, Group, Project, Task

router = APIRouter()

ALLOWED_ACCOUNT_STATUS = {"active", "deactivated", "suspended"}

class AccountStatusUpdate(BaseModel):
    account_status: str

class GroupCreation(BaseModel):
    name: str
    description: str
    manager_id: int

class LeadAssign(BaseModel):
    tech_lead_id: int

class CreateDeveloper(BaseModel):
    dev_id: int

class AssignProject(BaseModel):
    group_id: int

@router.get("/admin/users")
def get_all_users(user = Depends(is_admin)):

    db = SessionLocal()

    db_users = db.query(User).all()

    db.close()

    return db_users


@router.put("/admin/{user_id}/status")
def update_status(user_id: int, request: AccountStatusUpdate, user = Depends(is_admin)):

    if (request.account_status).lower() not in ALLOWED_ACCOUNT_STATUS:
        raise HTTPException(
            status_code = 400, # Bad request
            detail = "This status is not allowed"
        )

    db = SessionLocal()

    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = f"There is no user who has id {user_id}"
        )
    
    
    db_user.account_status = (request.account_status).lower()

    db.commit()
    db.refresh(db_user)
    db.close()

    return {
        "message": "Account status updated successfully"
    }

@router.post("/admin/groups")
def create_groups(request: GroupCreation, user = Depends(is_admin)):

    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    db_manager = db.query(User).filter(User.id == request.manager_id).first()

    if not db_manager:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Manager not found"
        )

    if db_manager.role != "manager":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = f"{db_manager.username} is not a manager"
        )

    if db_manager.group_id is not None:
        db.close()
        raise HTTPException(
            status_code = 409,
            detail = f"{db_manager.username} is already assigned with a group"
        )

    db_group = db.query(Group).filter(Group.name == request.name).first()

    if db_group:
        db.close()
        raise HTTPException(
            status_code = 409,
            detail = f"{db_group.name} already exists"
        )

    db_new_group = Group(
        name = request.name,
        description = request.description,
        owner_id = db_user.id,
        manager_id = db_manager.id
    )

    db.add(db_new_group)
    db.commit()
    db.refresh(db_new_group)

    db_manager.group_id = db_new_group.id
    db.commit()
    db.refresh(db_manager)

    db.close()

    return {
        "message": "The group is created successfully",
        "Owner": f"{user['sub']}"
    }

@router.get("/admin/groups")
def get_all_groups(user = Depends(is_admin)):

    db = SessionLocal()

    db_groups = db.query(Group).all()

    if not db_groups:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail= "No group is created"
        )

    db.close()

    return db_groups

@router.get("/admin/projects")
def get_all_groups(user = Depends(is_admin)):

    db = SessionLocal()

    db_projects = db.query(Project).all()

    if not db_projects:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail= "No project is created"
        )

    db.close()

    return db_projects

@router.post("/admin/groups/{group_id}/tech-leads")
def create_techLeads(group_id: int, request: LeadAssign, user = Depends(is_admin)):
    
    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["sub"]).first()

    db_group = db.query(Group).filter(Group.id == group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group doesn't exist"
        )

    db_tech_lead = db.query(User).filter(User.id == request.tech_lead_id).first()

    if not db_tech_lead:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Tech Lead not found"
        )
    if db_tech_lead.role != "tech lead":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = f"{db_tech_lead.username} is not a tech lead"
        )

    if db_tech_lead.group_id is not None:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The Tech Lead is already assigned to a group"
        )

    db_tech_lead.group_id = group_id

    lead_name = db_tech_lead.username
    admin_name = db_user.username
    group_name = db_group.name

    db.commit()
    db.refresh(db_tech_lead)
    db.close()

    return {
        "message": f"{lead_name} is assigned to {group_name} group",
        "Admin": f"{admin_name}"
    }

@router.post("/admin/groups/{group_id}/developers")
def create_devs(group_id: int, request: CreateDeveloper, user = Depends(is_admin)):
    
    db = SessionLocal()

    db_admin = db.query(User).filter(User.username == user["sub"]).first()

    db_dev = db.query(User).filter(User.id == request.dev_id).first()

    if not db_dev:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Developer doesn't exist"
        )
    
    if db_dev.group_id is not None:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "Developer is already assigned to a group"
        )

    if db_dev.role != "developer":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "User is not a developer"
        )

    db_group = db.query(Group).filter(Group.id == group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group not found"
        )

    db_dev.group_id = group_id

    dev_name = db_dev.username
    admin_name = db_admin.username
    group_name = db_group.name

    db.commit()
    db.refresh(db_dev)
    db.close()

    return {
        "message": f"{dev_name} is assigned to {group_name}",
        "Admin": f"{admin_name}"
    }

@router.patch("/admin/projects/{project_id}/group")
def assign_project(project_id: int, request: AssignProject, user = Depends(is_admin)):
    
    db = SessionLocal()

    db_group = db.query(Group).filter(Group.id == request.group_id).first()

    if not db_group:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Group doesn't exist"
        )
    
    project_to_the_target_group = db.query(Project).filter(Project.group_id == db_group.id).first()

    if project_to_the_target_group:
        if project_to_the_target_group.status in ["active", "completed"]:
            db.close()
            raise HTTPException(
                status_code = 400,
                detail = "The Group has an ongoing project"
            )

    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        db.close()
        raise HTTPException(
            status_code = 404,
            detail = "Project not found"
        )

    if db_project.group_id is not None:
        db.close()
        raise HTTPException(
            status_code = 409,
            detail = f"{db_project.name} is already assigned to a group"
        )

    if db_project.status != "active":
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "The project is no longer active"
        )

    db_project.group_id = request.group_id
    project_name = db_project.name
    

    try:
        db.commit()
        db.refresh(db_project)

    except IntegrityError:
        db.rollback()
        db.close()

        raise HTTPException(
            status_code = 409,
            detail = "This group already assigned to a another project"
        )

    db.close()

    return {
        "message": f"{project_name} is assigned to group id {request.group_id}",
        "Admin": f"{user['sub']}"
    }

@router.delete("/admin/delete/user/{user_id}")
def delete_user(user_id: int, user = Depends(is_admin)):
    
    db = SessionLocal()

    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        db.close()
        raise HTTPException(
            status_code = 400,
            detail = "User don't exist"
        )

    username = db_user.username

    if db_user.role == "admin":
        db.close()
        raise HTTPException(
            status_code = 403,
            detail = "Not Authorized to remove an admin"
        )

    if db_user.group_id is None:
        db.delete(db_user)
        db.commit()
        db.close()
        return {
            "message": f"{username} is removed from the company",
            "Removed By": f"Admin {user['sub']}"
        }

    if db_user.group_id is not None:
        db_group = db.query(Group).filter(Group.id == db_user.group_id).first()

        if not db_group:
            db.delete(db_user)
            db.commit()
            db.close()
            return {
                "message": f"{username} is removed from the company and the user's asscociated group doesn't exist , so checking is required",
                "Removed By": f"Admin {user['sub']}"
            }

        db_project = db.query(Project).filter(Project.group_id == db_group.id).first()

        if not db_project:

            if db_group.manager_id == db_user.id:
                db_group.manager_id = None

            db.delete(db_user)
            db.commit()
            db.close()
            return {
                "message": f"{username} is removed from the company and the user's asscociated group isn't assigned to any project",
                "Removed By": f"Admin {user['sub']}"
            }

        if db_project:
            if db_user.role == "developer":
                db_tasks = db.query(Task).filter(Task.assigned_to == db_user.id).all()

                if len(db_tasks) == 0:
                    db.delete(db_user)
                    db.commit()
                    db.close()
                    return {
                        "message": f"{username} is removed from the company cause the user has no assigned tasks",
                        "Removed By": f"Admin {user['sub']}"
                    }
                
                flag = 0
                for db_task in db_tasks:
                    if db_task.status in ["assigned", "on_hold", "in_progress"]:
                        flag = 1
                        db.close()
                        raise HTTPException(
                            status_code = 400,
                            detail = "Can't remove this user from here cause he has a task which is neither completed not canclled"
                        )

                if flag == 0:
                    for db_task in db_tasks:
                        db_task.assigned_to = None
                    db.delete(db_user)
                    db.commit()
                    db.close()
                    return {
                        "message": f"{username} is removed from the company cause the user has no ongoin tasks",
                        "Removed By": f"Admin {user['sub']}"
                    }

            elif db_user.role == "tech lead":
                all_tech_leads = db.query(User).filter(User.role == "tech lead", User.group_id == db_group.id).all()

                if len(all_tech_leads) == 2:

                    tasks_assigned_to_the_deleting_tech_lead = db.query(Task).filter(Task.assigned_to == db_user.id).all()
                    if len(tasks_assigned_to_the_deleting_tech_lead) > 0:
                        flag = 0
                        for db_task in tasks_assigned_to_the_deleting_tech_lead:
                            if db_task.status in ["assigned", "on_hold", "in_progress"]:
                                flag = 1
                                db.close()
                                raise HTTPException(
                                    status_code = 400,
                                    detail = "Can't remove this tech lead from here cause he has a task which is neither completed not canclled"
                                )

                        if flag == 0:
                            for db_task in tasks_assigned_to_the_deleting_tech_lead:
                                db_task.assigned_to = None

                            all_tasks_created_by_the_deleting_tech_lead = db.query(Task).filter(Task.created_by == db_user.id).all()

                            for another_tech_lead in all_tech_leads:
                                if another_tech_lead.id != db_user.id:
                                    tech_lead_except_the_deleting_one = another_tech_lead
                                    break

                            for TASK in all_tasks_created_by_the_deleting_tech_lead:
                                TASK.created_by = tech_lead_except_the_deleting_one.id

                            db.delete(db_user)
                            db.commit()
                            db.close()
                            return {
                                "message": f"{username} is removed from the company while preserving all the rules",
                                "Removed By": f"Admin {user['sub']}"
                            }

                    else:

                        all_tasks_created_by_the_deleting_tech_lead = db.query(Task).filter(Task.created_by == db_user.id).all()

                        for another_tech_lead in all_tech_leads:
                            if another_tech_lead.id != db_user.id:
                                    tech_lead_except_the_deleting_one = another_tech_lead
                                    break

                        for TASK in all_tasks_created_by_the_deleting_tech_lead:
                            TASK.created_by = tech_lead_except_the_deleting_one.id

                        db.delete(db_user)
                        db.commit()
                        db.close()
                        return {
                            "message": f"{username} is removed from the company while preserving all the rules",
                            "Removed By": f"Admin {user['sub']}"
                        }
                
                else:
                    db.close()
                    raise HTTPException(
                        status_code = 400,
                        detail = "Can't remove this tech lead cause he is the only tech lead in this group as well as this project, to remove him (if necessary) must add another tech lead before."
                    )
            
            elif db_user.role == "manager":
                any_other_manager = db.query(User).filter(User.role == "manager", User.id != db_user.id).all()

                if not any_other_manager:
                    db.close()
                    raise HTTPException(
                        status_code = 400,
                        detail = "Can't remove him cause he is the only manager present in our company so to remove him company must need to hire one and he is also associated with a project"
                    )

                else:
                    flag = 0
                    for other_manager in any_other_manager:
                        if other_manager.group_id:
                            db_project_for_the_other_manager = db.query(Project).filter(Project.group_id == other_manager.group_id).first()

                            if not db_project_for_the_other_manager:
                                flag = 1

                                group_of_the_replacment_manager = db.query(Group).filter(Group.manager_id == other_manager.id).first()
                                if group_of_the_replacment_manager is not None:
                                    group_of_the_replacment_manager.manager_id = None

                                other_manager.group_id = db_user.group_id

                                db_group.manager_id = other_manager.id

                                db.delete(db_user)
                                db.commit()
                                db.close()
                                return {
                                    "message": f"{username} is removed from the company and another manager is assigned for the Project",
                                    "Removed By": f"Admin {user['sub']}"
                                }

                        else:
                            flag = 1

                            other_manager.group_id = db_user.group_id

                            db_group.manager_id = other_manager.id
                            
                            db.delete(db_user)
                            db.commit()
                            db.close()
                            return {
                                "message": f"{username} is removed from the company and another manager is assigned for the Project",
                                "Removed By": f"Admin {user['sub']}"
                            }

                    
                    if flag == 0:
                        db.close()
                        raise HTTPException(
                            status_code = 400,
                            detail = f"No manager can't be replaced in the place of {username} so not possible to remove him"
                        )
