from fastapi import APIRouter

from app.api.v1.routes import health

# This router collects all the v1 routes in one place.
# Each time we add a new routes file, we add one line here.
api_router = APIRouter()
api_router.include_router(health.router)
