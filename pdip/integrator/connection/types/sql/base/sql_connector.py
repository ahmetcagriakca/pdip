from abc import abstractmethod


class SqlConnector(object):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def get_engine_connection_url(self):
        pass

    @abstractmethod
    def get_engine(self):
        pass

    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def execute_many(self, query, data):
        pass
