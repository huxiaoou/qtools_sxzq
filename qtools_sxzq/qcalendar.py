import datetime as dt
import pandas as pd


class CCalendar(object):
    def __init__(self, calendar_path: str, header: int = 0):
        if isinstance(header, int):
            calendar_df = pd.read_csv(calendar_path, dtype=str, header=header)
        else:
            calendar_df = pd.read_csv(calendar_path, dtype=str, header=None, names=["trade_date"])
        self.__trade_dates = [_.replace("-", "") for _ in calendar_df["trade_date"]]

    @property
    def last_date(self):
        return self.__trade_dates[-1]

    @property
    def first_date(self):
        return self.__trade_dates[0]

    @property
    def trade_dates(self) -> list[str]:
        return self.__trade_dates

    def get_iter_list(self, bgn_date: str, stp_date: str, ascending: bool = True) -> list[str]:
        res = []
        for t_date in self.__trade_dates:
            if t_date < bgn_date:
                continue
            if t_date >= stp_date:
                break
            res.append(t_date)
        return res if ascending else sorted(res, reverse=True)

    def shift_iter_dates(self, iter_dates: list[str], shift: int) -> list[str]:
        """

        :param iter_dates:
        :param shift: > 0, in the future
                      < 0, in the past
        :return:
        """
        if shift >= 0:
            new_dates = [self.get_next_date(iter_dates[-1], shift=s) for s in range(1, shift + 1)]
            shift_dates = iter_dates[shift:] + new_dates
        else:  # shift < 0
            new_dates = [self.get_next_date(iter_dates[0], shift=s) for s in range(shift, 0)]
            shift_dates = new_dates + iter_dates[:shift]
        return shift_dates

    def get_sn(self, base_date: str) -> int:
        return self.__trade_dates.index(base_date)

    def get_date(self, sn: int) -> str:
        return self.__trade_dates[sn]

    def get_next_date(self, this_date: str, shift: int = 1) -> str:
        """

        :param this_date:
        :param shift: > 0, get date in the future; < 0, get date in the past
        :return:
        """

        this_sn = self.get_sn(this_date)
        next_sn = this_sn + shift
        return self.__trade_dates[next_sn]

    def get_start_date(self, bgn_date: str, max_win: int, shift: int) -> str:
        return self.get_next_date(bgn_date, -max_win + shift)

    def get_last_days_in_range(self, bgn_date: str, stp_date: str) -> list[str]:
        res = []
        for this_day, next_day in zip(self.__trade_dates[:-1], self.__trade_dates[1:]):
            if this_day < bgn_date:
                continue
            elif this_day >= stp_date:
                break
            else:
                if this_day[0:6] != next_day[0:6]:
                    res.append(this_day)
        return res

    def get_last_day_of_month(self, month: str) -> str:
        """
        :param month: like "202403"

        """

        threshold = f"{month}31"
        for t in self.__trade_dates[::-1]:
            if t <= threshold:
                return t
        raise ValueError(f"Could not find last day for {month}")

    def get_first_day_of_month(self, month: str) -> str:
        """
        :param month: like 202403

        """

        threshold = f"{month}01"
        for t in self.__trade_dates:
            if t >= threshold:
                return t
        raise ValueError(f"Could not find first day for {month}")

    @staticmethod
    def split_by_month(dates: list[str]) -> dict[str, list[str]]:
        res = {}
        for t in dates:
            m = t[0:6]
            if m not in res:
                res[m] = [t]
            else:
                res[m].append(t)
        return res

    @staticmethod
    def move_date_string(trade_date: str, move_days: int = 1) -> str:
        """

        :param trade_date:
        :param move_days: >0, to the future; <0, to the past
        :return:
        """
        return (dt.datetime.strptime(trade_date, "%Y%m%d") + dt.timedelta(days=move_days)).strftime("%Y%m%d")

    @staticmethod
    def convert_d08_to_d10(date: str) -> str:
        # "202100101" -> "2021-01-01"
        return date[0:4] + "-" + date[4:6] + "-" + date[6:8]

    @staticmethod
    def convert_d10_to_d08(date: str) -> str:
        # "20210-01-01" -> "20210101"
        return date.replace("-", "")

    @staticmethod
    def get_next_month(month: str, s: int) -> str:
        """

        :param month: format = YYYYMM
        :param s: > 0 in the future
                  < 0 in the past
        :return:
        """
        y, m = int(month[0:4]), int(month[4:6])
        dy, dm = s // 12, s % 12
        ny, nm = y + dy, m + dm
        if nm > 12:
            ny, nm = ny + 1, nm - 12
        return f"{ny:04d}{nm:02d}"

    def get_dates_header(self, bgn_date: str, stp_date: str, header_name: str = "trade_date") -> pd.DataFrame:
        """
        :param bgn_date: format = "YYYYMMDD"
        :param stp_date: format = "YYYYMMDD"
        :param header_name:
        :return:
        """

        h = pd.DataFrame({header_name: self.get_iter_list(bgn_date, stp_date)})
        return h
