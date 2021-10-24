import json
from unittest import TestCase

from pdip import Pdi

from pdip.api.app import FlaskAppWrapper
from pdip.data import DatabaseSessionManager
from pdip.data.repository_provider import RepositoryProvider
# from tests.api.basic_app_db_model.models.dao.User import User


class TestBasicAppDbModel(TestCase):
    def setUp(self):
        self.pdi = Pdi()
        self.pdi.drop_all()
        self.pdi.create_all()
        self.client = self.pdi.get(FlaskAppWrapper).test_client()

    def tearDown(self):
        if hasattr(self,'pdi') and self.pdi is not None:
            del self.pdi
        return super().tearDown()

    def test_user_model_api(self):
        response = self.client.get(
            'api/BasicApiDbModel?name=TestUser',
            content_type='application/json',
        )
        assert response.status_code == 200
        response_data = response.get_data(as_text=True)
        json_data = json.loads(response_data)
        assert json_data['Result'] == 'user:TestUser'

    # def test_check_user_model(self):
    #     name = 'test'
    #     engine = self.pdi.get(DatabaseSessionManager).engine
    #     engine.connect()
    #     repository_provider = self.pdi.get(RepositoryProvider)
    #     user_repository = repository_provider.get(User)
    #     new_user = User()
    #     new_user.Name = name
    #     user_repository.insert(new_user)
    #     repository_provider.commit()
    #     user = user_repository.first(Name=name)
    #     assert user != None
    #     assert user.Name == name
