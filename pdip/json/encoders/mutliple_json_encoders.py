import json


class MultipleJsonEncoders:
    """
    Combine multiple JSON encoders
    """

    def __init__(self, *encoders):
        self.encoders = encoders
        self.args = ()
        self.kwargs = {}

    def default(self, obj):
        for encoder in self.encoders:
            try:
                return encoder(*self.args, **self.kwargs).default(obj)
            except TypeError:
                pass
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        enc = json.JSONEncoder(*args, **kwargs)
        enc.default = self.default
        return enc
