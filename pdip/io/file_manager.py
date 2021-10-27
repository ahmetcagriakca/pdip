import os

from injector import inject

from ..configuration.models.application import ApplicationConfig
from ..dependency import IScoped


class FileManager(IScoped):
    @inject
    def __init__(self,
                 application_config: ApplicationConfig
                 ):
        self.application_config = application_config

    def check_path_exist(self, folder, file):
        path = os.path.join(self.application_config.root_directory, folder, file)
        return os.path.exists(path)

    def create_folder_if_not_exist(self, folder):
        os.path.join(self.application_config.root_directory, folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def create_file(self, folder, file_name, content, file_extension='.py'):
        self.create_folder_if_not_exist(folder)
        file_path = '/'.join([folder, f'{file_name}{file_extension}'])

        with open(file_path, "w") as outfile:
            outfile.write(content.strip() + '\n')
