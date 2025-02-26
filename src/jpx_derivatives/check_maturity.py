import os
import datetime
import pandas as pd

from config import data_dir


class maturity_info_class:
    def __init__(self):
        sqpath = data_dir / "special_quotation.parquet"
        if not os.path.exists(sqpath):
            raise FileNotFoundError(f"{sqpath}が存在しません")

        sqinfo = pd.read_parquet(sqpath)
        sqinfo["LastTradingDay"] = pd.to_datetime(sqinfo["LastTradingDay"])
        sqinfo["SpecialQuotationDay"] = pd.to_datetime(sqinfo["SpecialQuotationDay"])
        # SQの時刻は9時
        sqinfo["SpecialQuotationDay"] = sqinfo["SpecialQuotationDay"].apply(
            lambda x: x.replace(hour=9, minute=0, second=0)
        )

        # 取引時刻が2024/11/5に変更
        sqinfo["LastTradingDay"] = sqinfo.apply(
            lambda row: (
                datetime.datetime.combine(row["LastTradingDay"], datetime.time(15, 15))
                if row["LastTradingDay"] < datetime.datetime(2024, 11, 5)
                else datetime.datetime.combine(
                    row["LastTradingDay"], datetime.time(15, 45)
                )
            ),
            axis=1,
        )
        self.sqinfo = sqinfo.sort_values("LastTradingDay")

    def check_option_maturity(
        self,
        dt: datetime.datetime,
        maturity_n: int,
        large_mini: str,
    ) -> tuple[datetime.datetime, datetime.datetime, str]:
        """
        渡されたdtの第[maturity_n]限月の最終取引日時とSQ日を返す。
        dt: 基準日時
        maturity_n: 2の場合第2限月を返す、マイナスも可
        large_mini: "large" / "mini"
        return: lasttradingday, sqdate, contractmonth
        contractmonthは "2025-03", "2025-03-W5" など
        """
        if maturity_n == 0:
            raise ValueError(f"maturity_nは0以外で指定してください。（マイナスも可）")
        if dt < self.sqinfo["LastTradingDay"].min():
            raise ValueError(f"dt={self.sqinfo['LastTradingDay'].min()}以降のみ対応")
        if dt > self.sqinfo["LastTradingDay"].max():
            raise ValueError(f"dt={self.sqinfo['LastTradingDay'].max()}以前のみ対応")
        if large_mini not in ["large", "mini"]:
            raise ValueError(f"large_miniは'large' / 'mini'のみ指定してください。")

        # large / mini のフィルタ
        if large_mini == "large":
            sqinfo = self.sqinfo[~self.sqinfo["ContractMonth"].str.contains("W")]
        else:
            # miniの場合は全て対象
            sqinfo = self.sqinfo

        if 0 < maturity_n:
            sqinfo = sqinfo[sqinfo["LastTradingDay"] > dt]
        else:
            # マイナス限月の場合逆順にする
            sqinfo = sqinfo[sqinfo["LastTradingDay"] < dt].sort_values(
                "LastTradingDay", ascending=False
            )

        if sqinfo.shape[0] < abs(maturity_n):
            raise ValueError(f"{dt}の第{maturity_n}限月は存在しません")

        lasttradingday = sqinfo["LastTradingDay"].iloc[abs(maturity_n) - 1]
        sqdate = sqinfo["SpecialQuotationDay"].iloc[abs(maturity_n) - 1]
        contractmonth = sqinfo["ContractMonth"].iloc[abs(maturity_n) - 1]
        return lasttradingday, sqdate, contractmonth
