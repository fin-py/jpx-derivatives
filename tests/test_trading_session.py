from datetime import datetime, timedelta

import pytest

from trading_session import (
    TradingSession,
    get_closing_time,
    get_current_session,
    parse_time,
)

# テスト用設定
test_config = {
    "day": {"start": "09:00", "end": "11:30"},
    "day_closing": {"start": "11:30", "end": "11:45"},
    "night": {"start": "16:30", "end": "05:30"},
    "night_closing": {"start": "05:30", "end": "06:00"},
}


def test_get_current_session_day(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 1, 10, 0)
    assert get_current_session(dt) == TradingSession.DAY


def test_get_current_session_day_closing(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 1, 11, 32)
    assert get_current_session(dt) == TradingSession.DAY_CLOSING


def test_get_current_session_night(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    # 17:00 は 夜間取引 (NIGHT)
    dt = datetime(2023, 1, 1, 17, 0)
    assert get_current_session(dt) == TradingSession.NIGHT

    # 翌日の 03:00 も NIGHT
    dt = datetime(2023, 1, 2, 3, 0)
    assert get_current_session(dt) == TradingSession.NIGHT


def test_get_current_session_night_closing(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    # 05:40 は 夜間クロージング (NIGHT_CLOSING)
    dt = datetime(2023, 1, 1, 5, 40)
    assert get_current_session(dt) == TradingSession.NIGHT_CLOSING


def test_get_current_session_off_hours(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 1, 8, 0)
    assert get_current_session(dt) == TradingSession.OFF_HOURS


def test_get_closing_time_day(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    # 日中取引の場合、day_closing.end ("11:45") の当日日時
    dt = datetime(2023, 1, 2, 10, 0)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date(), parse_time("11:45"))
    assert closing == expected


def test_get_closing_time_night_same_day(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    # NIGHT セッションで、まだ夜間クロージング開始前の場合 (03:00)
    dt = datetime(2023, 1, 3, 3, 0)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date(), parse_time("06:00"))
    assert closing == expected


def test_get_closing_time_night_tomorrow(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    # NIGHT セッションで、現在時刻が夜間クロージング開始後 (17:00)
    # ※この場合、クロージング日時は翌日の "06:00" となる
    dt = datetime(2023, 1, 3, 17, 0)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date() + timedelta(days=1), parse_time("06:00"))
    assert closing == expected


def test_get_closing_time_night_closing(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    # NIGHT_CLOSING の場合、当日の "06:00" を返す
    dt = datetime(2023, 1, 3, 5, 40)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date(), parse_time("06:00"))
    assert closing == expected


def test_get_closing_time_off_hours(monkeypatch):
    monkeypatch.setattr("trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 3, 12, 0)
    closing = get_closing_time(dt)
    assert closing is None
