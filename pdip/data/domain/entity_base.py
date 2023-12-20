from datetime import datetime
from uuid import UUID


class EntityBase:

    def __init__(self,
                 Id: UUID = None,
                 CreateUserId: UUID = None,
                 CreateUserTime: datetime = None,
                 UpdateUserId: UUID = None,
                 UpdateUserTime: datetime = None,
                 TenantId: UUID = None,
                 GcRecId: UUID = None,
                 # RowVersion: bytes = None,
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.Id = Id
        self.CreateUserId: int = CreateUserId
        self.CreateUserTime: datetime = CreateUserTime
        self.UpdateUserId: int = UpdateUserId
        self.UpdateUserTime: datetime = UpdateUserTime
        self.TenantId: bool = TenantId
        self.GcRecId: bool = GcRecId
        # self.RowVersion: bytes = RowVersion
