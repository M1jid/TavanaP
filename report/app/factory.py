from datetime import timedelta
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi import Depends, FastAPI, HTTPException, status

from auth.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    User,
    Token,
    check_user_entrance,
)

from app.startup import (
    elastic_handler,
    kafka_router
)

from app.config import TELEGRAM_INDEX_MESSAGES, ACCESS_TOKEN_EXPIRE_MINUTES
from services import services
from schemas import schemas
from routers import  main
# from routers.actions import user_query, user_channel, user

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown logic"""
    # Startup logic
    try:
        pass
        # scheduler.add_job()
        # scheduler.start()
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    yield
    # Shutdown logic
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    PRODUCTION = False
    app = FastAPI(
        lifespan=lifespan,
        title="Report Data API",
        # description=services.load_description('docs/descriptions/report_apis.md'),
        version="1.0.0",
        root_path="/api/v1",
        redoc_url=None if PRODUCTION else "/redoc",
        docs_url=None if PRODUCTION else "/docs",
        openapi_url=None if PRODUCTION else "/openapi.json",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(main.router)
    
    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return await request_validation_exception_handler(request, exc)
    
    # Add authentication endpoint
    @app.post(
        "/token", 
        response_model=Token,
        description=services.load_description('docs/authorization.md'),
    )
    async def login_for_access_token(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
    ):
        user = authenticate_user(form_data.username, form_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not check_user_entrance(user, request.base_url):
            raise HTTPException (
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User Not Found for {request.base_url}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    # Add health check endpoint
    @app.get("/status")
    async def get_status():
        return {"status": "healthy"}
    
    # Add explicit OPTIONS handler for CORS preflight
    @app.options("/{full_path:path}")
    async def options_handler(full_path: str):
        return {"message": "OK"}

    # Add satellite channels endpoint
    @app.get("/satellite_channels/sources")
    async def get_satellite_channels(
        current_user: User = Depends(get_current_active_user)
    ):
        return [
            "http://www.parsatv.com/embed.php?name=Channel-One-TV&auto=true",
            "http://www.parsatv.com/embed.php?name=VOA-Persian&auto=true",
            "http://www.parsatv.com/embed.php?name=BBC-Persian&auto=true",
            "http://www.parsatv.com/embed.php?name=Iran-TV-Israel&auto=true",
            "http://www.parsatv.com/embed.php?name=Irane-Farda&auto=true",
            "http://www.parsatv.com/embed.php?name=Israel-Pars-TV&auto=true",
        ]
    
    return app 
