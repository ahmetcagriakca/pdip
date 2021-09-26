import json
import os
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.dependency.container import DependencyContainer

# from .controllers.TestApiResource import TestApiResource

class TestBasicApp(TestCase):
    def setUp(self):
        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        self.client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()

    def tearDown(self):
        DependencyContainer.cleanup()
        return super().tearDown()

    def test_api_controller(self):
        response = self.client.get(
            'api/BasicApi?value=1',
            content_type='application/json',
        )

        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Result'] == 'testdata:1'