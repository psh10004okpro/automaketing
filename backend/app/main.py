"""
Main FastAPI Application
Marketing Automation Platform
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="All-in-one marketing automation platform for startups and SMBs",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Marketing Automation Platform...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Marketing Automation Platform",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": str(datetime.utcnow())
    }


# Import and include routers
from app.api import auth, campaigns, ai_content, leads, analytics, workflows, sms_campaigns, social_media, ab_tests, drip_campaigns, segments

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(ai_content.router, prefix="/api/ai", tags=["AI Content"])
app.include_router(leads.router, prefix="/api/leads", tags=["Lead Management"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(sms_campaigns.router, prefix="/api/sms", tags=["SMS Campaigns"])
app.include_router(social_media.router, prefix="/api/social", tags=["Social Media"])
app.include_router(ab_tests.router, prefix="/api/ab-tests", tags=["A/B Testing"])
app.include_router(drip_campaigns.router, prefix="/api/drip-campaigns", tags=["Drip Campaigns"])
app.include_router(segments.router, prefix="/api/segments", tags=["Segments"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
