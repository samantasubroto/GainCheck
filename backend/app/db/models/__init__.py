# Import every model here so Alembic can find all the tables.
# When we add a new model file, we add one line for it.
from app.db.models.user import User  # noqa: F401
