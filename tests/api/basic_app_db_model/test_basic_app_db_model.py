# import json
# import os
# from unittest import TestCase

# from tests.api.basic_app_db_model.models.dao.User import User

# from pdip.api.app import FlaskAppWrapper
# from pdip.data import DatabaseSessionManager, RepositoryProvider
# from pdip.dependency.container import DependencyContainer


# class TestBasicAppDbModel(TestCase):
#     def setUp(self):
#         root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
#         DependencyContainer.initialize_service(root_directory=root_directory)
#         engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
#         DependencyContainer.Base.metadata.create_all(engine)
#         self.client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()

#     def tearDown(self):
#         DependencyContainer.cleanup()
#         return super().tearDown()

#     def test_user_model_api(self):
#         response = self.client.get(
#             'api/BasicApiDbModel?name=TestUser',
#             content_type='application/json',
#         )
#         assert response.status_code == 200
#         response_data = response.get_data(as_text=True)
#         json_data = json.loads(response_data)
#         assert json_data['Result'] == 'user:TestUser'

#     # def test_check_user_model(self):
#     #     name = 'test'
#     #     engine = DependencyContainer.Instance.get(
#     #         DatabaseSessionManager).engine
#     #     engine.connect()
#     #     repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
#     #     user_repository = repository_provider.get(User)
#     #     new_user = User()
#     #     new_user.Name = name
#     #     user_repository.insert(new_user)
#     #     repository_provider.commit()
#     #     user = user_repository.first(Name=name)
#     #     assert user != None
#     #     assert user.Name == name

# # root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
# # DependencyContainer.initialize_service(root_directory=root_directory)
# # engine = DependencyContainer.Instance.get(DatabaseSessionManager).engine
# # DependencyContainer.Base.metadata.create_all(engine)
# # client = DependencyContainer.Instance.injector.get(FlaskAppWrapper).run()
