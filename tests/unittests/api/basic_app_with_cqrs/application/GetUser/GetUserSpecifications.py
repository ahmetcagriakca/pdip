from injector import inject
from sqlalchemy.orm import Query

from pdip.data.repository import RepositoryProvider
from pdip.dependency import IScoped
from tests.unittests.api.basic_app_with_cqrs.application.GetUser.GetUserQuery import GetUserQuery
from tests.unittests.api.basic_app_with_cqrs.domain.user.User import User


class GetUserSpecifications(IScoped):
    @inject
    def __init__(self,
                 repository_provider: RepositoryProvider,
                 ):
        self.repository_provider = repository_provider

    def __specified_query(self, query: GetUserQuery) -> Query:
        specified_query = self.repository_provider.get(User).table
        specified_query = specified_query.filter(User.Name == query.request.Name)
        return specified_query

    def specify(self, query: GetUserQuery) -> Query:
        data_query = self.__specified_query(query=query)
        return data_query

    def count(self, query: GetUserQuery) -> Query:
        return self.__specified_query(query=query).count()
