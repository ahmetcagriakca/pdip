from sqlalchemy import Column, Integer, String, DateTime

from pdip.data.entity import Entity
from pdip.logging.models.log_data import LogData
from tests.unittests.api.basic_app_with_log.domain.dao import Base


class Log(LogData, Entity, Base):
    __tablename__ = "Log"
    __table_args__ = {"schema": "Common"}
    TypeId = Column(Integer, index=False, unique=False, nullable=False)
    Content = Column(String(4000), index=False, unique=False, nullable=True)
    LogDatetime = Column(DateTime, index=False, unique=False, nullable=True)
    JobId = Column(Integer, index=False, unique=False, nullable=True)
