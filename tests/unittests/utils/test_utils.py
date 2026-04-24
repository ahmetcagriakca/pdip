import os
from typing import List
from unittest import TestCase

from pdip.configuration.models.database import DatabaseConfig
from pdip.utils import Utils
from pdip.utils.module_finder import ModuleFinder
from pdip.utils.type_checker import TypeChecker


class ClassTest:
    pass


class TestUtils(TestCase):
    def tearDown(self):
        return super().tearDown()

    def test_process_info(self):
        assert Utils.get_process_info().startswith('MainProcess')

    def test_path_split(self):
        path_splitted = Utils.path_split('test/test')
        assert path_splitted == ['test', 'test']
        assert Utils.path_split('test\\test') == ['test', 'test']

    def test_replace_last(self):
        replaced = Utils.replace_last(
            source_string='TestConfig', replace_what='Config', replace_with='')
        assert replaced == 'Test'

    def test_to_snake_case(self):
        replaced = Utils.to_snake_case(name='TestConfig')
        assert replaced == 'test_config'

    def test_get_config_name(self):
        replaced_name,result = Utils.get_config_name(class_name='TestConfig')
        assert replaced_name == 'Test'
        assert result == 'test'

    def test_TypeChecker_is_class(self):
        result = TypeChecker().is_class(int)
        assert not result
        result = TypeChecker().is_class(ClassTest)
        assert result

    def test_TypeChecker_is_primitive(self):
        result = TypeChecker().is_primitive(int)
        assert result
        result = TypeChecker().is_primitive(ClassTest)
        assert not result

    def test_TypeChecker_is_generic(self):
        result = TypeChecker().is_generic(List[int])
        assert result

    # def test_TypeChecker_is_base_generic():
    #     result = TypeChecker().is_base_generic(Union[str, bytes])
    #     assert result

    def test_ModuleFinder_get_module(self):
        root_directory = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__))))
        with self.assertRaises(Exception) as execinfo:
            result = ModuleFinder(root_directory).get_module("")
        assert execinfo.exception.args[0] == "Modules not found"
        assert str(execinfo.exception) == "Modules not found"


class UtilsGetPropertyNameSnakeCases(TestCase):
    def test_get_property_name_returns_original_and_snake_cased(self):
        # Arrange / Act
        original, snaked = Utils.get_property_name("CamelCaseProperty")

        # Assert
        self.assertEqual(original, "CamelCaseProperty")
        self.assertEqual(snaked, "camel_case_property")


class UtilsGetConnectionStringBuildsDriverUrl(TestCase):
    def test_sqlite_with_empty_host_produces_memory_style_url(self):
        # Arrange
        db = DatabaseConfig(type="SQLITE", host="")

        # Act
        cs = Utils.get_connection_string(db)

        # Assert
        self.assertEqual(cs, "sqlite://")

    def test_sqlite_with_host_uses_host_as_db_path(self):
        # Arrange
        db = DatabaseConfig(type="SQLITE", host="app.db")

        # Act
        cs = Utils.get_connection_string(db)

        # Assert
        self.assertEqual(cs, "sqlite:///app.db")

    def test_sqlite_with_host_and_root_directory_joins_path(self):
        # Arrange
        db = DatabaseConfig(type="SQLITE", host="app.db")

        # Act
        cs = Utils.get_connection_string(db, root_directory="/var/data")

        # Assert
        # Four slashes because the helper prepends ``/`` before joining
        # with an already-absolute root_directory.
        self.assertEqual(cs, "sqlite:////var/data/app.db")

    def test_mssql_connection_string_includes_driver_query_param(self):
        # Arrange
        db = DatabaseConfig(
            type="MSSQL", driver="ODBC Driver 17",
            host="h", port=1433, database="d",
            user="u", password="p",
        )

        # Act
        cs = Utils.get_connection_string(db)

        # Assert
        self.assertEqual(
            cs,
            "mssql+pyodbc://u:p@h:1433/d?driver=ODBC+Driver+17",
        )

    def test_postgresql_connection_string_has_no_driver_query(self):
        # Arrange
        db = DatabaseConfig(
            type="POSTGRESQL", driver="",
            host="pg", port=5432, database="app",
            user="u", password="p",
        )

        # Act
        cs = Utils.get_connection_string(db)

        # Assert
        self.assertEqual(cs, "postgresql://u:p@pg:5432/app")
