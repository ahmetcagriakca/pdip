import re

from injector import inject

from .web_service_policy import WebServicePolicy
from ......dependency import IScoped


class WebServiceContext(IScoped):
    @inject
    def __init__(self,
                 policy: WebServicePolicy,
                 retry_count=3):
        self.connector: WebServicePolicy = policy.connector
        self.retry_count = retry_count
        self.default_retry = 1

    def connect(func):
        def inner(*args, **kwargs):
            try:
                args[0].connector.connect()
                return func(*args, **kwargs)
            finally:
                args[0].connector.disconnect()

        return inner

    @connect
    def prepare_request_auth(self, request):
        request['Header']['userId'] = self.connector.config.BasicAuthentication.User
        request['Header']['password'] = self.connector.config.BasicAuthentication.User
        return request

    @connect
    def call_service(self, method, request):
        method = getattr(self.connector.client.service, method)
        result = method(request)
        return result

    @staticmethod
    def replace_regex(text, field, indexer):
        text = re.sub(r'\(:' + field + r'\b', f'({indexer}', text)
        text = re.sub(r':' + field + r'\b\)', f'{indexer})', text)
        text = re.sub(r':' + field + r'\b', f'{indexer}', text)
        return text

    def prepare_request_body(self, column_rows, request_body):
        body = request_body
        for column_row in column_rows:
            index = column_rows.index(column_row)
            indexer = self.connector.get_target_query_indexer().format(index=index)
            body = self.replace_regex(body, column_row[0], indexer)
        return body