import datetime

import pandas as pd


class maturity_info_class:
    def __init__(self, sq_data: pd.DataFrame):
        """
        sq_data: special_quotation.parquet
        """
        self.sq_data = sq_data.copy()
        self.sq_data["LastTradingDay"] = pd.to_datetime(self.sq_data["LastTradingDay"])
        self.sq_data["SpecialQuotationDay"] = pd.to_datetime(
            self.sq_data["SpecialQuotationDay"]
        )
        # SQの時刻は9時
        self.sq_data["SpecialQuotationDay"] = self.sq_data["SpecialQuotationDay"].apply(
            lambda x: x.replace(hour=9, minute=0, second=0)
        )

        # 取引時刻が2024/11/5に変更
        self.sq_data["LastTradingDay"] = self.sq_data.apply(
            lambda row: (
                datetime.datetime.combine(row["LastTradingDay"], datetime.time(15, 15))
                if row["LastTradingDay"] < datetime.datetime(2024, 11, 5)
                else datetime.datetime.combine(
                    row["LastTradingDay"], datetime.time(15, 45)
                )
            ),
            axis=1,
        )

        # タイムゾーン情報を追加
        jst = datetime.timezone(datetime.timedelta(hours=9))
        self.sq_data["SpecialQuotationDay"] = self.sq_data[
            "SpecialQuotationDay"
        ].dt.tz_localize(jst)
        self.sq_data["LastTradingDay"] = self.sq_data["LastTradingDay"].dt.tz_localize(
            jst
        )

        self.sq_data = self.sq_data.sort_values("LastTradingDay")

    def get_contract_dates(
        self,
        dt: datetime.datetime,
        nth_contract_month: int,
        contract_frequency: str,
    ) -> tuple[datetime.datetime, datetime.datetime, str]:
        """
        渡されたdtの第[nth_contract_month]限月の最終取引日時とSQ日を返す。
        dt: 基準日時
        nth_contract_month: 2の場合第2限月を返す、マイナスも可
        contract_frequency: "monthly" / "weekly"
        return: lasttradingday, sqdate, contractmonth
        contractmonthは "2025-03", "2025-03-W5" など
        """
        # timezoneがなければ付与
        if dt.tzinfo is None:
            jst = datetime.timezone(datetime.timedelta(hours=9))
            dt = dt.replace(tzinfo=jst)
        if nth_contract_month == 0:
            raise ValueError(
                "nth_contract_monthは0以外で指定してください。（マイナスも可）"
            )
        # if dt < self.sq_data["LastTradingDay"].min():
        #    raise ValueError(f"dt={self.sq_data['LastTradingDay'].min()}以降のみ対応")
        if dt > self.sq_data["LastTradingDay"].max():
            raise ValueError(f"dt={self.sq_data['LastTradingDay'].max()}以前のみ対応")
        if contract_frequency not in ["monthly", "weekly"]:
            raise ValueError(
                "contract_frequencyは'monthly' / 'weekly'のみ指定してください。"
            )

        # monthly / weekly のフィルタ
        if contract_frequency == "monthly":
            sq_data = self.sq_data[
                ~self.sq_data["ContractMonth"].str.contains("W")
            ].copy()
        else:
            # weeklyの場合は全て対象
            sq_data = self.sq_data.copy()
            # weeklyの場合第２週にWを付ける
            sq_data["ContractMonth"] = sq_data["ContractMonth"].apply(
                lambda x: f"{x}-W2" if "W" not in x else x
            )

        if 0 < nth_contract_month:
            sq_data = sq_data[sq_data["LastTradingDay"] > dt]
        else:
            # マイナス限月の場合逆順にする
            sq_data = sq_data[sq_data["LastTradingDay"] < dt].sort_values(
                "LastTradingDay", ascending=False
            )

        if sq_data.shape[0] < abs(nth_contract_month):
            raise ValueError(f"{dt}の第{nth_contract_month}限月は存在しません")

        lasttradingday = sq_data["LastTradingDay"].iloc[abs(nth_contract_month) - 1]
        sqdate = sq_data["SpecialQuotationDay"].iloc[abs(nth_contract_month) - 1]
        contractmonth = sq_data["ContractMonth"].iloc[abs(nth_contract_month) - 1]
        return lasttradingday, sqdate, contractmonth
