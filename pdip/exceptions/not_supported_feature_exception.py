class NotSupportedFeatureException(Exception):
    def __init__(self, feature):
        super().__init__(f"{feature} feature not supported yet")
