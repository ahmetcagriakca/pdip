import json
import os
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.data import DatabaseSessionManager
from pdip.dependency.container import DependencyContainer


class TestBasicAppWithError(TestCase):
    def setUp(self):
        root_directory = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        engine = DependencyContainer.Instance.get(
            DatabaseSessionManager).engine
        DependencyContainer.Base.metadata.create_all(engine)
        self.client = DependencyContainer.Instance.injector.get(
            FlaskAppWrapper).test_client()

    def tearDown(self):
        DependencyContainer.cleanup()
        return super().tearDown()

    def print_error_detail(self, data):
        print(data['message'] if 'message' in data else '')
        print(data['traceback'] if 'traceback' in data else '')
        print(data['message'] if 'message' in data else '')

    def test_api_controller(self):
        value = 5
        result_error = f"Value:{value} getting error"
        response = self.client.get(
            f'api/BasicApiWithError?value={value}',
            content_type='application/json',
        )

        assert response.status_code == 400
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Message'] == result_error
