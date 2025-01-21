#!/usr/bin/env python

import argparse
from transmatrix.data_api import Database
from qtools_sxzq.qwidgets import SFG


def parse_args():
    args_parser = argparse.ArgumentParser(description="A python script to list trans-quant database")
    args_parser.add_argument(
        "--lib",
        type=str,
        required=True,
        help="path for trans-quant database, like 'huxiaoou_private' or 'meta_data'",
    )
    _args = args_parser.parse_args()
    return _args


def main():
    args = parse_args()
    lib_name = args.lib
    db = Database(lib_name)
    tabs = db.show_tables()
    if tabs:
        for i, tab in enumerate(tabs):
            print(f"{i:>03d} {tab}")
    else:
        print(f"{SFG(lib_name)} has no tables")
    return 0


if __name__ == "__main__":
    main()
