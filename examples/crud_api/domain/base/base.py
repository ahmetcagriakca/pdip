from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# One MetaData per example app so tables don't collide with other
# pdip test fixtures that also define Base.
Base = declarative_base(metadata=MetaData())
