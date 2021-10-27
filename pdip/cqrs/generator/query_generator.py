from .domain.dao_generate_config import DaoGenerateConfig
from .domain.generator import Generator
from .domain.query_generate_config import QueryGenerateConfig
from ...configuration.models.application import ApplicationConfig
from ...io.file_manager import FileManager
from ...io.folder_manager import FolderManager
from ...utils import ModuleFinder


class QueryGenerator(Generator):
    def __init__(self,
                 application_config: ApplicationConfig,
                 module_finder: ModuleFinder,
                 folder_manager: FolderManager,
                 file_manager: FileManager):
        self.file_manager = file_manager
        self.folder_manager = folder_manager
        self.application_config = application_config
        self.module_finder = module_finder

    def generate(self, generate_config: QueryGenerateConfig):

        query_folder_path = "/".join([generate_config.base_directory, generate_config.domain, generate_config.name])

        self.folder_manager.start_copy(query_folder_path)

        self.__create_request_file(query_name=generate_config.name, query_folder_path=query_folder_path,
                                   has_paging=generate_config.has_paging)
        self.__create_dto_file(query_name=generate_config.name, query_folder_path=query_folder_path)
        self.__create_response_file(query_name=generate_config.name, query_folder_path=query_folder_path,
                                    is_list=generate_config.is_list, has_paging=generate_config.has_paging)
        self.__create_query_file(query_name=generate_config.name, query_folder_path=query_folder_path)
        self.__create_specifications_file(query_name=generate_config.name, query_folder_path=query_folder_path,
                                          dao=generate_config.dao, is_list=generate_config.is_list,
                                          has_paging=generate_config.has_paging)

        self.__create_mapping_file(query_name=generate_config.name, query_folder_path=query_folder_path,
                                   dao=generate_config.dao)
        self.__create_query_handler_file(query_name=generate_config.name, query_folder_path=query_folder_path,
                                         dao=generate_config.dao, is_list=generate_config.is_list,
                                         has_paging=generate_config.has_paging)

    def __create_query_file(self, query_name: str, query_folder_path: str):
        file_name = f"{query_name}Query"
        base_namespace = query_folder_path.replace('/', '.')
        request_namespace = f'from {base_namespace}.{query_name}Request import {query_name}Request'
        response_namespace = f'from {base_namespace}.{query_name}Response import {query_name}Response'
        request_attr = f'request: {query_name}Request = None'
        content = \
            f'''from dataclasses import dataclass
from infrastructure.cqrs.IQuery import IQuery
{request_namespace}
{response_namespace}


@dataclass
class {query_name}Query(IQuery[{query_name}Response]):
    {request_attr}
        '''
        self.file_manager.create_file(folder=query_folder_path, file_name=file_name, content=content)

    def __create_request_file(self, query_name: str, query_folder_path: str,
                              has_paging: bool = True, ):
        file_name = f"{query_name}Request"
        paging_parent = "(PagingParameter, OrderByParameter)" if has_paging else ""
        content = \
            f'''
from domain.common.decorators.requestclass import requestclass


@requestclass
class {query_name}Request{paging_parent}:
    # TODO:Request attributes
    pass
    '''
        self.file_manager.create_file(folder=query_folder_path, file_name=file_name,
                                      content=content)

    def __create_dto_file(self, query_name: str, query_folder_path: str):
        file_name = f"{query_name}Dto"

        content = \
            f'''
from domain.common.decorators.dtoclass import dtoclass


@dtoclass
class {query_name}Dto:
    # TODO:Dto attributes
    pass
    '''
        self.file_manager.create_file(folder=query_folder_path, file_name=file_name,
                                      content=content)

    def __create_response_file(self, query_name: str, query_folder_path: str, is_list: bool, has_paging: bool):
        query_request_file_name = f"{query_name}Response"

        base_namespace = query_folder_path.replace('/', '.')
        dto_namespace = f'from {base_namespace}.{query_name}Dto import {query_name}Dto'
        if is_list:
            if has_paging:
                attributes = \
                    f'''    Data: List[{query_name}Dto] = None
    PageNumber: int = None
    PageSize: int = None
    Count: int = None'''
            else:
                attributes = f"\tData: List[{query_name}Dto] = None"
        else:
            attributes = f"\tData: {query_name}Dto = None"
        content = \
            f'''
from typing import List
from domain.common.decorators.responseclass import responseclass
{dto_namespace}


@responseclass
class {query_name}Response:
{attributes}
    '''
        self.file_manager.create_file(folder=query_folder_path, file_name=query_request_file_name,
                                      content=content)

    def __create_specifications_file(self, query_name: str, query_folder_path: str, dao: DaoGenerateConfig,
                                     is_list: bool = True,
                                     has_paging: bool = True):
        file_name = f"{query_name}Specifications"

        base_namespace = query_folder_path.replace('/', '.')
        query_namespace = f'from {base_namespace}.{query_name}Query import {query_name}Query'
        orderable = {}
        pageable = {}
        if is_list:
            if has_paging:
                orderable[
                    'Namespace'] = f'from domain.common.specifications.OrderBySpecification import OrderBySpecification\n'
                pageable[
                    'Namespace'] = f'from domain.common.specifications.PagingSpecification import PagingSpecification\n'
        content = ''
        content += 'from injector import inject\n'
        content += 'from sqlalchemy.orm import Query\n'
        content += 'from infrastructure.dependency import IScoped\n'
        content += 'from infrastructure.data.RepositoryProvider import RepositoryProvider\n'
        content += f'{dao.namespace}\n'

        content += f'{query_namespace}\n'
        if has_paging:
            content += orderable['Namespace']
            content += '\n'
            content += pageable['Namespace']
            content += '\n'
        content += '\n'
        content += \
            f'''
class {query_name}Specifications(IScoped):
    @inject
    def __init__(self,\n'''
        content += f'''                 repository_provider: RepositoryProvider,\n'''
        if has_paging:
            content += f'''                 order_by_specification: OrderBySpecification,\n'''
            content += f'''                 paging_specification: PagingSpecification,\n'''
        content += f'''                 ):\n'''

        content += f'''        self.repository_provider = repository_provider\n'''
        if has_paging:
            content += f'''        self.paging_specification = paging_specification\n'''
            content += f'''        self.order_by_specification = order_by_specification\n'''
        else:
            content += f'''        \n'''
        content += \
            f'''
    def __specified_query(self, query: {query_name}Query) -> Query:
        repository = self.repository_provider.get({dao.name})
        specified_query = repository.table 
        # TODO:specify query
        return specified_query
        
    def specify(self, query: {query_name}Query) -> Query:
    
        data_query = self.__specified_query(query=query)\n'''
        if has_paging:
            content += f'''
        order_by = self.order_by_specification.specify(order_by_parameter=query.request)
        if order_by is not None:
            data_query = data_query.order_by(order_by)

        page_size, offset = self.paging_specification.specify(paging_parameter=query.request)
        if page_size is not None:
            data_query = data_query.limit(page_size)
        if offset is not None:
            data_query = data_query.offset(offset)\n'''
        content += '''        return data_query\n'''

        content += f'''
    def count(self, query: {query_name}Query) -> Query:
        return self.__specified_query(query=query).count()
    '''
        self.file_manager.create_file(folder=query_folder_path, file_name=file_name,
                                      content=content)

    def __create_mapping_file(self, query_name: str, query_folder_path: str, dao: DaoGenerateConfig):
        file_name = f"{query_name}Mapping"
        base_namespace = query_folder_path.replace('/', '.')
        dto_namespace = f'from {base_namespace}.{query_name}Dto import {query_name}Dto'
        content = \
            f'''
from typing import List
{dto_namespace}
{dao.namespace}


class {query_name}Mapping:
    @classmethod
    def to_dto(cls, entity: {dao.name}) -> {query_name}Dto:
        dto = {query_name}Dto()
        return dto

    @classmethod
    def to_dtos(cls, entities: List[{dao.name}]) -> List[{query_name}Dto]:
        result: List[{query_name}Dto] = []
        for entity in entities:
            dto = cls.to_dto(entity=entity)
            result.append(dto)
        return result'''
        self.file_manager.create_file(folder=query_folder_path, file_name=file_name,
                                      content=content)

    def __create_query_handler_file(self, query_name: str, query_folder_path: str, dao: DaoGenerateConfig,
                                    is_list: bool = True, has_paging: bool = True):
        file_name = f"{query_name}QueryHandler"
        base_namespace = query_folder_path.replace('/', '.')
        query_namespace = f'from {base_namespace}.{query_name}Query import {query_name}Query'
        mapping_namespace = f'from {base_namespace}.{query_name}Mapping import {query_name}Mapping'
        request_namespace = f'from {base_namespace}.{query_name}Request import {query_name}Request'
        response_namespace = f'from {base_namespace}.{query_name}Response import {query_name}Response'
        specifications_namespace = f'from {base_namespace}.{query_name}Specifications import {query_name}Specifications'
        content = \
            f'''
from injector import inject
{mapping_namespace}
{query_namespace}
{response_namespace}
{specifications_namespace}
from infrastructure.cqrs.IQueryHandler import IQueryHandler
from infrastructure.dependency import IScoped


class {query_name}QueryHandler(IQueryHandler[{query_name}Query], IScoped):
    @inject
    def __init__(self,
                 specifications: {query_name}Specifications):
        self.specifications = specifications

    def handle(self, query: {query_name}Query) -> {query_name}Response:
        result = {query_name}Response()\n'''
        if has_paging:
            content += f'''
        result.Count = self.specifications.count(query=query)

        result.PageNumber = query.request.PageNumber
        result.PageSize = query.request.PageSize\n'''

        content += \
            f'''        data_query = self.specifications.specify(query=query)\n'''
        if is_list:
            content += \
                f'''        result.Data = {query_name}Mapping.to_dtos(data_query)\n'''
        else:
            content += \
                f'''        result.Data = {query_name}Mapping.to_dto(data_query)\n'''
        content += \
            f'''        return result\n'''
        self.file_manager.create_file(folder=query_folder_path, file_name=file_name,
                                      content=content)
