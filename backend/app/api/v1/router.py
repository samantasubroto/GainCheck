from fastapi import APIRouter

from app.api.v1.routes import auth, body_metrics, exercises, health, profile, workouts

# This router collects all the v1 routes in one place.
# Each time we add a new routes file, we add one line here.
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(exercises.router)
api_router.include_router(workouts.router)
api_router.include_router(body_metrics.router)
