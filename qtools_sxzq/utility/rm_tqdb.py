#!/usr/bin/env python

import argparse
from transmatrix.data_api import Database
from qtools_sxzq.qwidgets import SFG, SFY


def parse_args():
    args_parser = argparse.ArgumentParser(description="A python script to remove trans-quant database")
    args_parser.add_argument(
        "lib", type=str,
        help="path for trans-quant database, like 'huxiaoou_private' or 'meta_data'",
    )
    args_parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="table name in the database, like 'table_avlb' or 'future_bar_1day'",
    )
    args_parser.add_argument(
        "-r", "--recursive",
        default=False,
        action="store_true",
        help="if argument --table is not provided, this one must be provided to the whole database",
    )
    _args = args_parser.parse_args()
    return _args


def rm_tab_from_db(db, table_name: str):
    try:
        db.truncate_table(table_name)  # clear table
        db.delete_table(table_name)  # delete table
    except ConnectionError:
        print(f"Connection error for table {SFY(table_name)}, file does not exist, it may have been removed.")
    return


def main():
    args = parse_args()
    lib_name, table_name = args.lib, args.table
    if table_name:
        db = Database(lib_name)
        rm_tab_from_db(db, table_name)
    elif args.recursive:
        db = Database(lib_name)
        tabs = db.show_tables()
        if tabs:
            for i, tab in enumerate(tabs):
                print(f"removing {i:>3d} {SFY(tab)}")
                # re.match(pattern=r".*_mapping_\d{13}_\d{2}$", string=tab):
                rm_tab_from_db(db, tab)
        else:
            print(f"{SFG(lib_name)} has no tables")
    else:
        print("either argument --table or --recursive is required")
    return 0


if __name__ == "__main__":
    main()
