from dataclasses import dataclass
from typing import Literal, NoReturn
import pandas as pd
from transmatrix.data_api import create_factor_table, Database


@dataclass
class CDataDescriptor:
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
            ",".join(self.fields),
            self.lag,
            self.data_view_type
        ]

    def set_lag(self, lag: int) -> NoReturn:
        self.lag = lag


def save_df_to_db(df: pd.DataFrame, db_name: str, table_name: str):
    db = Database(db_name)
    column_info = db.get_column_info_from_df(df)
    if table_name not in db.show_tables():
        db.create_table(table_name, column_info=column_info)
    db.insert_values(table_name, df)
    return 0
