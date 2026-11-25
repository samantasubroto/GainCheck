"""The only file in the frontend that talks to the backend.

Pages never call requests themselves. They call the functions here.
"""

import os

import requests
from dotenv import load_dotenv

# Read BACKEND_URL from the .env file (if there is one).
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")
API_PREFIX = "/api/v1"


class ApiError(Exception):
    """Something went wrong. The text is a message we can show to the user."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


# Friendly texts for the error codes the backend sends.
FRIENDLY_MESSAGES = {
    "EMAIL_EXISTS": "An account with this email already exists. Try logging in.",
    "INVALID_LOGIN_CREDENTIALS": "Wrong email or password.",
    "EMAIL_NOT_FOUND": "Wrong email or password.",
    "INVALID_PASSWORD": "Wrong email or password.",
}


def _error_message(response):
    """Work out what to tell the user when the backend answers with an error."""
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None

    # A normal error: detail is a short code like "EMAIL_EXISTS".
    if isinstance(detail, str):
        return FRIENDLY_MESSAGES.get(detail, "Something went wrong: " + detail)

    # Our input rules were not met (status 422): detail is a list.
    if response.status_code == 422:
        return "Please enter a valid email and a password with at least 6 characters."

    return "Something went wrong. Please try again."


def _call(method, path, json=None, token=None):
    """Send one request to the backend and return the answer as a dictionary."""
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token

    try:
        response = requests.request(
            method,
            BACKEND_URL + API_PREFIX + path,
            json=json,
            headers=headers,
            timeout=15,
        )
    except requests.exceptions.RequestException:
        raise ApiError("Cannot reach the server. Is the backend running?")

    if response.status_code >= 400:
        raise ApiError(_error_message(response), response.status_code)

    return response.json()


def signup(email, password):
    return _call("POST", "/auth/signup", json={"email": email, "password": password})


def login(email, password):
    return _call("POST", "/auth/login", json={"email": email, "password": password})


def logout(id_token):
    return _call("POST", "/auth/logout", token=id_token)
