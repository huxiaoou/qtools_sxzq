import argparse
import re
from transmatrix.data_api import Database
from qtools_sxzq.qwidgets import SFG


def parse_args():
    args_parser = argparse.ArgumentParser(description="A python script to remove trans-quant database")
    args_parser.add_argument(
        "--lib",
        type=str,
        required=True,
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


def main():
    args = parse_args()
    lib_name, table_name = args.lib, args.table
    if table_name:
        db = Database(lib_name)
        db.truncate_table(table_name)  # clear table
        db.delete_table(table_name)  # delete table
    elif args.recursive:
        db = Database(lib_name)
        tabs = db.show_tables()
        if tabs:
            for i, tab in enumerate(tabs):
                if re.match(pattern=r".*_mapping_\d{13}_\d{2}$", string=tab):
                    print(f"skip {i:>3d} {tab}, mapping file will be removed automatically when its master is removed")
                else:
                    print(f"removing {i:>3d} {tab}")
                    db.truncate_table(tab)
                    db.delete_table(tab)
        else:
            print(f"{SFG(lib_name)} has no tables")
    else:
        print("either argument --table or --recursive is required")
    return 0


if __name__ == "__main__":
    main()
