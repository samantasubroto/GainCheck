from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, get_db
from app.llm.provider import LLMError
from app.repositories import report_repository
from app.schemas.report import ReportCreate, ReportOut, ReportSummary
from app.services import report_service

router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportOut)
def generate_report(body: ReportCreate, db=Depends(get_db), user=Depends(get_current_user)):
    """Make the report for a month. This asks the language model, so it can take a few minutes."""
    try:
        return report_service.generate_report(db, user, body.month)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except LLMError as error:
        raise HTTPException(status_code=503, detail="The language model is not available. " + str(error))


@router.get("/reports", response_model=List[ReportSummary])
def list_reports(db=Depends(get_db), user=Depends(get_current_user)):
    return report_repository.list_for_user(db, user.uid)


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    report = report_repository.get_for_user(db, user.uid, report_id)
    if report is None:
        # Same answer whether it does not exist or belongs to someone else.
        raise HTTPException(status_code=404, detail="Report not found")
    return report
