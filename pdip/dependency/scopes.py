class IDependency:
    pass


class IScoped(IDependency):
    pass

    def __del__(self):
        pass


class ISingleton(IDependency):
    pass
