from sqlalchemy import Column, Float, Integer, String

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # Firebase gives every user a unique id (uid). We use it as our primary key.
    uid = Column(String, primary_key=True)
    email = Column(String, nullable=False)

    # Profile fields. They are empty until the user fills in their profile.
    display_name = Column(String, nullable=True)
    sex = Column(String, nullable=True)  # "male" or "female"
    birth_year = Column(Integer, nullable=True)
    height_cm = Column(Float, nullable=True)
    training_years = Column(Float, nullable=True)
    goal = Column(String, nullable=True)  # for example "strength" or "fat_loss"
