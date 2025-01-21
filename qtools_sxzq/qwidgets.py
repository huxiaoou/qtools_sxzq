import re
import datetime as dt
from typing import Union


def SetFontColor(c):
    def inner(s: Union[str, int, float, dt.datetime]):
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
