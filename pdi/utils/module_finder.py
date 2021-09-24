import glob
import importlib
import os
import sys

from . import Utils


class ModuleFinder:
    def __init__(self, root_directory: str):
        self.root_directory = root_directory
        self.running_directory=  os.getcwd()
        self.modules = []
        self.get_indexes = lambda module_name, modules: [i for (module, i) in zip(modules, range(len(modules))) if
                                                         module["module_name"] == module_name]
        self.find_all_modules(self.root_directory)

    def get_file_name(self, file):
        file_splits = Utils.path_split(file)
        file_name = file_splits[len(file_splits) - 1]
        file_name_without_extension = file_name[0:(len(file_name) - 3)]
        return file_name_without_extension

    def find_sub_folders(self, directory):
        for name in os.listdir(directory):
            sub_folder = os.path.join(directory, name)
            if os.path.isdir(sub_folder) and not name.startswith('.') and not name.startswith('_') and name != 'files':
                yield sub_folder
                for folder in self.find_sub_folders(sub_folder):
                    yield folder

    def find_all_modules(self, folder):
        folder_path = os.path.join(folder)
        folders = self.find_sub_folders(folder_path)
        for folder in folders:
            files = glob.glob(folder + '/*.py')
            for file in files:
                module = {}
                file_name = self.get_file_name(file=file)
                module_path = os.path.join(folder, file_name)
                module_address = module_path.replace(self.root_directory, '')[
                    1:].replace('\\', '.').replace('/', '.')
                module_base_address=''
                if(self.running_directory!= self.root_directory):
                    module_base_address = self.root_directory.replace(self.running_directory, '')[
                        1:].replace('\\', '.').replace('/', '.')+'.'
                module['module_name'] = file_name
                module['file_path'] = file
                module['module_path'] = module_path
                module['module_address'] = module_address
                module['module_base_address'] = module_base_address
                self.modules.append(module)

    def import_modules_by_name_ends_with(self, name):
        for module in self.modules:
            if (module['module_name'].endswith(name)):
                module_address = module["module_address"]
                if module_address not in sys.modules:
                    importlib.import_module(module_address)

    # checking existing module for duplicate importing
    def check_module_existing(self, module_address: str):
        for k in sys.modules.keys():
            if k.endswith(module_address):
                return True
        else:
            return False

    def import_modules(self, included_modules=None, excluded_modules=None):
        for module in self.modules:
            root_path_dir = os.path.join(
                self.root_directory, '')
            base_module_folder = \
                module['module_path'].replace(root_path_dir, '')
            if ((excluded_modules is None) or (
                    not any(base_module_folder.startswith(item) for item in excluded_modules))) and (
                    (included_modules is None) or (included_modules is not None and any(
                        base_module_folder.startswith(item) for item in included_modules))):
                module_address = module["module_address"]

                if not self.check_module_existing(module_address=module_address):
                    try:
                        importlib.import_module(module_address)
                    except ModuleNotFoundError as ex:
                        module_base_address = module["module_base_address"]
                        importlib.import_module(module_base_address+module_address)

    def get_module(self, name_of_module):
        indexes = self.get_indexes(name_of_module, self.modules)
        if indexes is not None and len(indexes) > 0:
            if len(indexes) == 1:
                module_address = self.modules[indexes[0]]["module_address"]
                module = importlib.import_module(module_address)
                return module
        else:
            raise Exception("Modules not found")
