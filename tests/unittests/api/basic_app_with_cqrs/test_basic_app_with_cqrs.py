import json
import sys
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi
from pdip.data import DatabaseSessionManager, RepositoryProvider
from tests.unittests.api.basic_app_with_cqrs.domain.base.base import Base
from tests.unittests.api.basic_app_with_cqrs.domain.user.User import User


class TestBasicAppWithCqrs(TestCase):
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
        modules = [y for y in sys.modules if 'pdip' in y]
        for module in modules:
            del module
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
        assert json_data['IsSuccess'] == True

    def get_user(self, name):
        response = self.client.get(
            'api/Application/UserCqrs?Name=' + name
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['IsSuccess'] == True
        return json_data['Result']['Data']

    def test_create_user(self):
        create_user_request = {
            "Name": "Name",
            "Surname": "Surname",
        }
        self.create_user(create_user_request)
        user_data = self.get_user(create_user_request["Name"])

        repository_provider = self.pdi.get(RepositoryProvider)
        user_repository = repository_provider.get(User)
        self.pdi.get(DatabaseSessionManager).engine.connect()
        user = user_repository.filter_by(Id=user_data["Id"]).first()
        assert user is not None
        assert user.Surname == create_user_request["Surname"]
