from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
from backend.utils.logging_config import setup_logging
setup_logging()

# Import API routes
from backend.api import video, summary, auth

# Create FastAPI app
app = FastAPI(
    title="YouTube Transcript Extractor",
    description="A web application that extracts transcripts from YouTube videos using proxy configuration.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(video.router, prefix="/api", tags=["video"])
app.include_router(summary.router, prefix="/api", tags=["summary"])
app.include_router(auth.router, prefix="/api", tags=["authentication"])

# Mount static files for frontend (after API routes to avoid conflicts)
app.mount('/app', StaticFiles(directory='frontend', html=True), name='frontend')

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Backend is running and ready to accept requests",
        "timestamp": time.time()
    }

# Root endpoint to serve frontend
@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse('frontend/index.html')

@app.get("/api/status")
async def get_status():
    """Get detailed status of the backend services"""
    try:
        # Check if summarizer is loaded
        from backend.api.summary import get_summarizer
        summarizer = get_summarizer()
        summarizer_status = "ready" if summarizer and summarizer.chat else "loading"
    except Exception:
        summarizer_status = "error"
    
    return {
        "status": "running",
        "services": {
            "summarizer": summarizer_status,
            "video_processor": "ready"
        },
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )

