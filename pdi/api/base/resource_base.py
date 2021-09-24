from flask_restx import Resource


class ResourceBase(Resource):
    def __init__(self,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
