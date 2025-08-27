#!/usr/bin/env python

import argparse
from transmatrix.data_api import Database
from qtools_sxzq.qwidgets import SFG
from qtools_sxzq.qdataviewer import get_tqdb_tables


def parse_args():
    args_parser = argparse.ArgumentParser(description="A python script to list trans-quant database")
    args_parser.add_argument(
        "lib", type=str,
        help="path for trans-quant database, like 'huxiaoou_private' or 'meta_data'",
    )
    _args = args_parser.parse_args()
    return _args


def main():
    args = parse_args()
    lib_name = args.lib
    tabs = get_tqdb_tables(lib_name)
    if tabs:
        for i, tab in enumerate(tabs):
            print(f"{i:>03d} {tab}")
    else:
        print(f"{SFG(lib_name)} has no tables")
    return 0


if __name__ == "__main__":
    main()
