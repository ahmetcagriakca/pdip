import dataclasses

import dataclasses_json
from sqlalchemy import Column, String

from pdip.data.domain import Entity, EntityBase
from tests.unittests.api.basic_app_with_cqrs.domain.base import Base


# @dataclasses
# class UserBase(EntityBase):
#      Name: str = None
#      Surname: str = None
class UserBase1:
    def __init__(self,
                 Name: str = None,
                 Surname: str = None,
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.Name = Name
        self.Surname = Surname
class UserBase(EntityBase):
    def __init__(self,
                 Name: str = None,
                 Surname: str = None,
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.Name = Name
        self.Surname = Surname


class User(UserBase, Entity, Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}
    Name = Column(String(300), index=False, unique=False, nullable=False)
    Surname = Column(String(300), index=False, unique=False, nullable=False)
