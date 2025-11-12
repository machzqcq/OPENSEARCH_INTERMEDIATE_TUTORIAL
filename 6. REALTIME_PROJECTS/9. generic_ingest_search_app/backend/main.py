"""
FastAPI Main Application
Provides REST API endpoints for OpenSearch ingestion and search functionality
"""
import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import auth, ingest, search
from app.services.opensearch_service import OpenSearchService
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Generic Ingest & Search Application")
    
    # Initialize services
    try:
        os_service = OpenSearchService()
        logger.info("✓ OpenSearch service initialized")
        
        embedding_service = EmbeddingService(os_service)
        await embedding_service.initialize_models()
        logger.info("✓ Embedding models deployed and ready")
        
        # Store services in app state
        app.state.os_service = os_service
        app.state.embedding_service = embedding_service
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize services: {e}")
        raise
    
    yield
    
    logger.info("🛑 Shutting down application")


# Create FastAPI application
app = FastAPI(
    title="Generic Ingest & Search API",
    description="Full-stack application for ingesting data and performing advanced search on OpenSearch",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "message": "Generic Ingest & Search API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check OpenSearch connection
        os_service = app.state.os_service
        health = os_service.client.cluster.health()
        
        return {
            "status": "healthy",
            "opensearch": {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"]
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
