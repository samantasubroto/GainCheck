from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.repositories import user_repository
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=UserOut)
def get_me(user=Depends(get_current_user)):
    # get_current_user already found the user from the token. We just return it.
    return user


@router.put("/me", response_model=UserOut)
def update_me(body: UserUpdate, user=Depends(get_current_user), db=Depends(get_db)):
    # We only ever change the logged-in user's own row.
    return user_repository.update(db, user, body.model_dump())
