import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.orm as orm

from app.config import settings

# Use the database URL from settings
engine = sql.create_engine(settings.database_url)

SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Test database engine for isolated testing
test_engine = None
test_session_local = None

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_test_engine():
    """Get a test database engine for isolated testing"""
    global test_engine
    if test_engine is None:
        test_engine = sql.create_engine(settings.test_database_url)
    return test_engine

def get_test_session():
    """Get a test database session factory"""
    global test_session_local
    if test_session_local is None:
        test_session_local = orm.sessionmaker(autocommit=False, autoflush=False, bind=get_test_engine())
    return test_session_local
