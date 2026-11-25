"""Puts Firebase and our database together for signup, login, refresh and logout."""

from app.auth import firebase_client, token_verifier
from app.repositories import user_repository


def signup(db, email, password):
    result = firebase_client.signup(email, password)
    user_repository.get_or_create(db, result["uid"], result["email"])
    return result


def login(db, email, password):
    result = firebase_client.login(email, password)
    # First login ever? Then we do not have a row for this user yet.
    user_repository.get_or_create(db, result["uid"], result["email"])
    return result


def refresh(refresh_token):
    return firebase_client.refresh(refresh_token)


def logout(uid):
    token_verifier.revoke_tokens(uid)
