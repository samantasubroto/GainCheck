"""Uses the Firebase Admin library to check tokens and to log users out.

This needs the service account file (firebase-service-account.json).
"""

import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import settings


def _start_firebase():
    """Start the Firebase Admin library, but only once."""
    try:
        firebase_admin.get_app()  # already started
    except ValueError:
        cred = credentials.Certificate(settings.firebase_service_account_path)
        firebase_admin.initialize_app(cred)


def verify_token(id_token):
    """Check an id token.

    Returns the information inside the token (it includes "uid" and "email")
    if the token is good. Returns None if it is expired, fake or revoked.
    """
    _start_firebase()
    try:
        # check_revoked=True makes a token stop working after logout.
        return auth.verify_id_token(id_token, check_revoked=True)
    except (ValueError, auth.InvalidIdTokenError, auth.RevokedIdTokenError):
        return None


def revoke_tokens(uid):
    """Log the user out everywhere by cancelling their refresh tokens."""
    _start_firebase()
    auth.revoke_refresh_tokens(uid)
