from abc import abstractmethod

from ....dependency import IScoped


class DatabaseConnector(IScoped):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def execute_many(self, query, data):
        pass

    @abstractmethod
    def get_target_query_indexer(self):
        pass

    @abstractmethod
    def get_truncate_query(self, schema, table):
        count_query = f'TRUNCATE TABLE "{schema}"."{table}"'
        return count_query

    @abstractmethod
    def get_table_count_query(self, query):
        count_query = f"SELECT COUNT(*) as \"COUNT\"  FROM ({query})  as count_table"
        return count_query

    @abstractmethod
    def get_table_select_query(self, selected_rows, schema, table):
        return f'SELECT {selected_rows} FROM "{schema}"."{table}"'

    @abstractmethod
    def get_table_data_query(self, query):
        return f"SELECT * FROM ({query}) base_query"

    @abstractmethod
    def get_table_data_with_paging_query(self, query, order_row, start, end):
        return f"WITH TEMP_INTEGRATION AS(SELECT ordered_query.*,ROW_NUMBER() OVER ( order by \"{order_row}\") row_number FROM ({query}) ordered_query) SELECT * FROM TEMP_INTEGRATION WHERE row_number >= {start} AND row_number < {end}"

    @abstractmethod
    def prepare_data(self, data):
        return data
