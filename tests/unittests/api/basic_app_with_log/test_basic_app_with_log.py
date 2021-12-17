import json
from unittest import TestCase

from sqlalchemy import desc

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi
from pdip.data.base import DatabaseSessionManager
from pdip.data.repository import RepositoryProvider
from tests.unittests.api.basic_app_with_log.domain.dao import Base
from tests.unittests.api.basic_app_with_log.domain.dao.Log import Log


class TestBasicAppWithLog(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            engine = self.pdi.get(DatabaseSessionManager).engine
            Base.metadata.create_all(engine)
            self.client = self.pdi.get(FlaskAppWrapper).test_client()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        return super().tearDown()

    def test_check_model_logs(self):
        repository_provider = self.pdi.get(
            RepositoryProvider)
        log_repository = repository_provider.get(Log)
        new_log = Log()
        new_log.TypeId = 1
        new_log.Content = 'test'
        log_repository.insert(new_log)
        repository_provider.commit()
        log = log_repository.first(TypeId=1)
        assert log != None
        assert log.Content == 'test'

    def test_api_logs(self):
        value = 1
        api_result = f'testdata:{value}'
        log_result = f'data:{value}'
        response = self.client.get(
            'api/BasicApiWithLog?value=1',
            content_type='application/json',
        )

        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Result'] == api_result

        repository_provider = self.pdi.get(
            RepositoryProvider)
        log_repository = repository_provider.get(Log)
        self.pdi.get(
            DatabaseSessionManager).engine.connect()
        log = log_repository.table.order_by(
            desc(Log.Id)).filter_by(TypeId=20).first()
        assert log is not None
        assert log.Content == log_result
