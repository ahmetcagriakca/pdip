import json
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi
from pdip.data.base import DatabaseSessionManager
from tests.unittests.api.basic_app_with_cqrs.domain.base.base import Base


class TestBasicAppWithCqrs(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            engine = self.pdi.get(DatabaseSessionManager).engine
            Base.metadata.create_all(engine)
            self.client = self.pdi.get(FlaskAppWrapper).test_client()
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        return super().tearDown()

    def create_user(self, create_user_request):
        data = json.dumps(create_user_request)
        response = self.client.post(
            'api/Application/UserCqrs',
            data=data,
            content_type='application/json',
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['IsSuccess']

    def get_user(self, name):
        response = self.client.get(
            'api/Application/UserCqrs?Name=' + name
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['IsSuccess']
        return json_data['Result']['Data']

    def test_create_user(self):
        create_user_request = {
            "Name": "Name",
            "Surname": "Surname",
        }
        self.create_user(create_user_request)

        user_data = self.get_user(create_user_request["Name"])

        # Assert the behaviour in the test body itself so ADR-0026 A.1's
        # machine guard can see it. The ``create_user`` / ``get_user``
        # helpers also carry inline asserts, but those are invisible
        # to a static walker.
        self.assertEqual(user_data["Name"], create_user_request["Name"])
