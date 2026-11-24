from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Every database model (User, Workout, ...) inherits from this class.

    SQLAlchemy keeps a list of all the tables that inherit from it,
    and Alembic reads that list to build the migrations.
    """

    pass
