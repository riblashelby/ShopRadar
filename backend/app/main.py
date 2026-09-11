"""
FastAPI application factory and main entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.db.database import init_db, close_db
from app.parsers.factory import init_registry, cleanup_parsers
from app.api.router import api_router


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    # Initialize parser registry
    init_registry()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Self-hosted price comparison for grocery stores",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Setup lifespan events
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up CheapCart application...")
        await init_db()
        logger.info("Database initialized")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down CheapCart application...")
        await cleanup_parsers()
        await close_db()
        logger.info("Application shutdown complete")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
