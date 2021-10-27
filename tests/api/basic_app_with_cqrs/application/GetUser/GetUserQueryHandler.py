from injector import inject

from pdip.cqrs import IQueryHandler
from pdip.dependency import IScoped
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserMapping import GetUserMapping
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserQuery import GetUserQuery
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserResponse import GetUserResponse
from tests.api.basic_app_with_cqrs.application.GetUser.GetUserSpecifications import GetUserSpecifications


class GetUserQueryHandler(IQueryHandler[GetUserQuery], IScoped):
    @inject
    def __init__(self,
                 specifications: GetUserSpecifications):
        self.specifications = specifications

    def handle(self, query: GetUserQuery) -> GetUserResponse:
        result = GetUserResponse()
        data_query = self.specifications.specify(query=query)
        result.Data = GetUserMapping.to_dto(data_query.first())
        return result
