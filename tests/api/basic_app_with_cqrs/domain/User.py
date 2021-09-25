from sqlalchemy import Column, Integer, String, DateTime

from pdi.data import Entity
from pdi.dependency.container import DependencyContainer


class User(Entity, DependencyContainer.Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}
    Name = Column(String(300), index=False, unique=False, nullable=False)
    Surname = Column(String(300), index=False, unique=False, nullable=False)
