from datetime import datetime, time, timedelta

import pytest

from jpx_derivatives import (
    TradingSession,
    get_closing_time,
    get_current_session,
)

# テスト用設定
test_config = {
    "day": {
        "start": time(8, 45),
        "end": time(15, 40)
    },
    "day_closing": {
        "start": time(15, 40),
        "end": time(15, 45)
    },
    "night": {
        "start": time(17, 0),
        "end": time(5, 55)
    },
    "night_closing": {
        "start": time(5, 55),
        "end": time(6, 0)
    },
}


def test_get_current_session_day(monkeypatch):
    """現在のセッション日を取得するテスト"""
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 1, 9, 0)  # 8:45-15:40の間
    assert get_current_session(dt) == TradingSession.DAY


def test_get_current_session_day_closing(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 1, 15, 42)  # 15:40-15:45の間
    assert get_current_session(dt) == TradingSession.DAY_CLOSING


def test_get_current_session_night(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    # 17:00 は 夜間取引 (NIGHT)
    dt = datetime(2023, 1, 1, 17, 0)
    assert get_current_session(dt) == TradingSession.NIGHT

    # 翌日の 03:00 も NIGHT
    dt = datetime(2023, 1, 2, 3, 0)
    assert get_current_session(dt) == TradingSession.NIGHT


def test_get_current_session_night_closing(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    # 5:57 は 夜間クロージング (NIGHT_CLOSING)
    dt = datetime(2023, 1, 1, 5, 57)
    assert get_current_session(dt) == TradingSession.NIGHT_CLOSING


def test_get_current_session_off_hours(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 1, 7, 0)  # 6:00-8:45の間
    assert get_current_session(dt) == TradingSession.OFF_HOURS


def test_get_closing_time_day(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    # 日中取引の場合、day_closing.end (15:45) の当日日時
    dt = datetime(2023, 1, 2, 10, 0)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date(), time(15, 45))
    assert closing == expected


def test_get_closing_time_night_same_day(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    # NIGHT セッションで、まだ夜間クロージング開始前の場合 (03:00)
    dt = datetime(2023, 1, 3, 3, 0)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date(), time(6, 0))
    assert closing == expected


def test_get_closing_time_night_tomorrow(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    # NIGHT セッションで、現在時刻が夜間クロージング開始後 (17:00)
    # ※この場合、クロージング日時は翌日の 06:00 となる
    dt = datetime(2023, 1, 3, 17, 0)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date() + timedelta(days=1), time(6, 0))
    assert closing == expected


def test_get_closing_time_night_closing(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    # NIGHT_CLOSING の場合、当日の 06:00 を返す
    dt = datetime(2023, 1, 3, 5, 57)
    closing = get_closing_time(dt)
    expected = datetime.combine(dt.date(), time(6, 0))
    assert closing == expected


def test_get_closing_time_off_hours(monkeypatch):
    monkeypatch.setattr("jpx_derivatives.trading_session.load_trading_hours", lambda: test_config)
    dt = datetime(2023, 1, 3, 7, 0)
    closing = get_closing_time(dt)
    assert closing is None
