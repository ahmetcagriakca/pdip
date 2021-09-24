import json
import os
from unittest import TestCase

from sqlalchemy import desc

from pdi.api.app import FlaskAppWrapper
from pdi.data import DatabaseSessionManager, RepositoryProvider
from pdi.dependency.container import DependencyContainer
from tests.api.basic_app_with_log.domain.dao.Log import Log


class TestBasicAppWithLog(TestCase):
    def __init__(self, methodName='TestBasicAppWithLog'):
        super(TestBasicAppWithLog, self).__init__(methodName)

        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        self.client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()
        engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
        DependencyContainer.Base.metadata.create_all(engine)

    def print_error_detail(self, data):
        print(data['message'] if 'message' in data else '')
        print(data['traceback'] if 'traceback' in data else '')
        print(data['message'] if 'message' in data else '')

    def check_model_logs(self):
        repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
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
        self.check_model_logs()
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

        repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
        log_repository = repository_provider.get(Log)
        DependencyContainer.Instance.get(DatabaseSessionManager).engine.connect()
        log = log_repository.table.order_by(desc(Log.Id)).filter_by(TypeId=20).first()
        assert log is not None
        assert log.Content == log_result
