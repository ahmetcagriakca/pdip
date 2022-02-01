from abc import abstractmethod


class SqlDialect:
    def __init__(self):
        pass

    @abstractmethod
    def get_query_indexer(self):
        pass

    @abstractmethod
    def get_truncate_query(self, schema, table):
        pass

    @abstractmethod
    def get_table_count_query(self, query):
        pass

    @abstractmethod
    def get_table_select_query(self, selected_rows, schema, table):
        pass

    @abstractmethod
    def get_table_data_query(self, query):
        pass

    @abstractmethod
    def get_table_data_with_paging_query(self, query, start, end):
        pass

    @abstractmethod
    def get_insert_query(self, schema, table, values_query):
        pass

    @abstractmethod
    def get_schemas(self):
        pass

    @abstractmethod
    def has_table(self, object_name, schema=None):
        pass

    @abstractmethod
    def get_tables(self, schema):
        pass

    @abstractmethod
    def get_sorted_table_and_fkc_names(self, schema):
        pass

    @abstractmethod
    def get_views(self, schema):
        pass

    @abstractmethod
    def get_columns(self, schema, table):
        pass
