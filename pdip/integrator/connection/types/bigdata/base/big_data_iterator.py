from .big_data_connector import BigDataConnector


class BigDataIterator:

    def __init__(self, connector: BigDataConnector, query, excluded_columns=None, limit: int = 0, start: int = 0) -> None:
        self.start = start
        self.offset = 0
        if self.start is not None:
            self.offset = start
        self.excluded_columns = excluded_columns
        self.connector = connector
        self.query = query
        self.cursor = None
        self.limit = limit
        self.excluded_columns = excluded_columns
        self.columns = None
        self.is_finished = False

    def _initialize(self):
        if self.connector.cursor is None:
            self.is_finished = False
            self.connector.connect()
            self.cursor = self.connector.cursor
            self.cursor.execute(self.query)
            self.columns = [column[0] for column in self.cursor.description if
                            self.excluded_columns is None or column[0] not in self.excluded_columns]

    def __iter__(self) -> any:  # this makes the class an Iterable
        return self

    def __next__(self) -> str:
        self._initialize()
        if self.is_finished:
            raise StopIteration

        if self.limit is not None and self.limit > 0:
            data = self.cursor.fetchmany(self.limit)
            if len(data) <= 0:
                self.is_finished = True
                self.connector.disconnect()
                raise StopIteration
            self.offset += len(data)
        else:
            data = self.cursor.fetchall()
            self.is_finished = True
            self.connector.disconnect()
            self.offsetszddssssss += len(data)
        results = [dict(zip(self.columns, t)) for t in data]
        return results
