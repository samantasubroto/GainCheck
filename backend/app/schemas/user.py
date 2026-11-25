from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    """What we send back when someone asks for a profile."""

    # from_attributes lets Pydantic read the values straight from the database object.
    model_config = ConfigDict(from_attributes=True)

    uid: str
    email: str
    display_name: Optional[str] = None
    sex: Optional[str] = None
    birth_year: Optional[int] = None
    height_cm: Optional[float] = None
    training_years: Optional[float] = None
    goal: Optional[str] = None


class UserUpdate(BaseModel):
    """What the user sends when they save their profile.

    Literal means only these exact words are allowed.
    Field(ge=..., le=...) means the number must be between the two values.
    """

    display_name: Optional[str] = Field(default=None, max_length=50)
    sex: Literal["male", "female"]
    birth_year: int = Field(ge=1920, le=2015)
    height_cm: float = Field(ge=100, le=250)
    training_years: float = Field(ge=0, le=80)
    goal: Literal["strength", "muscle", "fat_loss", "general"]
