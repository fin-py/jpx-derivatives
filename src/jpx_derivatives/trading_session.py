from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path

import tomllib


class TradingSession(Enum):
    DAY = "DAY"  # 日中取引
    DAY_CLOSING = "DAY_CLOSING"  # 日中クロージングオークション
    NIGHT = "NIGHT"  # 夜間取引
    NIGHT_CLOSING = "NIGHT_CLOSING"  # 夜間クロージングオークション
    OFF_HOURS = "OFF_HOURS"  # 立会時間外


def load_trading_hours() -> dict:
    """取引時間設定を読み込む"""
    config_path = Path(__file__).parent / "config" / "trading_hours.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def parse_time(time_str: str) -> time:
    """HH:MM形式の文字列をtime型に変換"""
    hour, minute = map(int, time_str.split(":"))
    return time(hour, minute)


def get_current_session(current_datetime: datetime = None) -> TradingSession:
    """現在の立会時間を返す

    引数 current_datetime が指定されていない場合は、現在時刻 (datetime.now()) を使用して判定します。
    """
    if current_datetime is None:
        current_datetime = datetime.now()
    current_time = current_datetime.time()
    config = load_trading_hours()

    # 日中取引
    day_start = parse_time(config["day"]["start"])
    day_end = parse_time(config["day"]["end"])
    if day_start <= current_time < day_end:
        return TradingSession.DAY

    # 日中クロージングオークション
    day_closing_start = parse_time(config["day_closing"]["start"])
    day_closing_end = parse_time(config["day_closing"]["end"])
    if day_closing_start <= current_time < day_closing_end:
        return TradingSession.DAY_CLOSING

    # 夜間取引（日付をまたぐケースに対応）
    night_start = parse_time(config["night"]["start"])
    night_end = parse_time(config["night"]["end"])
    if night_start <= current_time or current_time < night_end:
        return TradingSession.NIGHT

    # 夜間クロージングオークション
    night_closing_start = parse_time(config["night_closing"]["start"])
    night_closing_end = parse_time(config["night_closing"]["end"])
    if night_closing_start <= current_time < night_closing_end:
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
        closing_time = parse_time(config["day_closing"]["end"])
        candidate = datetime.combine(current_datetime.date(), closing_time)
        if candidate <= current_datetime:
            candidate += timedelta(days=1)
        return candidate

    elif current_session in [TradingSession.NIGHT, TradingSession.NIGHT_CLOSING]:
        closing_time = parse_time(config["night_closing"]["end"])
        candidate = datetime.combine(current_datetime.date(), closing_time)
        if current_session == TradingSession.NIGHT:
            night_closing_start = parse_time(config["night_closing"]["start"])
            # もし現在時刻が night_closing の開始時刻以降であれば、終了日時を翌日に設定
            if current_datetime.time() >= night_closing_start:
                candidate = datetime.combine(current_datetime.date() + timedelta(days=1), closing_time)
            else:
                if candidate <= current_datetime:
                    candidate += timedelta(days=1)
        else:
            if candidate <= current_datetime:
                candidate += timedelta(days=1)
        return candidate

    else:
        return None
