from datetime import datetime
from sqlalchemy import Integer, DateTime, TIMESTAMP, text, Column, String
from sqlalchemy.ext.declarative import declared_attr


class Entity:
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

    @declared_attr
    def RowVersion(cls):
        return Column(TIMESTAMP(), default=text('DEFAULT'))

    def __init__(self,
                 CreatedByUserId: int = None,
                 CreationDate: datetime = None,
                 LastUpdatedUserId: int = None,
                 LastUpdatedDate: datetime = None,
                 IsDeleted: bool = None,
                 Comments: str = None,
                 RowVersion: bytes = None,
                 ):
        self.CreatedByUserId: int = CreatedByUserId
        self.CreationDate: datetime = CreationDate
        self.LastUpdatedUserId: int = LastUpdatedUserId
        self.LastUpdatedDate: datetime = LastUpdatedDate
        self.IsDeleted: bool = IsDeleted
        self.Comments: str = Comments
        self.RowVersion: bytes = RowVersion
