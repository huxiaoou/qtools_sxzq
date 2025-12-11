#!/usr/bin/env python

import argparse
import re
from qtools_sxzq.qwidgets import SFG
from qtools_sxzq.qdataviewer import get_tqdb_tables


def parse_args():
    args_parser = argparse.ArgumentParser(description="A python script to list trans-quant database")
    args_parser.add_argument(
        "lib",
        type=str,
        help="path for trans-quant database, like 'huxiaoou_private' or 'meta_data'",
    )
    args_parser.add_argument(
        "--pattern",
        type=str,
        default="",
        help="regex expression to filter table names, like 'gamma'",
    )
    _args = args_parser.parse_args()
    return _args


def main():
    args = parse_args()
    lib_name = args.lib
    tabs = get_tqdb_tables(lib_name)
    if args.pattern:
        selected_tabs = [tab for tab in tabs if re.search(args.pattern, tab) is not None]
    else:
        selected_tabs = tabs
    if selected_tabs:
        for i, tab in enumerate(selected_tabs):
            print(f"{i:>03d} {tab}")
    else:
        if args.pattern:
            print(f"{SFG(lib_name)} has no tables match pattern = '{args.pattern}'")
        else:
            print(f"{SFG(lib_name)} has no tables.")
    return 0


if __name__ == "__main__":
    main()
