from datetime import datetime

from ...data import EntityBase

class ConfigParameter(EntityBase):
    
    def __init__(self,
                 Name: str = None,
                 Type: str = None,
                 Value: str = None,
                 Description: str = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Name: str = Name
        self.Type: str = Type
        self.Value: str = Value
        self.Description: str = Description