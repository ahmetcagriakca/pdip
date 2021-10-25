def controller(namespace=None, namespace_name=None, route=None):
    def decorate(cls):
        cls.namespace = namespace
        cls.namespace_name = namespace_name
        cls.route = route
        return cls

    return decorate
