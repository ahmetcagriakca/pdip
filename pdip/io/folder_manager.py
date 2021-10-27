import os
import shutil

from injector import inject

from ..configuration.models.application import ApplicationConfig
from ..dependency import IScoped


class FolderManager(IScoped):
    @inject
    def __init__(self,
                 application_config: ApplicationConfig
                 ):
        self.application_config = application_config

    def create_folder_if_not_exist(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

    def copytree(self, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    def get_old_folder_path(self, folder):

        if os.path.exists(folder + '_old'):
            return self.get_old_folder_path(folder + '1')
        else:
            return folder + '_old'

    def start_copy(self, folder):
        path = os.path.join(self.application_config.root_directory, folder)

        if os.path.exists(path):
            path_old = self.get_old_folder_path(path)
            self.create_folder_if_not_exist(path_old)
            self.copytree(path, path_old)
