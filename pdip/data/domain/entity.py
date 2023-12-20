import uuid
from datetime import datetime

from sqlalchemy import DateTime, Column
from sqlalchemy.ext.declarative import declared_attr

from .entity_base import EntityBase
from .types import GUID


class Entity(EntityBase):
    Id = Column(
        GUID(),
        primary_key=True,
        default=str(uuid.uuid4())
    )

    @declared_attr
    def CreateUserId(cls):
        return Column(GUID(), index=False, unique=False, nullable=False,
                      default=uuid.UUID("00000000-0000-0000-0000-000000000000"))

    @declared_attr
    def CreateUserTime(cls):
        return Column(DateTime, index=False, unique=False, nullable=False, default=datetime.now)

    @declared_attr
    def UpdateUserId(cls):
        return Column(GUID(), index=False, unique=False, nullable=True)

    @declared_attr
    def UpdateUserTime(cls):
        return Column(DateTime, index=False, unique=False, nullable=True)

    @declared_attr
    def TenantId(cls):
        return Column(GUID(), index=False, unique=False, nullable=False)

    @declared_attr
    def GcRecId(cls):
        return Column(GUID(), index=False, unique=False, nullable=True)
