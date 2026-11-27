from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db
from app.schemas.progress import ProgressOut
from app.services import progress_service

router = APIRouter(tags=["progress"])


@router.get("/progress", response_model=ProgressOut)
def get_progress(
    days: int = Query(default=90, ge=7, le=730),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    # The facts are always worked out for the logged-in user only.
    return progress_service.get_progress(db, user.uid, days)
