from injector import inject

from ...api.request_parameter import PagingParameter
from ...dependency import IScoped


class PagingSpecification(IScoped):
    @inject
    def __init__(self):
        self.default_page_size = 10
        self.default_page_number = 1
        self.default_offset = 0
        self.min_page_size = 5
        self.max_page_size = 200
        pass

    def specify(self, paging_parameter: PagingParameter):
        if not hasattr(paging_parameter, 'PageSize') and hasattr(paging_parameter, 'PageNumber'):
            return None, None
        if paging_parameter.PageSize is None or paging_parameter.PageSize < self.min_page_size or paging_parameter.PageSize > self.max_page_size:
            page_size = self.default_page_size
        else:
            page_size = paging_parameter.PageSize
        if paging_parameter.PageNumber is None or paging_parameter.PageNumber < self.default_page_number:
            page_number = self.default_page_number
        else:
            page_number = paging_parameter.PageNumber
        offset = (page_number - 1) * page_size
        if offset is None or offset < self.default_offset:
            offset = self.default_offset
        return page_size, offset
