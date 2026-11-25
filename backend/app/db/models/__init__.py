# Import every model here so Alembic can find all the tables.
# When we add a new model file, we add one line for it.
from app.db.models.user import User  # noqa: F401
from app.db.models.exercise import Exercise  # noqa: F401
from app.db.models.workout import WorkoutSession, WorkoutSet  # noqa: F401
