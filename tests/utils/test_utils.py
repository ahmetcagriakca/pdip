import os
from pdip.utils.module_finder import ModuleFinder
from typing import List, Union
from pdip.utils.type_checker import TypeChecker
from pdip.utils import Utils
from unittest import TestCase

class ClassTest:
    pass

class TestUtils(TestCase):
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
        replaced = Utils.get_config_name(class_name='TestConfig')
        assert replaced == 'TEST'




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
