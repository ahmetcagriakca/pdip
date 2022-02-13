from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ConnectionColumnBase:
    Name: str = None
    Type: Optional[str] = None
    Nullable: Optional[str] = None
