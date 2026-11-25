from typing import List

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.repositories import exercise_repository
from app.schemas.exercise import ExerciseOut

router = APIRouter(tags=["exercises"])


@router.get("/exercises", response_model=List[ExerciseOut])
def list_exercises(db=Depends(get_db), user=Depends(get_current_user)):
    # The list is the same for everyone. We still ask for a logged-in user,
    # so only people with an account can use the API.
    return exercise_repository.get_all(db)
