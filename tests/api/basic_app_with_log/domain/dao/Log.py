from sqlalchemy import Column, Integer, String, DateTime

from pdi.data.entity import Entity
from pdi.dependency.container import DependencyContainer
from pdi.logging.log_data import LogData


class Log(LogData, Entity, DependencyContainer.Base):
    __tablename__ = "Log"
    __table_args__ = {"schema": "Common"}
    TypeId = Column(Integer, index=False, unique=False, nullable=False)
    Content = Column(String(4000), index=False, unique=False, nullable=True)
    LogDatetime = Column(DateTime, index=False, unique=False, nullable=True)
    JobId = Column(Integer, index=False, unique=False, nullable=True)
