import os
from datetime import datetime, time, timedelta
from enum import Enum

from jpx_derivatives.holidays import is_holiday

# 取引時間の設定
TRADING_HOURS = {
    "day": {"start": time(8, 45), "end": time(15, 40)},
    "day_closing": {"start": time(15, 40), "end": time(15, 45)},
    "night": {"start": time(17, 0), "end": time(5, 55)},
    "night_closing": {"start": time(5, 55), "end": time(6, 0)},
}


class TradingSession(Enum):
    DAY = "DAY"  # 日中取引
    DAY_CLOSING = "DAY_CLOSING"  # 日中クロージングオークション
    NIGHT = "NIGHT"  # 夜間取引
    NIGHT_CLOSING = "NIGHT_CLOSING"  # 夜間クロージングオークション
    OFF_HOURS = "OFF_HOURS"  # 立会時間外

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


def load_trading_hours() -> dict:
    """取引時間設定を返す"""
    return TRADING_HOURS


def get_current_session(current_datetime: datetime = None) -> TradingSession:
    """現在の立会時間を返す

    引数 current_datetime が指定されていない場合は、現在時刻 (datetime.now()) を使用して判定します。
    """
    if current_datetime is None:
        current_datetime = datetime.now()
    current_time = current_datetime.time()
    config = load_trading_hours()

    # 日中取引
    if config["day"]["start"] <= current_time < config["day"]["end"]:
        return TradingSession.DAY

    # 日中クロージングオークション
    if config["day_closing"]["start"] <= current_time < config["day_closing"]["end"]:
        return TradingSession.DAY_CLOSING

    # 夜間取引（日付をまたぐケースに対応）
    if (
        config["night"]["start"] <= current_time
        or current_time < config["night"]["end"]
    ):
        return TradingSession.NIGHT

    # 夜間クロージングオークション
    if (
        config["night_closing"]["start"]
        <= current_time
        < config["night_closing"]["end"]
    ):
        return TradingSession.NIGHT_CLOSING

    # 立会時間外
    return TradingSession.OFF_HOURS


def get_closing_time(current_datetime: datetime = None) -> datetime:
    """
    現在の取引時間帯に応じたクロージングオークション終了時刻のdatetimeを返す
    ・日中取引・日中クロージングオークションの場合は、config["day_closing"]["end"] の時刻で当日のdatetimeを返す
    ・夜間取引・夜間クロージングオークションの場合は、config["night_closing"]["end"] の時刻でdatetimeを返す
      ※ TradingSession.NIGHTの場合、config["night_closing"]["start"]以降（つまり0時になるまで）の場合は翌日の日付となります
    ・立会時間外の場合は None を返します

    引数 current_datetime が None の場合は、現在時刻 (datetime.now()) を使用します。
    """
    if current_datetime is None:
        current_datetime = datetime.now()
    config = load_trading_hours()
    current_session = get_current_session(current_datetime)

    if current_session in [TradingSession.DAY, TradingSession.DAY_CLOSING]:
        closing_time = config["day_closing"]["end"]
        candidate = datetime.combine(current_datetime.date(), closing_time)
        if candidate <= current_datetime:
            candidate += timedelta(days=1)
        return candidate

    elif current_session in [TradingSession.NIGHT, TradingSession.NIGHT_CLOSING]:
        closing_time = config["night_closing"]["end"]
        candidate = datetime.combine(current_datetime.date(), closing_time)
        if current_session == TradingSession.NIGHT:
            night_closing_start = config["night_closing"]["start"]
            # もし現在時刻が night_closing の開始時刻以降であれば、終了日時を翌日に設定
            if current_datetime.time() >= night_closing_start:
                candidate = datetime.combine(
                    current_datetime.date() + timedelta(days=1), closing_time
                )
            else:
                if candidate <= current_datetime:
                    candidate += timedelta(days=1)
        else:
            if candidate <= current_datetime:
                candidate += timedelta(days=1)
        return candidate

    else:
        return None


def is_trading_hours(current_datetime: datetime = None) -> bool:
    """
    指定された日時が取引可能な時間帯かどうかを判定する

    Args:
        current_datetime: 判定対象の日時（Noneの場合は現在時刻を使用）

    Returns:
        bool: 取引可能な時間の場合はTrue、それ以外（休日・立会時間外）の場合はFalse
    """
    if current_datetime is None:
        current_datetime = datetime.now()

    # 休日判定
    if is_holiday(current_datetime):
        return False

    # 立会時間判定
    current_session = get_current_session(current_datetime)
    return current_session not in [TradingSession.OFF_HOURS]
