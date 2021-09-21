from multiprocessing.process import current_process
import os
import re


class Utils:

    @staticmethod
    def replace_last(source_string, replace_what, replace_with):
        head, _sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    @staticmethod
    def to_snake_case(name):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('__([A-Z])', r'_\1', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower()

    @staticmethod
    def get_config_name(class_name):
        replace_what = 'Config'
        replace_with = ''
        replaced_name = Utils.replace_last(source_string=class_name, replace_what=replace_what,
                                           replace_with=replace_with)
        snaked_case = Utils.to_snake_case(replaced_name)
        result = snaked_case.upper()
        return result

    @staticmethod
    def path_split(path):
        splits = path.split('/')
        if len(splits) == 1:
            splits = path.split('\\')
        return splits

    @staticmethod
    def get_process_info():
        return f"{current_process().name} ({os.getpid()},{os.getppid()})"

    @staticmethod
    def get_connection_string(database_config):
        if database_config.driver is not None and database_config.driver != '':
            driver = database_config.driver.replace(' ', '+')
        driver_string = ''
        connection_type = ''
        if database_config.type == 'MSSQL':
            driver_string = f'?driver={driver}'
            connection_type = 'mssql+pyodbc'
        elif database_config.type == 'POSTGRESQL':
            connection_type = 'postgresql'
        connection_string = f'{connection_type}://{database_config.username}:{database_config.password}@{database_config.host}:{database_config.port}/{database_config.database}{driver_string}'
        return connection_string
