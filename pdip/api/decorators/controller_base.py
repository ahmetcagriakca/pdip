def controller(namespace=None, route=None):
    def decorate(cls):
        cls.namespace = namespace
        cls.route = route
        return cls

    return decorate
