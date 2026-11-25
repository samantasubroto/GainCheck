from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, get_db
from app.auth import service
from app.auth.firebase_client import FirebaseAuthError
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def to_http_error(error):
    """Turn a Firebase error code into an HTTP error for the caller."""
    code = str(error)
    if code == "EMAIL_EXISTS":
        status = 409  # conflict: this email is already registered
    elif code in ("INVALID_LOGIN_CREDENTIALS", "EMAIL_NOT_FOUND",
                  "INVALID_PASSWORD", "INVALID_REFRESH_TOKEN", "TOKEN_EXPIRED"):
        status = 401  # not allowed
    else:
        status = 400  # something else was wrong with the request
    return HTTPException(status_code=status, detail=code)


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db=Depends(get_db)):
    try:
        return service.signup(db, body.email, body.password)
    except FirebaseAuthError as error:
        raise to_http_error(error)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    try:
        return service.login(db, body.email, body.password)
    except FirebaseAuthError as error:
        raise to_http_error(error)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    try:
        return service.refresh(body.refresh_token)
    except FirebaseAuthError as error:
        raise to_http_error(error)


@router.post("/logout")
def logout(user=Depends(get_current_user)):
    service.logout(user.uid)
    return {"message": "logged out"}
