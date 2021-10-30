from sqlalchemy import Column, String

from pdip.data import Entity
from tests.unittests.api.basic_app_with_cqrs.domain import Base


class User(Entity, Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}
    Name = Column(String(300), index=False, unique=False, nullable=False)
    Surname = Column(String(300), index=False, unique=False, nullable=False)
