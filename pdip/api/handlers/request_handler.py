from flask import request, Response
from injector import inject

from ...configuration.models.api import ApiConfig
from ...data import RepositoryProvider
from ...dependency import ISingleton


class RequestHandler(ISingleton):
    @inject
    def __init__(self,
                 api_config: ApiConfig,
                 repository_provider: RepositoryProvider
                 ):
        self.repository_provider = repository_provider
        self.api_config = api_config

    def set_headers(self, response):
        white_origin = None
        if self.api_config.origins is not None:
            white_origin = self.api_config.origins.split(',')
        if (white_origin is not None and ((len(white_origin) == 1 and white_origin[0] == '*') or (
                ('Origin' in request.headers and request.headers['Origin'] in white_origin)))):
            response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
            # response.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
            # response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Server'] = ''
        return response

    def after_request(self, response: Response):
        response = self.set_headers(response=response)
        self.repository_provider.close()
        return response
