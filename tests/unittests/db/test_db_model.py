import sys
from unittest import TestCase

from sqlalchemy import MetaData, create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base(metadata=MetaData())


class User(Base):
    __tablename__ = "User"
    __table_args__ = {"schema": "Common"}  # "schema": "Common",
    # __table_args__ = {'extend_existing': True}  # "schema": "Common",
    Id = Column(
        Integer,
        primary_key=True
    )
    Name = Column(String(300), index=False, unique=False, nullable=False)


class TestDbModel(TestCase):
    def tearDown(self):
        modules = [y for y in sys.modules if 'pdip' in y]
        for module in modules:
            del module
        return super().tearDown()

    def test_model(self):
        engine = create_engine('sqlite:///:memory:', execution_options={"schema_translate_map": {"Common": None}})

        session_factory = sessionmaker(bind=engine)
        session: Session = session_factory()

        Base.metadata.create_all(engine)
        session.add(User(Name='User'))
        session.commit()
        result = session.query(User).filter_by(Name='User').first()
        assert result is not None
        assert result.Name == 'User'
