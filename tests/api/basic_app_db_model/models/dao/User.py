from sqlalchemy import Column, Integer, String, DateTime

from pdi.data import Entity
from pdi.dependency.container import DependencyContainer


class User(Entity, DependencyContainer.Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}  # "schema": "Common",
    Name = Column(String(300), index=False, unique=False, nullable=False)
    TypeId = Column(Integer, index=False, unique=False, nullable=True)
    Content = Column(String(4000), index=False, unique=False, nullable=True)
    LogDatetime = Column(DateTime, index=False, unique=False, nullable=True)
    JobId = Column(Integer, index=False, unique=False, nullable=True)

# class User(Entity, DependencyContainer.Base):
#     __tablename__ = "User"
#     __table_args__ = {'extend_existing': True}#"schema": "Common",
#     Name = Column(String(300), index=False, unique=False, nullable=False)
