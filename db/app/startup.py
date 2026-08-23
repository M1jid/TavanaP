"""
Application startup and shutdown events
"""
import asyncio
from fastapi import FastAPI
from database import engine, Base
from app.config import settings


async def startup_event():
    """Application startup event"""
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {'Testing' if settings.testing else 'Production'}")
    print(f"Database: {settings.database_url}")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise
    
    print("Application startup completed")


async def shutdown_event():
    """Application shutdown event"""
    print(f"Shutting down {settings.app_name}")
    
    # Close database connections
    try:
        engine.dispose()
        print("Database connections closed")
    except Exception as e:
        print(f"Error closing database connections: {e}")
    
    print("Application shutdown completed") 