from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.api import auth, users, books, genres, reviews

app = FastAPI(
    title=settings.app_name,
    description="Backend API for Book Review Platform",
    version=settings.app_version,
    debug=settings.debug,
)

# Security middleware - TrustedHost should be added first
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(books.router, prefix="/api/v1")
app.include_router(genres.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - welcome message."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "BRS Backend is running",
        "version": settings.app_version
    }
