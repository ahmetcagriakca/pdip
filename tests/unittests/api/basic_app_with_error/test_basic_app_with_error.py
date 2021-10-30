import json
import sys
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi


class TestBasicAppWithError(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            self.client = self.pdi.get(FlaskAppWrapper).test_client()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
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
