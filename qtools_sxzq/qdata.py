from dataclasses import dataclass
from typing import Literal, Union, NoReturn
import pandas as pd
from transmatrix.data_api import create_factor_table, Database, DataView2d, save_factor


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
    """

    :param df: any pd.Dataframe, DOES NOT require contains columns with ["code", "datetime"]
    :param db_name:
    :param table_name:
    :return:
    """
    db = Database(db_name)
    column_info = db.get_column_info_from_df(df)
    if table_name not in db.show_tables():
        db.create_table(table_name, column_info=column_info)
    db.insert_values(table_name, df)
    return 0


def save_data3d_to_db_with_key_as_code(
        data_3d: dict[str, Union[pd.DataFrame, DataView2d]],
        table_name: str,
        using_index_as_datetime: bool = True,
        datetime_name: str = "datetime",
):
    """

    :param data_3d: for each (key, value) pair in data_3d:
                    the key will be inserted to value and renamed as "code".
                    the value must be pd.DataFrame or DataView2d.
                    the value must be one of the following structure:
                        1. datetime-like index + fields. in this case, set using_index_as_datetime = True, and argument
                           datetime_name won't work.
                        2. [datetime_name] + fields. in this case, set using_index_as_datetime = False, and provide
                           argument datetime_name, the corresponding column will be used as datetime.
    :param table_name: the table to save
    :param using_index_as_datetime: if true, make sure the type of index of the dataframe is datetime.
                                    else the following argument datetime_name must be provided.
    :param datetime_name: the name of the datetime column.
    :return:
    """
    if len(data_3d) > 0:
        data = []
        for code, factor in data_3d.items():
            if isinstance(factor, DataView2d):
                _data = factor.to_dataframe()
            elif isinstance(factor, pd.DataFrame):
                _data = factor
            else:
                raise TypeError(f"Invalid data type: {type(factor)}, supported type: DataView2d, pd.DataFrame.")
            _data.insert(loc=0, column="code", value=code)
            data.append(_data)
        data = pd.concat(data, axis=0, ignore_index=False)
        if using_index_as_datetime:
            datetime_name = data.index.name or "index"
            data.reset_index(inplace=True)
        data.rename(columns={datetime_name: "datetime"}, inplace=True)
        create_factor_table(table_name)
        save_factor(table_name=table_name, data=data)
    else:
        print(f"No data available for saving")
