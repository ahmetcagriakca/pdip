from sqlalchemy import Column, Integer, String, DateTime

from pdip.data import Entity
from pdip.dependency.container import DependencyContainer


class User(Entity, DependencyContainer.Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}  # "schema": "Common",
    Name = Column(String(300), index=False, unique=False, nullable=False)

