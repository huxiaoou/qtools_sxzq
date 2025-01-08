import argparse
from typing import Union
from qtools_sxzq.qwidgets import SFG
import pandas as pd


def parse_args():
    args_parser = argparse.ArgumentParser(description="A python script to view trans-quant database")
    args_parser.add_argument(
        "--lib",
        type=str,
        required=True,
        help="path for trans-quant database, like 'huxiaoou_private' or 'meta_data'",
    )
    args_parser.add_argument(
        "--table",
        type=str,
        required=True,
        help="table name in the database, like 'table_avlb' or 'future_bar_1day'",
    )
    args_parser.add_argument(
        "--vars",
        type=str,
        default=None,
        help="variables to fetch, separated by ',' like \"open,high,low,close\", "
             "if not provided then fetch all.",
    )
    args_parser.add_argument(
        "--where",
        type=str,
        default=None,
        help="conditions to filter, sql expressions "
             "like \"code = 'A9999_DCE'\" AND datetime >= '2024-10-01 09:00:00'",
    )
    args_parser.add_argument(
        "--sort",
        type=str,
        default=None,
        help="like 'datetime' or 'datetime,code'",
    )
    args_parser.add_argument(
        "--descending",
        default=False,
        action="store_true",
        help="sort data in descending order",
    )

    args_parser.add_argument("--head", type=int, default=0, help="integer, head lines to print")
    args_parser.add_argument("--tail", type=int, default=0, help="integer, tail lines to print")
    args_parser.add_argument(
        "--maxrows",
        type=int,
        default=0,
        help="integer, provide larger value to see more rows when print outcomes",
    )
    args_parser.add_argument(
        "--maxcols",
        type=int,
        default=0,
        help="integer, provide larger value to see more columns when print outcomes",
    )
    _args = args_parser.parse_args()
    return _args


def fetch(lib: str, table: str, names: Union[list[str], str], conds: str) -> pd.DataFrame:
    from transmatrix.data_api import Database

    var_str = ",".join(names) if isinstance(names, list) else names
    cmd_sql = f"SELECT {var_str} FROM {table}{f' WHERE {conds}' if conds else ''}"
    print(f"{SFG(cmd_sql)}:")
    db = Database(lib)
    _df = db.query(query=cmd_sql)
    return _df


def main():
    pd.set_option("display.unicode.east_asian_width", True)
    args = parse_args()
    if args.maxrows > 0:
        pd.set_option("display.max_rows", args.maxrows)
    if args.maxcols > 0:
        pd.set_option("display.max_columns", args.maxcols)

    col_names = args.vars.split(",") if args.vars else "*"
    df = fetch(args.lib, args.table, col_names, args.where)

    if args.sort:
        df = df.sort_values(args.sort.split(","), ascending=not args.descending)

    if args.head == 0 and args.tail == 0:
        print(df)
    else:
        if args.head > 0:
            print(f"{'head':-^120s}")
            print(df.head(args.head))
        if args.tail > 0:
            print(f"{'tail':-^120s}")
            print(df.tail(args.tail))
    return 0


if __name__ == "__main__":
    main()
