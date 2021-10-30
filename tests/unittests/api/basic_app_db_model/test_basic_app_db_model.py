import json
import sys
from unittest import TestCase

from pdip.api.app import FlaskAppWrapper
from pdip.base import Pdi
from pdip.data import DatabaseSessionManager, RepositoryProvider
from tests.unittests.api.basic_app_db_model.models.dao import Base
from tests.unittests.api.basic_app_db_model.models.dao.User import User


class TestBasicAppDbModel(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            engine = self.pdi.get(DatabaseSessionManager).engine
            Base.metadata.create_all(engine)
            self.client = self.pdi.get(FlaskAppWrapper).test_client()
        except Exception as ex:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
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

    def test_check_user_model(self):
        name = 'test'
        engine = self.pdi.get(DatabaseSessionManager).engine
        engine.connect()
        repository_provider = self.pdi.get(RepositoryProvider)
        user_repository = repository_provider.get(User)
        new_user = User()
        new_user.Name = name
        user_repository.insert(new_user)
        repository_provider.commit()
        user = user_repository.first(Name=name)
        assert user != None
        assert user.Name == name
