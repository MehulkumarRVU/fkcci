from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import init_database
from app.routes import auth_router, sessions_router, skills_router, analysis_router, analytics_router

# Initialize FastAPI app
app = FastAPI(
    title="PocketCoach AI API",
    description="AI-Powered Real-Time Sports Technique Coach for Table Tennis & Boxing",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    print("✅ Database initialized successfully")
    print("🚀 PocketCoach AI backend is running on http://localhost:8080")

# Include routers
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(skills_router)
app.include_router(analysis_router)
app.include_router(analytics_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to PocketCoach AI API",
        "version": "1.0.0",
        "sports": ["table_tennis", "boxing"],
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "PocketCoach AI Backend",
        "port": 8080
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
