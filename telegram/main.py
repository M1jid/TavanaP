"""
Main entry point for the Telegram Data API application.

This module creates and runs the FastAPI application using the factory pattern
for better organization and testability.
"""

import time
import uvicorn
from app.startup.application import create_app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
