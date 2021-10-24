import json
from unittest import TestCase

from pdip import Pdi
from pdip.api.app import FlaskAppWrapper

class TestBasicApp(TestCase):
    def setUp(self):
        self.pdi = Pdi()
        self.client = self.pdi.get(FlaskAppWrapper).test_client()

    def tearDown(self):
        if hasattr(self,'pdi') and self.pdi is not None:
            del self.pdi
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