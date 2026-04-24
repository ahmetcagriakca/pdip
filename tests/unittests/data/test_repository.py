"""Unit tests for ``pdip.data.repository.Repository``.

These tests stand up an in-memory SQLite database so the full
``Repository[T]`` surface — insert, update, delete (soft), read —
can run without mocking SQLAlchemy, while still being a true unit
test (no external service, no network, no process boundary).

They also pin down the audit-column contract from ADR-0010 and the
soft-delete behaviour from ADR-0009.
"""

import uuid
from dataclasses import dataclass
from typing import Optional
from unittest import TestCase

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from pdip.data.repository.repository import Repository


Base = declarative_base()


@dataclass
class _ConfigStub:
    type: Optional[str] = None
    connection_string: str = ''
    application_name: str = 'pdip-tests'
    execution_options: dict = None


class _Widget(Base):
    __tablename__ = "widget"
    # Minimal stand-in for ``pdip.data.domain.entity.Entity`` so tests
    # do not pull in the full DI-registered base class.
    Id = Column(Integer, primary_key=True)
    Name = Column(String(32), nullable=False)
    CreateUserId = Column(String(36))
    CreateUserTime = Column(String(32))
    UpdateUserId = Column(String(36))
    UpdateUserTime = Column(String(32))
    TenantId = Column(String(36))
    GcRecId = Column(String(36))


class _SessionManagerStub:
    """A stand-in for ``DatabaseSessionManager`` that the Repository
    only touches through `.session` and `.engine`."""

    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(bind=self.engine)
        self.session = self._Session()

    def commit(self):
        self.session.commit()


class RepositoryInsertPopulatesAuditColumns(TestCase):
    def setUp(self):
        self.mgr = _SessionManagerStub()
        self.repo = Repository(_Widget, self.mgr)

    def test_insert_fills_create_user_and_tenant(self):
        widget = _Widget(Name="first")
        self.repo.insert(widget)
        self.repo.commit()

        stored = self.repo.first(Name="first")
        self.assertIsNotNone(stored.CreateUserId)
        self.assertIsNotNone(stored.CreateUserTime)
        self.assertEqual(
            stored.TenantId, str(uuid.UUID("00000000-0000-0000-0000-000000000000"))
        )

    def test_insert_respects_caller_supplied_tenant(self):
        tenant = str(uuid.uuid4())
        widget = _Widget(Name="second", TenantId=tenant)
        self.repo.insert(widget)
        self.repo.commit()

        self.assertEqual(self.repo.first(Name="second").TenantId, tenant)


class RepositoryReadApi(TestCase):
    def setUp(self):
        self.mgr = _SessionManagerStub()
        self.repo = Repository(_Widget, self.mgr)
        for name in ("a", "b", "c"):
            self.repo.insert(_Widget(Name=name))
        self.repo.commit()

    def test_get_returns_every_row(self):
        self.assertEqual(len(self.repo.get()), 3)

    def test_first_matches_filter(self):
        self.assertEqual(self.repo.first(Name="b").Name, "b")

    def test_filter_by_is_chainable_to_all(self):
        self.assertEqual(len(self.repo.filter_by(Name="c").all()), 1)

    def test_get_by_id_returns_the_right_row(self):
        widget = self.repo.first(Name="a")
        self.assertEqual(self.repo.get_by_id(widget.Id).Name, "a")


class RepositoryUpdateSetsAuditColumns(TestCase):
    def setUp(self):
        self.mgr = _SessionManagerStub()
        self.repo = Repository(_Widget, self.mgr)
        self.repo.insert(_Widget(Name="to-edit"))
        self.repo.commit()

    def test_update_populates_update_user_fields(self):
        widget = self.repo.first(Name="to-edit")
        widget.Name = "edited"
        self.repo.update(widget)
        self.repo.commit()

        reloaded = self.repo.first(Name="edited")
        self.assertIsNotNone(reloaded.UpdateUserId)
        self.assertIsNotNone(reloaded.UpdateUserTime)


class RepositoryDeleteIsSoft(TestCase):
    def setUp(self):
        self.mgr = _SessionManagerStub()
        self.repo = Repository(_Widget, self.mgr)
        self.repo.insert(_Widget(Name="to-delete"))
        self.repo.commit()

    def test_delete_marks_gc_rec_id_without_physical_delete(self):
        widget = self.repo.first(Name="to-delete")
        self.repo.delete(widget)
        self.repo.commit()

        # Row still exists physically in the table (ADR-0009).
        still_there = self.mgr.session.query(_Widget).filter_by(Name="to-delete").one()
        self.assertIsNotNone(still_there.GcRecId)
        self.assertIsNotNone(still_there.UpdateUserId)

    def test_delete_by_id_uses_soft_delete_semantics(self):
        widget = self.repo.first(Name="to-delete")
        self.repo.delete_by_id(widget.Id)
        self.repo.commit()

        still_there = self.mgr.session.query(_Widget).filter_by(Id=widget.Id).one()
        self.assertIsNotNone(still_there.GcRecId)
