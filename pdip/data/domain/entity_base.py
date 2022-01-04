from datetime import datetime


class EntityBase:

    def __init__(self,
                 Id: int = None,
                 CreatedByUserId: int = None,
                 CreationDate: datetime = None,
                 LastUpdatedUserId: int = None,
                 LastUpdatedDate: datetime = None,
                 IsDeleted: bool = None,
                 Comments: str = None,
                 # RowVersion: bytes = None,
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.Id = Id
        self.CreatedByUserId: int = CreatedByUserId
        self.CreationDate: datetime = CreationDate
        self.LastUpdatedUserId: int = LastUpdatedUserId
        self.LastUpdatedDate: datetime = LastUpdatedDate
        self.IsDeleted: bool = IsDeleted
        self.Comments: str = Comments
        # self.RowVersion: bytes = RowVersion
