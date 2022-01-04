from datetime import datetime

from sqlalchemy import Integer, DateTime, Column, String
from sqlalchemy.ext.declarative import declared_attr

from .entity_base import EntityBase


class Entity(EntityBase):
    Id = Column(
        Integer,
        primary_key=True
    )

    @declared_attr
    def CreatedByUserId(cls):
        return Column(Integer, index=False, unique=False, nullable=False, default=0)

    @declared_attr
    def CreationDate(cls):
        return Column(DateTime, index=False, unique=False, nullable=False, default=datetime.now)

    @declared_attr
    def LastUpdatedUserId(cls):
        return Column(Integer, index=False, unique=False, nullable=True)

    @declared_attr
    def LastUpdatedDate(cls):
        return Column(DateTime, index=False, unique=False, nullable=True)

    @declared_attr
    def IsDeleted(cls):
        return Column(Integer, index=False, unique=False, nullable=False, default=0)

    @declared_attr
    def Comments(cls):
        return Column(String(1000), index=False, unique=False, nullable=True)

    # @declared_attr
    # def RowVersion(cls):
    #     return Column(TIMESTAMP(), default=text('DEFAULT'))
