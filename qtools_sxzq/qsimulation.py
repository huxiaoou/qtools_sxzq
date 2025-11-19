import os
import numpy as np
import pandas as pd
from tqdm.contrib import tzip
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Union, Literal
from qtools_sxzq.qcalendar import CCalendar
from qtools_sxzq.qwidgets import check_and_makedirs, SFG, SFY, parse_instrument_from_contract
from qtools_sxzq.qdata import CDataDescriptor
from qtools_sxzq.qdataviewer import fetch


class TExePriceType(Enum):
    OPEN = "open"
    CLOSE = "close"


class TPosDirection(IntEnum):
    LNG = 1
    SRT = -1


class TPosOffset(IntEnum):
    OPN = 1
    CLS = -1


@dataclass(frozen=True)
class CPosKey:
    contract: str
    direction: TPosDirection


"""
------ position ------
"""


@dataclass(frozen=True)
class CTrade:
    key: CPosKey
    offset: TPosOffset
    qty: int
    multiplier: Union[int, float]
    exe_price: float

    def cost(self, cost_rate: float) -> float:
        return self.exe_price * self.multiplier * self.qty * cost_rate


def print_trades(trades: list[CTrade], color: bool = True):
    for ti, trade in enumerate(trades):
        if color:
            print(f"| {ti:>04d} | {SFG(trade)} |")
        else:
            print(f"| {ti:>04d} | {trade} |")
    return 0


@dataclass
class CPosition:
    key: CPosKey
    qty: int
    multiplier: Union[int, float]
    cost_price: float
    last_price: float

    @property
    def unrealized_pnl(self) -> float:
        return (self.last_price - self.cost_price) * self.multiplier * self.qty * float(self.key.direction)

    def cal_trade_from_target(self, target: "CPosition", exe_price: float) -> CTrade:
        return CTrade(
            key=self.key,
            offset=TPosOffset.OPN if (self.qty <= target.qty) else TPosOffset.CLS,
            qty=abs(target.qty - self.qty),
            multiplier=self.multiplier,
            exe_price=exe_price,
        )

    def convert_as_trade(self, exe_price: float, operation: TPosOffset) -> CTrade:
        return CTrade(
            key=self.key,
            offset=operation,
            qty=self.qty,
            multiplier=self.multiplier,
            exe_price=exe_price,
        )

    def update_from_trade(self, trade: CTrade, cost_rate: float) -> tuple[float, float]:
        cost = trade.cost(cost_rate)
        if trade.offset == TPosOffset.OPN:
            sum_amt = self.cost_price * self.qty + trade.exe_price * trade.qty
            sum_qty = self.qty + trade.qty
            self.cost_price = sum_amt / sum_qty
            self.qty = sum_qty
            realized_pnl = 0
        elif trade.offset == TPosOffset.CLS:
            if trade.qty > self.qty:
                raise ValueError(f"trade qty {trade.qty} > pos qty {self.qty}")
            else:
                self.qty -= trade.qty
            realized_pnl = (trade.exe_price - self.cost_price) * self.multiplier * trade.qty * float(self.key.direction)
        else:
            raise ValueError(f"unknown offset = {trade.offset}")
        return realized_pnl, cost

    def update_from_market(self, last_price: float):
        self.last_price = last_price
        return 0


TPositions = dict[CPosKey, CPosition]


def print_positions(positions: TPositions, color: bool = True):
    for key, pos in positions.items():
        if color:
            print(f"| {SFY(key)} : {SFG(pos)} |")
        else:
            print(f"| {key} : {pos} |")
    return 0


"""
------ manger major contract ------ 
"""


class CMgrMajContractBase:
    def get_contract(self, trade_date: str, instrument: str) -> str:
        raise NotImplementedError


"""
------ manger market data ------ 
"""


class CMgrMktDataBase:
    def get_md(
        self,
        trade_date: str,
        contract: str,
        md: Literal["open", "close", "settle", "multiplier"],
    ) -> Union[int, float]:
        raise NotImplementedError


"""
------ signal reader ------
"""


class CSignalBase:
    @property
    def sid(self) -> str:
        raise NotImplementedError

    def get_signal(self, trade_date: str) -> dict[str, float]:
        raise NotImplementedError


"""
------ account ------
"""


class CAccount:
    def __init__(self, init_cash: float, cost_rate: float):
        self.init_cash = init_cash
        self.cost_rate = cost_rate
        self.tot_realized_pnl: float = 0
        self.tot_unrealized_pnl: float = 0
        self.positions: TPositions = {}
        self.snapshots: list[dict] = []
        self.last_nav: float = init_cash

    @property
    def nav(self) -> float:
        return self.init_cash + self.tot_realized_pnl + self.tot_unrealized_pnl

    @property
    def navps(self) -> float:
        return self.nav / self.init_cash

    @property
    def ret(self) -> float:
        return self.nav / self.last_nav - 1

    def update_pnl(self, this_day_unrealized_pnl: float, this_day_realized_pnl: float, this_day_cost: float):
        self.tot_realized_pnl += this_day_realized_pnl - this_day_cost
        self.tot_unrealized_pnl = this_day_unrealized_pnl
        return 0

    def take_snapshot(self, trade_date: str, this_day_realized_pnl: float, this_day_cost: float):
        snapshot = {
            "trade_date": trade_date,
            "init_cash": self.init_cash,
            "tot_realized_pnl": self.tot_realized_pnl,
            "this_day_realized_pnl": this_day_realized_pnl,
            "this_day_cost": this_day_cost,
            "tot_unrealized_pnl": self.tot_unrealized_pnl,
            "last_nav": self.last_nav,
            "nav": self.nav,
            "navps": self.navps,
            "ret": self.ret,
        }
        self.snapshots.append(snapshot)
        return 0

    def update_last_nav(self):
        self.last_nav = self.nav
        return 0

    def export_snapshots(self) -> pd.DataFrame:
        return pd.DataFrame(self.snapshots)


"""
------ simulation ------
"""


class CSimulation:
    """
    This class provides a complex method to test signals using market data.
    0.  this class DOES NOT support increment test. In other words, user CAN NOT use this class to do
        daily increment to get a quick result.
    1.  the results may be a slightly WORSE than the results in husfort.qsimquick because of:
        1.1 major contract shifting is considered.
        1.2 a specific quantity instead of a precise weight number is used.
    2.  To use this class, user must provide the following 3 classes as input arguments when initializing.
            (CMgrMajContract, CMgrMktData, CSignal)
        To do this, user can:
        2.1 EITHER import CMgrMajContract, CMgrMktData, CSignal from husfort.qsimulation
        2.2 OR Write their own version of these 3 classes by inheriting from CMgrMajContractBase, CMgrMktDataBase, CSignalBase
            and realize corresponding virtual methods.

    """

    def __init__(
        self,
        signal: CSignalBase,
        init_cash: float,
        cost_rate: float,
        exe_price_type: TExePriceType,
        mgr_maj_contract: CMgrMajContractBase,
        mgr_mkt_data: CMgrMktDataBase,
        sim_save_dir: str,
        vid: str,
    ):
        self.signal: CSignalBase = signal
        self.account: CAccount = CAccount(init_cash, cost_rate)
        self.exe_price_type: TExePriceType = exe_price_type
        self.mgr_maj_contract: CMgrMajContractBase = mgr_maj_contract
        self.mgr_mkt_data: CMgrMktDataBase = mgr_mkt_data
        self.sim_save_dir = sim_save_dir
        self.vid = vid

    @property
    def save_id(self) -> str:
        return f"{self.signal.sid}-{self.exe_price_type.value}"

    def save_nav(self, nav_data: pd.DataFrame):
        check_and_makedirs(self.sim_save_dir)
        save_name = f"hsim_{self.save_id}.{self.vid}.csv"
        save_path = os.path.join(self.sim_save_dir, save_name)
        nav_data.to_csv(save_path, index=False, float_format="%.8f")
        return 0

    @staticmethod
    def gen_sig_exe_dates(bgn_date: str, stp_date: str, calendar: CCalendar) -> tuple[list[str], list[str]]:
        sig_bgn_date = calendar.get_next_date(bgn_date, shift=-1)
        iter_dates = calendar.get_iter_list(sig_bgn_date, stp_date)
        sig_dates, exe_dates = iter_dates[0:-1], iter_dates[1:]
        return sig_dates, exe_dates

    def covert_sig_to_target_pos(self, sig_date: str) -> TPositions:
        sigs = self.signal.get_signal(sig_date)
        target_pos: TPositions = {}
        for instru, weight in sigs.items():
            if abs(weight) < 1e-6:
                continue
            contract = self.mgr_maj_contract.get_contract(sig_date, instru)
            multiplier = self.mgr_mkt_data.get_md(sig_date, contract, md="multiplier")
            sig_price = self.mgr_mkt_data.get_md(sig_date, contract, md=TExePriceType.CLOSE.value)
            qty = int(np.round(self.account.last_nav * abs(weight) / multiplier / sig_price))
            key = CPosKey(contract, direction=TPosDirection.LNG if weight > 0 else TPosDirection.SRT)
            target_pos[key] = CPosition(
                key=key,
                qty=qty,
                multiplier=multiplier,
                cost_price=0,
                last_price=0,
            )
        return target_pos

    def cal_trades(self, target_pos: TPositions, trade_date: str) -> list[CTrade]:
        trades: list[CTrade] = []
        for pos_key, tgt_pos in target_pos.items():
            exe_price = self.mgr_mkt_data.get_md(trade_date, pos_key.contract, md=self.exe_price_type.value)
            act_pos = self.account.positions.get(pos_key, None)
            if act_pos is None:
                trade = tgt_pos.convert_as_trade(exe_price=exe_price, operation=TPosOffset.OPN)
            else:
                trade = act_pos.cal_trade_from_target(target=tgt_pos, exe_price=exe_price)
            trades.append(trade) if trade.qty > 0 else None

        for pos_key, act_pos in self.account.positions.items():
            if pos_key not in target_pos:
                exe_price = self.mgr_mkt_data.get_md(trade_date, pos_key.contract, md=self.exe_price_type.value)
                trade = act_pos.convert_as_trade(exe_price, operation=TPosOffset.CLS)
                trades.append(trade) if trade.qty > 0 else None
        return trades

    def update_from_trades(self, trades: list[CTrade]) -> tuple[float, float]:
        """

        :param trades:
        :return: realized_pnl, cost
        """
        realized_pnl, cost = 0.0, 0.0
        for trade in trades:
            if trade.key not in self.account.positions:
                if trade.offset == TPosOffset.CLS:
                    raise ValueError(f"Try to close a position not in account: {trade.key}")
                else:  # trade.operation == TPosOperation.OPN
                    self.account.positions[trade.key] = CPosition(
                        key=trade.key,
                        qty=0,
                        multiplier=trade.multiplier,
                        cost_price=0,
                        last_price=0,
                    )
            trade_rpnl, trade_cost = self.account.positions[trade.key].update_from_trade(
                trade, cost_rate=self.account.cost_rate
            )
            realized_pnl += trade_rpnl
            cost += trade_cost
        return realized_pnl, cost

    def update_from_market(self, trade_date: str) -> float:
        """

        :param trade_date:
        :return: unrealized_pnl
        """

        unrealized_pnl = 0
        rm_keys: list[CPosKey] = []
        for pos_key, pos in self.account.positions.items():
            if pos.qty > 0:
                contract = pos_key.contract
                last_price = self.mgr_mkt_data.get_md(trade_date, contract=contract, md="close")
                pos.update_from_market(last_price=last_price)
                unrealized_pnl += pos.unrealized_pnl
            else:
                rm_keys.append(pos_key)
        for pos_key in rm_keys:
            del self.account.positions[pos_key]
        return unrealized_pnl

    def main(self, bgn_date: str, stp_date: str, calendar: CCalendar, verbose: bool = False):
        sig_dates, exe_dates = self.gen_sig_exe_dates(bgn_date, stp_date, calendar)
        for sig_date, exe_date in tzip(sig_dates, exe_dates):
            target_pos = self.covert_sig_to_target_pos(sig_date=sig_date)
            trades = self.cal_trades(target_pos, trade_date=exe_date)
            this_day_realized_pnl, this_day_cost = self.update_from_trades(trades=trades)
            this_day_unrealized_pnl = self.update_from_market(trade_date=exe_date)
            self.account.update_pnl(
                this_day_unrealized_pnl=this_day_unrealized_pnl,
                this_day_realized_pnl=this_day_realized_pnl,
                this_day_cost=this_day_cost,
            )
            self.account.take_snapshot(exe_date, this_day_realized_pnl, this_day_cost)
            self.account.update_last_nav()
            if verbose:
                print(f"----------{exe_date}----------")
                print_positions(self.account.positions)
        snapshots = self.account.export_snapshots()
        self.save_nav(snapshots)
        return 0


"""
------ classes for Transquant ------
Not necessary for all users
users could define their own classes
by inherit from base class
------------------------------------
"""


class CMgrMajContract(CMgrMajContractBase):
    def __init__(self, universe: list[str], dominant: CDataDescriptor):
        major_data = fetch(
            lib=dominant.db_name,
            table=dominant.table_name,
            names=dominant.fields,
            conds="",
        ).dropna(axis=0, subset="dominant")
        major_data["trade_date"] = major_data["trade_day"].map(lambda z: z.replace("-", ""))
        major_data["instrument"] = major_data["dominant"].map(self.get_instrument_from_contract)
        self.major_data: dict[str, dict[str, str]] = {}  # dict[instrument, dict[trade_date, major_contract]]
        for instrument, instrument_data in major_data.groupby(by="instrument"):  # type:ignore
            instrument: str
            instrument_data: pd.DataFrame
            if instrument not in universe:
                continue
            self.major_data[instrument] = instrument_data.set_index("trade_date")["dominant"].to_dict()
        print(f"... Major contract loaded")

    @staticmethod
    def get_instrument_from_contract(contract: str) -> str:
        n0 = parse_instrument_from_contract(contract)
        instru, exchange = n0.split("_")
        return f"{instru}9999_{exchange}"

    def get_contract(self, trade_date: str, instrument: str) -> str:
        """

        :param trade_date: like "20250407"
        :param instrument: "CU.SHF"
        :return: "CU2506.SHF"
        """
        return self.major_data[instrument][trade_date]


class CMgrMktData(CMgrMktDataBase):
    def __init__(self, fmd: CDataDescriptor):
        fmt_fields = [f"`{z}`" if z in ["open", "close"] else z for z in fmd.fields]
        major_data = fetch(
            lib=fmd.db_name,
            table=fmd.table_name,
            names=["datetime", "code"] + fmt_fields,
            conds="",
        )
        major_data = major_data.rename(columns={"contractmultiplier": "multiplier", "code": "contract"})
        major_data["trade_date"] = major_data["datetime"].map(lambda z: z.strftime("%Y%m%d"))
        keys = ["trade_date", "contract"]
        # dict[(trade_date, contract), dict[md, value]]
        self.md: dict[tuple[str, str], dict] = major_data.set_index(keys).to_dict(orient="index")  # type:ignore
        print(f"... Market data loaded")

    def get_md(
        self,
        trade_date: str,
        contract: str,
        md: Literal["open", "close", "settle", "multiplier"],
    ) -> Union[int, float]:
        """

        :param trade_date:
        :param contract:
        :param md:  ["pre_close", "pre_settle",
                     "open", "high", "low", "close", "settle",
                     "vol", "amount", "oi"]
        :return:
        """
        return self.md[(trade_date, contract)][md]


class CSignal(CSignalBase):
    def __init__(self, sid: str, signal_db: CDataDescriptor):
        self._sid = sid
        signal_data = fetch(
            lib=signal_db.db_name,
            table=signal_db.table_name,
            names=["datetime", "code", self.sid],
            conds="",
        )
        signal_data["trade_date"] = signal_data["datetime"].map(lambda z: z.strftime("%Y%m%d"))
        self.signal: dict[str, dict[str, float]] = {}  # dict[trade_date, dict[instrument, weight]]
        for trade_date, trade_date_data in signal_data.groupby(by="trade_date"):  # type:ignore
            trade_date: str
            trade_date_data: pd.DataFrame
            self.signal[trade_date] = trade_date_data.set_index("code")[self.sid].to_dict()
        print(f"... Singal {SFG(sid)} data loaded")

    @property
    def sid(self) -> str:
        return self._sid

    def get_signal(self, trade_date: str) -> dict[str, float]:
        return self.signal.get(trade_date, {})
