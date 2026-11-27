from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db
from app.repositories import body_metric_repository
from app.schemas.body_metric import BodyMetricIn, BodyMetricOut

router = APIRouter(tags=["body metrics"])


@router.post("/body-metrics", response_model=BodyMetricOut)
def save_body_metric(body: BodyMetricIn, db=Depends(get_db), user=Depends(get_current_user)):
    # One entry per day: saving again for the same date updates that day's entry.
    return body_metric_repository.save(db, user.uid, body.model_dump())


@router.get("/body-metrics", response_model=List[BodyMetricOut])
def list_body_metrics(
    limit: int = Query(default=100, ge=1, le=500),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    return body_metric_repository.get_all_for_user(db, user.uid, limit)
