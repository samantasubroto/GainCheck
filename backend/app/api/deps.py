"""Helpers that routes can ask for with Depends(...)."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import token_verifier
from app.db.session import SessionLocal
from app.repositories import user_repository

# Reads the "Authorization: Bearer <token>" header.
# It also adds an "Authorize" button to the /docs page.
bearer = HTTPBearer()


def get_db():
    """Give a route a database session, and close it when the route is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db=Depends(get_db),
):
    """Find out who is calling, using the token they sent.

    Routes that need a logged-in user add: user = Depends(get_current_user)
    """
    token_info = token_verifier.verify_token(credentials.credentials)
    if token_info is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_repository.get_or_create(db, token_info["uid"], token_info["email"])
