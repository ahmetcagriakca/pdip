from injector import inject
from sqlalchemy import desc, text

from ...api.request_parameter import OrderByParameter
from ...dependency import IScoped
from ...utils import ModuleFinder


class OrderBySpecification(IScoped):
    @inject
    def __init__(self, module_finder: ModuleFinder):
        self.default_order = 'asc'
        self.module_finder = module_finder

    def specify(self, order_by_parameter: OrderByParameter):

        if not hasattr(order_by_parameter, 'OrderBy') and hasattr(order_by_parameter, 'Order'):
            return None
        if order_by_parameter.OrderBy is not None and order_by_parameter.OrderBy != '':
            if order_by_parameter.Order is None or order_by_parameter.Order == '':
                order = self.default_order
            else:
                order = order_by_parameter.Order
            split = order_by_parameter.OrderBy.split(".")
            if len(split) == 1:
                return text(f'"{order_by_parameter.OrderBy}" {order_by_parameter.Order}')
            if len(split) == 2:
                class_name, attr_name = split
                module = self.module_finder.get_module(class_name)
                class_type = getattr(module, class_name)
                order_by = getattr(class_type, attr_name)

                if order == 'desc':
                    return desc(order_by)
                else:
                    return order_by
            else:
                return None
