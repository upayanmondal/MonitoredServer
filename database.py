from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://username:password@localhost:5432/monitored_server"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush = False,
    autocommit = False
)

class Base(DeclarativeBase):
    pass
