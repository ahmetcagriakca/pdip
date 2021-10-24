import json
from unittest import TestCase

from pdip import Pdi
from pdip.api.app import FlaskAppWrapper
from pdip.data import DatabaseSessionManager, RepositoryProvider
from tests.api.basic_app_with_cqrs.domain.User import User
from tests.api.basic_app_with_cqrs.application.controllers.UserCqrsResource import UserCqrsResource


class TestBasicAppWithCqrs(TestCase):
    def setUp(self):
        self.pdi = Pdi()
        self.pdi.drop_all()
        self.pdi.create_all()
        self.client = self.pdi.get(FlaskAppWrapper).test_client()

    def tearDown(self):
        if hasattr(self,'pdi') and self.pdi is not None:
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

    def test_api_logs(self):
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
