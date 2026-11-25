from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, get_db
from app.repositories import workout_repository
from app.schemas.workout import WorkoutCreate, WorkoutOut
from app.services import workout_service

router = APIRouter(tags=["workouts"])


@router.post("/workouts", response_model=WorkoutOut, status_code=201)
def create_workout(body: WorkoutCreate, db=Depends(get_db), user=Depends(get_current_user)):
    try:
        session = workout_service.create_workout(db, user.uid, body)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return workout_service.workout_to_dict(session)


@router.get("/workouts", response_model=List[WorkoutOut])
def list_workouts(
    limit: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    sessions = workout_repository.get_all_for_user(db, user.uid, limit)
    return [workout_service.workout_to_dict(s) for s in sessions]


@router.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    session = workout_repository.get_for_user(db, user.uid, workout_id)
    if session is None:
        # Same answer whether it does not exist or belongs to someone else.
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout_service.workout_to_dict(session)
