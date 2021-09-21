class IDependency:
    pass


class IScoped(IDependency):
    pass

    def __init__(self):
        # print(f"{str(self)} constructed")
        pass

    def __del__(self):
        # print(f"{str(self)} deconstructed")
        pass


class ISingleton(IDependency):
    pass
