import json
import os
from unittest import TestCase

from pdi.api.app import FlaskAppWrapper
from pdi.data import DatabaseSessionManager, RepositoryProvider
from pdi.dependency.container import DependencyContainer


class TestBasicAppWithCqrs(TestCase):
    def setUp(self):
        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
        DependencyContainer.Base.metadata.create_all(engine)
        self.client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()

    def tearDown(self):
        engine = DependencyContainer.Instance.get(
            DatabaseSessionManager).engine
        engine.connect()
        DependencyContainer.Base.metadata.drop_all(engine)
        DependencyContainer.cleanup()
        return super().tearDown()

    def create_user(self, create_user_request):
        data=json.dumps(create_user_request)
        response = self.client.post(
            'api/UserCqrs',
            data=data,
            content_type='application/json',
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['IsSuccess'] == True

    def get_user(self, name):
        response = self.client.get(
            'api/UserCqrs?Name=' + name
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['IsSuccess'] == True
        return json_data['Result']['Data']

    def test_api_logs(self):
        from .domain.User import User
        create_user_request = {
            "Name": "Name",
            "Surname": "Surname",
        }
        self.create_user(create_user_request)
        user_data = self.get_user(create_user_request["Name"])

        repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
        user_repository = repository_provider.get(User)
        DependencyContainer.Instance.get(DatabaseSessionManager).engine.connect()
        user = user_repository.filter_by(Id=user_data["Id"]).first()
        assert user is not None
        assert user.Surname == create_user_request["Surname"]

# root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
# DependencyContainer.initialize_service(root_directory=root_directory)
# engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
# DependencyContainer.Base.metadata.create_all(engine)
# DependencyContainer.Instance.injector.get(FlaskAppWrapper).run()