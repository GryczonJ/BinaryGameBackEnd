from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import all routers
from routers import auth, users, puzzles, solves, rankings, calendar, ai, admin

app = FastAPI(
    title="Binary Game API",
    description="API for Binary Puzzle Game with daily challenges, rankings, and AI hints",
    version="1.0.0"
)

# Add CORS middleware FIRST - must be before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Binary Game API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "puzzles": "/puzzles",
            "solves": "/solves",
            "rankings": "/rankings",
            "calendar": "/calendar",
            "ai": "/ai",
            "admin": "/admin"
        }
    }


# Include all routers with their prefixes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(puzzles.router, prefix="/puzzles", tags=["Puzzles"])
app.include_router(solves.router, prefix="/solves", tags=["Solves"])
app.include_router(rankings.router, prefix="/rankings", tags=["Rankings"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
app.include_router(ai.router, prefix="/ai", tags=["AI Hints"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
