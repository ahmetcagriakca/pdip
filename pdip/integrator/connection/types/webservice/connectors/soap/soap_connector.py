from zeep import Client

from ...base.web_service_connector import WebServiceConnector
from .....domain.webservice.base import WebServiceConnectionConfiguration


class SoapConnector(WebServiceConnector):
    def __init__(self, config: WebServiceConnectionConfiguration):
        self.config: WebServiceConnectionConfiguration = config
        if config.Server.Port is not None:
            url = f'{config.Server.Host}:{config.Server.Port}{config.Soap.Wsdl}'
        else:
            url = f'{config.Server.Host}{config.Soap.Wsdl}'

        if config.Ssl:
            url = 'https://' + url
        else:
            url = 'http://' + url
        self.wsdl_url = url

        self.client: Client = None

    def connect(self):
        self.client = Client(self.wsdl_url)

    def disconnect(self):
        try:
            if self.client is not None:
                del self.client

        except Exception:
            pass

    def execute_many(self, query, data):
        self.cursor.fast_executemany = True
        try:
            self.cursor.executemany(query, data)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as error:
            try:
                self.connection.rollback()
                self.cursor.fast_executemany = False
                self.cursor.executemany(query, data)
                self.connection.commit()
                return self.cursor.rowcount
            except Exception as error:
                self.connection.rollback()
                self.cursor.close()
                raise

    def get_target_query_indexer(self):
        indexer = '?'
        return indexer

    def prepare_data(self, data):
        # if data is not None and isinstance(data, str):
        #     data = data\
        #         .replace("ı", "i")\
        #         .replace("ş", "s")\
        #         .replace("ğ", "g")\
        #         .replace("İ", "I")\
        #         .replace("Ş","S")\
        #         .replace("Ğ", "G")
        return data
