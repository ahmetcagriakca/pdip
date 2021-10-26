from sqlalchemy import Column, Integer, String, DateTime

from pdip.data import Entity
from tests.api.basic_app_db_model.models.dao import Base


class User(Entity, Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}  # "schema": "Common",
    Name = Column(String(300), index=False, unique=False, nullable=False)

