"""Talks to Firebase over HTTP (its REST API) for signup, login and refresh.

We send an email and password, and Firebase sends back tokens.
This file only talks to Firebase. It knows nothing about our database.
"""

import requests

from app.core.config import settings

SIGNUP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
LOGIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
REFRESH_URL = "https://securetoken.googleapis.com/v1/token"


class FirebaseAuthError(Exception):
    """Raised when Firebase says no, for example a wrong password.

    The text is Firebase's own code, such as "EMAIL_EXISTS" or "INVALID_PASSWORD".
    """

    pass


def _send(url, data):
    """Send a request to Firebase and return the answer as a dictionary."""
    response = requests.post(
        url,
        params={"key": settings.firebase_web_api_key},
        data=data,
        timeout=10,
    )
    answer = response.json()

    # When something goes wrong, Firebase answers like:
    # {"error": {"message": "EMAIL_EXISTS"}}
    if response.status_code != 200:
        message = answer.get("error", {}).get("message", "UNKNOWN_ERROR")
        raise FirebaseAuthError(message)

    return answer


def signup(email, password):
    answer = _send(
        SIGNUP_URL,
        {"email": email, "password": password, "returnSecureToken": True},
    )
    return {
        "uid": answer["localId"],
        "email": answer["email"],
        "id_token": answer["idToken"],
        "refresh_token": answer["refreshToken"],
    }


def login(email, password):
    answer = _send(
        LOGIN_URL,
        {"email": email, "password": password, "returnSecureToken": True},
    )
    return {
        "uid": answer["localId"],
        "email": answer["email"],
        "id_token": answer["idToken"],
        "refresh_token": answer["refreshToken"],
    }


def refresh(refresh_token):
    """Trade a refresh token for a new id token.

    Firebase uses different names in this answer (id_token, user_id).
    """
    answer = _send(
        REFRESH_URL,
        {"grant_type": "refresh_token", "refresh_token": refresh_token},
    )
    return {
        "uid": answer["user_id"],
        "id_token": answer["id_token"],
        "refresh_token": answer["refresh_token"],
    }
