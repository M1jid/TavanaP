"""
RSS Service Main Application

This is the main entry point for the RSS feed processing service.
"""

from app.factory import create_app

# Create the FastAPI application using the factory pattern
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
