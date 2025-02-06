from datetime import date, datetime

import pandas as pd

from jpx_derivatives.config import data_dir


def get_data() -> pd.Series:
    holidays_jp = pd.to_datetime(
        pd.read_csv(
            "https://raw.githubusercontent.com/holiday-jp/holiday_jp/refs/heads/master/holidays.yml",
            skiprows=1,
            delimiter=":",
            header=None,
        ).iloc[:, 0]
    )
    holidays_jp_2020_2022 = holidays_jp[
        (holidays_jp >= pd.Timestamp("2020-01-01"))
        & (holidays_jp < pd.Timestamp("2022-09-23"))
    ]
    add_date = pd.to_datetime(
        pd.Series(
            [
                "2020-01-02",
                "2020-01-03",
                "2020-12-31",
                "2021-01-02",
                "2021-01-03",
                "2021-12-31",
                "2022-01-02",
                "2022-01-03",
                "2023-01-01",
                "2024-01-01",
                "2025-01-01",
            ]
        )
    )
    holidays_jpx_2020_2022 = (
        pd.concat([holidays_jp_2020_2022, add_date])
        .sort_values()
        .reset_index(drop=True)
    )
    holidays_jpx_after_2022 = pd.read_excel(
        "https://www.jpx.co.jp/derivatives/rules/holidaytrading/nlsgeu000006hweb-att/nlsgeu000006jgee.xlsx"
    )
    return (
        pd.concat(
            [
                holidays_jpx_2020_2022,
                pd.to_datetime(
                    holidays_jpx_after_2022.groupby("実施有無")
                    .get_group("実施しない")
                    .loc[:, "祝日取引の対象日"]
                ),
            ]
        )
        .sort_values()
        .reset_index(drop=True)
    )


def is_holiday(target_date: date | datetime | str | None = None) -> bool:
    """
    指定された日付が休日かどうかを判定する

    Args:
        target_date: 判定対象の日付（date型、datetime型、または'YYYY-MM-DD'形式の文字列）
                    Noneの場合は現在の日時を使用

    Returns:
        bool: 休日の場合はTrue、営業日の場合はFalse
        以下の場合にTrueを返します:
        - 土曜日または日曜日
        - JPX休場日（祝日、年末年始等）
    """
    # 引数がNoneの場合は現在の日時を使用
    if target_date is None:
        target_date = datetime.now()

    # 入力を日付型に変換
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()
    elif isinstance(target_date, type(datetime.now())):
        target_date = target_date.date()

    # 土日判定
    if target_date.weekday() >= 5:  # 5=土曜日, 6=日曜日
        return True

    # URLからparquetファイルを読み込む
    holidays_df = pd.read_parquet(
        "https://github.com/fin-py/jpx-derivatives/raw/refs/heads/main/data/holidays.parquet"
    )

    # 休日一覧と照合
    return target_date in holidays_df['Date'].dt.date.values


def save_holidays_to_parquet():
    """休日の一覧をparquetファイルに保存する"""
    holidays = pd.DataFrame(get_data(), columns=["Date"])
    holidays.to_parquet(data_dir / "holidays.parquet")


if __name__ == "__main__":
    save_holidays_to_parquet()
