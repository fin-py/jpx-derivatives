import pandas as pd

from config import data_dir


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


def main() -> None:
    holidays = pd.DataFrame(get_data(), columns=["Date"])
    holidays.to_parquet(data_dir / "holidays.parquet")


if __name__ == "__main__":
    main()
