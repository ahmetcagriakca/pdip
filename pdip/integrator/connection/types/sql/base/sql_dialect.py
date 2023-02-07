from abc import abstractmethod


class SqlDialect:
    def __init__(self):
        pass

    @property
    @abstractmethod
    def indexer(self) -> str:
        pass

    @property
    @abstractmethod
    def quotation_mark(self) -> str:
        pass

    @abstractmethod
    def mark_to_object(self, o) -> str:
        pass

    @abstractmethod
    def get_table_count_query(self, schema, table):
        pass

    @abstractmethod
    def get_count_query(self, query):
        pass

    @abstractmethod
    def get_select_query(self, query):
        pass

    @abstractmethod
    def get_table_select_query(self, schema, table, selected_rows):
        pass

    @abstractmethod
    def get_paging_query(self, query, start, end):
        pass

    @abstractmethod
    def prepare_select_query(self, schema, table, columns=None):
        pass

    @abstractmethod
    def generate_insert_query(self, schema, table, columns_query, values_query):
        pass

    @abstractmethod
    def get_insert_query(self, schema, table, columns_query, values_query):
        pass

    @abstractmethod
    def get_insert_values_query(self, schema, table, values_query):
        pass

    @abstractmethod
    def get_create_table_query(self, schema, table, columns, if_exists=None):
        pass

    @abstractmethod
    def get_drop_table_query(self, schema, table, if_not_exists=None):
        pass

    @abstractmethod
    def get_truncate_table_query(self, schema, table):
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

