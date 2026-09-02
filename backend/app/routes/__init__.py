from .auth import router as auth_router
from .sessions import router as sessions_router
from .skills import router as skills_router
from .analysis import router as analysis_router
from .analytics import router as analytics_router
from .gamification import router as gamification_router
from .reports import router as reports_router
from .notes import router as notes_router
from .coaches import router as coaches_router

__all__ = [
    "auth_router",
    "sessions_router",
    "skills_router",
    "analysis_router",
    "analytics_router",
    "gamification_router",
    "reports_router",
    "notes_router",
    "coaches_router",
]
