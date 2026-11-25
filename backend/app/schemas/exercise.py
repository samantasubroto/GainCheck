from pydantic import BaseModel, ConfigDict


class ExerciseOut(BaseModel):
    """One exercise in the list we send to the frontend."""

    # from_attributes lets Pydantic read the values straight from the database object.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    is_bodyweight: bool
