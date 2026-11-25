"""All database queries for the users table live here."""

from app.db.models.user import User


def get_by_uid(db, uid):
    """Return the user with this uid, or None if there is none."""
    return db.query(User).filter(User.uid == uid).first()


def create(db, uid, email):
    user = User(uid=uid, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create(db, uid, email):
    """Return the user, and create the row first if this is their first time."""
    user = get_by_uid(db, uid)
    if user is None:
        user = create(db, uid, email)
    return user
