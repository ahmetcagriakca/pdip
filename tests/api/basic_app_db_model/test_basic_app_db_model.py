import json
import os
from unittest import TestCase


from pdi.api.app import FlaskAppWrapper
from pdi.data import DatabaseSessionManager, RepositoryProvider
from pdi.dependency.container import DependencyContainer
from tests.api.basic_app_db_model.models.dao.User import User

class TestBasicAppDbModel(TestCase):
    def __init__(self, methodName='TestBasicAppDbModel'):
        super(TestBasicAppDbModel, self).__init__(methodName)
        #
    def setUp(self) -> None:
        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
        DependencyContainer.Base.metadata.create_all(engine)
        self.client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()

    def test_user_model_api(self):
        self.check_user_model()
        response = self.client.get(
            'api/BasicApiDbModel?name=TestUser',
            content_type='application/json',
        )
        print(response.status_code)
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Result'] == 'username:TestUser'

    def check_user_model(self):
        name = 'test'
        repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
        user_repository = repository_provider.get(User)
        new_user = User()
        new_user.Name = name
        user_repository.insert(new_user)
        repository_provider.commit()
        user = user_repository.first(Name=name)
        assert user != None
        assert user.Name == name

# root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
# DependencyContainer.initialize_service(root_directory=root_directory)
# engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
# DependencyContainer.Base.metadata.create_all(engine)
# client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).run()