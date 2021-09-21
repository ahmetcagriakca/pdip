import os
from pdi.utils.module_finder import ModuleFinder
from typing import List, Union
from pdi.utils.type_checker import TypeChecker
from pdi.utils import Utils
from unittest import TestCase


def test_process_info():
    assert Utils.get_process_info().startswith('MainProcess')


def test_path_split():
    path_splitted = Utils.path_split('test/test')
    assert path_splitted == ['test', 'test']
    assert Utils.path_split('test\\test') == ['test', 'test']


def test_replace_last():
    replaced = Utils.replace_last(
        source_string='TestConfig', replace_what='Config', replace_with='')
    assert replaced == 'Test'


def test_to_snake_case():
    replaced = Utils.to_snake_case(name='TestConfig')
    assert replaced == 'test_config'


def test_get_config_name():
    replaced = Utils.get_config_name(class_name='TestConfig')
    assert replaced == 'TEST'


class ClassTest:
    pass


def test_TypeChecker_is_class():
    result = TypeChecker().is_class(int)
    assert not result
    result = TypeChecker().is_class(ClassTest)
    assert result


def test_TypeChecker_is_primitive():
    result = TypeChecker().is_primitive(int)
    assert result
    result = TypeChecker().is_primitive(ClassTest)
    assert not result


def test_TypeChecker_is_generic():
    result = TypeChecker().is_generic(List[int])
    assert result


# def test_TypeChecker_is_base_generic():
#     result = TypeChecker().is_base_generic(Union[str, bytes])
#     assert result

def test_ModuleFinder_get_module():
    import pytest
    root_directory = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__))))
    with pytest.raises(Exception) as execinfo:
        result = ModuleFinder(root_directory).get_module("")
    assert execinfo.value.args[0] == "Modules not found"
    assert str(execinfo.value) == "Modules not found"
