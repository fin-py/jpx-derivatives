from datetime import date, datetime
from unittest.mock import patch

import pytest

from jpx_derivatives.holidays import is_holiday


@pytest.mark.parametrize(
    "target_date,expected",
    [
        (date(2020, 1, 13), True),    # 祝日
        (date(2024, 1, 1), True),    # 元日
        (date(2024, 1, 2), True),    # 年始休業日
        (date(2024, 1, 3), False),    # 祝日取引
        (date(2024, 1, 4), False),   # 営業日
        (date(2024, 1, 6), True),    # 土曜日
        (date(2024, 1, 7), True),    # 日曜日
        (datetime(2024, 1, 1), True),  # datetime型
        ("2024-01-01", True),        # 文字列
        ("2024-01-06", True),        # 土曜日（文字列）
    ],
)
def test_is_holiday(target_date, expected):
    """休日判定のテスト"""
    assert is_holiday(target_date) == expected 

def test_is_holiday_no_args():
    """引数なしで現在時刻の休日判定ができることを確認"""
    # 2024-01-01（元日）の日時をモック
    mock_datetime = datetime(2024, 1, 1, 10, 0)
    with patch('jpx_derivatives.holidays.datetime') as mock_date:
        mock_date.now.return_value = mock_datetime
        assert is_holiday() is True

    # 2024-01-04（営業日）の日時をモック
    mock_datetime = datetime(2024, 1, 4, 10, 0)
    with patch('jpx_derivatives.holidays.datetime') as mock_date:
        mock_date.now.return_value = mock_datetime
        assert is_holiday() is False

    # 2024-01-06（土曜日）の日時をモック
    mock_datetime = datetime(2024, 1, 6, 10, 0)
    with patch('jpx_derivatives.holidays.datetime') as mock_date:
        mock_date.now.return_value = mock_datetime
        assert is_holiday() is True 