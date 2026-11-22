from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key = True)
    username: Mapped[str] = mapped_column(String(50), unique = True)
    password: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(50), default = "user")
    experience: Mapped[int] = mapped_column(default = 0)
    account_status: Mapped[str] = mapped_column(String(20), default = "active")
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable = True)

class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key = True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int]
    owner_id: Mapped["int"] = mapped_column(ForeignKey("users.id"))
    storage_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(500))

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(primary_key = True)
    token: Mapped[str] = mapped_column(String(500), unique = True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(50), unique = True)
    description: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default = "active")
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable = True, unique = True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(50), unique = True)
    description: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key = True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_to: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default = "medium")
    status: Mapped[str] = mapped_column(String(20), default = "created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activitylogs"

    id: Mapped[int] = mapped_column(primary_key = True)
    actor_id: Mapped[int | None] = mapped_column(nullable = True)
    actor_username: Mapped[str | None] = mapped_column(String(100), nullable = True)
    action: Mapped[str] = mapped_column(String(100))
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[int | None] = mapped_column(nullable = True)
    description: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    source_ip: Mapped[str | None] = mapped_column(String(100))
    before_data: Mapped[str | None] = mapped_column(Text, nullable = True)
    after_data: Mapped[str | None] = mapped_column(Text, nullable = True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable = True) # UUID: Universally Unique Identifier, 128 bits