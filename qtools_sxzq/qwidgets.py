import re
import os
import datetime as dt
from typing import Union, Any


def SetFontColor(c):
    def inner(s: Union[str, int, float, dt.datetime, Any]):
        return f"\033[{c}m{s}\033[0m"

    return inner


SFR = SetFontColor(c="0;31;40")  # Red
SFG = SetFontColor(c="0;32;40")  # Green
SFY = SetFontColor(c="0;33;40")  # Yellow
SFB = SetFontColor(c="0;34;40")  # Blue
SFM = SetFontColor(c="0;35;40")  # Magenta
SFC = SetFontColor(c="0;36;40")  # Cyan
SFW = SetFontColor(c="0;37;40")  # White


def parse_instrument_from_contract(contract_id: str) -> str:
    return re.sub(pattern="[0-9]", repl="", string=contract_id)


def check_and_mkdir(dir_path: str, verbose: bool = False):
    try:
        os.mkdir(dir_path)
    except FileExistsError:
        pass
    if verbose:
        print(f"[INF] Making directory {SFG(dir_path)}")
    return 0


def check_and_makedirs(dir_path: str, verbose: bool = False):
    try:
        os.makedirs(dir_path)
    except FileExistsError:
        pass
    if verbose:
        print(f"[INF] Making directory {SFG(dir_path)}")
    return 0
