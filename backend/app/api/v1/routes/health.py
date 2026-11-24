from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """Lets us check that the server is running."""
    return {"status": "ok"}
