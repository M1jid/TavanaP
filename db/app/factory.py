"""
Application factory for creating FastAPI app with dependencies
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.startup import startup_event, shutdown_event
from routers import telegram_peers, users, telegram_accounts, rss_resources, user_queries, telegram_channels_underfollow, telegram_users_underfollow


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if not settings.testing else None,
        redoc_url="/redoc" if not settings.testing else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add exception handlers
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    
    # Add startup and shutdown events
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
    
    # Include routers

    app.include_router(
        users.router,
        prefix=f"{settings.api_prefix}",
        tags=["Users"]
    )
    
    app.include_router(
        user_queries.router,
        prefix=f"{settings.api_prefix}/user",
        tags=["User Query Ids (Topic, Person and Event)"]
    )

    app.include_router(
        telegram_peers.router,
        prefix=f"{settings.api_prefix}/telegram",
        tags=["Telegram Peers"]
    )
    
    app.include_router(
        telegram_accounts.router,
        prefix=f"{settings.api_prefix}/telegram",
        tags=["Telegram Accounts"]
    )
    
    app.include_router(
        telegram_channels_underfollow.router,
        prefix=f"{settings.api_prefix}/telegram",
        tags=["Telegram Channels Under Follow"]
    )
    
    app.include_router(
        telegram_users_underfollow.router,
        prefix=f"{settings.api_prefix}/telegram",
        tags=["Telegram Users Under Follow"]
    )
    
    app.include_router(
        rss_resources.router,
        prefix=f"{settings.api_prefix}",
        tags=["RSS Resources"]
    )

    return app 
