from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api import businesses, smtp, target_markets, campaigns, prospects, tracking, influencers, social_listening, voice_calls, lead_discovery
from app.db.seed_data import ensure_seeded

# Auto-create tables & seed default businesses and SMTP accounts
Base.metadata.create_all(bind=engine)
ensure_seeded()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(businesses.router, prefix=settings.API_V1_STR)
app.include_router(smtp.router, prefix=settings.API_V1_STR)
app.include_router(target_markets.router, prefix=settings.API_V1_STR)
app.include_router(campaigns.router, prefix=settings.API_V1_STR)
app.include_router(prospects.router, prefix=settings.API_V1_STR)
app.include_router(tracking.router, prefix=settings.API_V1_STR)
app.include_router(influencers.router, prefix=settings.API_V1_STR)
app.include_router(social_listening.router, prefix=settings.API_V1_STR)
app.include_router(voice_calls.router, prefix=settings.API_V1_STR)
app.include_router(lead_discovery.router, prefix=settings.API_V1_STR, tags=["Lead Discovery"])

@app.get("/")
def root():
    return {
        "message": "Brit Lead Gen & Outreach System API Running",
        "version": "1.0.0",
        "docs": "/docs"
    }
