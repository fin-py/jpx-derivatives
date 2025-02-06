from datetime import date, datetime

import pytest

from jpx_derivatives.holidays import is_holiday


@pytest.mark.parametrize(
    "target_date,expected",
    [
        (date(2024, 1, 1), True),    # 元日
        (date(2024, 1, 2), True),    # 年始休業日
        (date(2024, 1, 3), True),    # 年始休業日
        (date(2024, 1, 4), False),   # 営業日
        (datetime(2024, 1, 1), True),  # datetime型
        ("2024-01-01", True),        # 文字列
    ],
)
def test_is_holiday(target_date, expected):
    """休日判定のテスト"""
    assert is_holiday(target_date) == expected 