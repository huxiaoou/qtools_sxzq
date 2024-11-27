from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CDataDescribe:
    db_name: str
    table_name: str
    codes: list[str]
    fields: list[str]
    lag: int
    data_view_type: Literal["data3d", "data2d", "struct-array"]

    def to_args(self) -> list:
        return [
            self.db_name,
            self.table_name,
            self.codes,
            ".".join(self.fields),
            self.lag,
            self.data_view_type
        ]
