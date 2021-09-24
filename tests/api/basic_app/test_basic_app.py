import json
import os
from unittest import TestCase

from pdi.api.app import FlaskAppWrapper
from pdi.dependency.container import DependencyContainer

# from .controllers.TestApiResource import TestApiResource

class TestBasicApp(TestCase):
    def __init__(self, methodName='TestBasicApp'):
        super(TestBasicApp, self).__init__(methodName)

        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        self.client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()

    def print_error_detail(self, data):
        print(data['message'] if 'message' in data else '')
        print(data['traceback'] if 'traceback' in data else '')
        print(data['message'] if 'message' in data else '')

    def test_api_controller(self):
        response = self.client.get(
            'api/BasicApi?value=1',
            content_type='application/json',
        )

        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Result'] == 'testdata:1'