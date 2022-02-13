import json
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi


class TestBasicApp(TestCase):
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

    def test_api_controller(self):
        response = self.client.get(
            'api/BasicApi?value=1',
            content_type='application/json',
        )

        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Result'] == 'testdata:1'
