import datetime
from io import StringIO

import pandas as pd
import pytest
import pytz

# テスト対象のクラスをインポート
from jpx_derivatives.check_maturity import maturity_info_class


# 更新されたテスト用データフレーム
@pytest.fixture
def sample_sq_data():
    data = """ContractMonth,SpecialQuotationDay,LastTradingDay,FinalSettlementPrices
2024-09,2024-09-13,2024-09-12,36906.92
2024-09-W1,2024-09-06,2024-09-05,36768.8
2024-09-W3,2024-09-20,2024-09-19,37876.02
2024-09-W4,2024-09-27,2024-09-26,39214.82
2024-10,2024-10-11,2024-10-10,39701.93
2024-10-W1,2024-10-04,2024-10-03,38544.47
2024-10-W3,2024-10-18,2024-10-17,39087.66
2024-10-W4,2024-10-25,2024-10-24,37960.31
2024-11,2024-11-08,2024-11-07,39901.35
2024-11-W1,2024-11-01,2024-10-31,38161.24
2024-11-W3,2024-11-15,2024-11-14,38718.98
2024-11-W4,2024-11-22,2024-11-21,38143.78
2024-11-W5,2024-11-29,2024-11-28,38176.09
2024-12,2024-12-13,2024-12-12,39434.85
2024-12-W1,2024-12-06,2024-12-05,39368.37
2024-12-W3,2024-12-20,2024-12-19,38978.32
2024-12-W4,2024-12-27,2024-12-26,39702.65
2025-01,2025-01-10,2025-01-09,39343.19
2025-01-W1,2025-01-03,2025-01-02,40310.49
2025-01-W3,2025-01-17,2025-01-16,38409.93
2025-01-W4,2025-01-24,2025-01-23,40066.13
2025-01-W5,2025-01-31,2025-01-30,39655.97"""

    return pd.read_csv(StringIO(data))


@pytest.fixture
def maturity_info(sample_sq_data):
    return maturity_info_class(sample_sq_data)


class TestMaturityInfoClass:
    def test_initialization(self, sample_sq_data):
        """maturity_info_classの初期化テスト"""
        # インスタンスを作成
        instance = maturity_info_class(sample_sq_data)

        # データフレームが正しくコピーされ修正されたことを確認
        assert isinstance(instance.sq_data, pd.DataFrame)
        assert "LastTradingDay" in instance.sq_data.columns
        assert "SpecialQuotationDay" in instance.sq_data.columns

        # タイムゾーンのローカライズを確認
        assert instance.sq_data["LastTradingDay"].iloc[0].tzinfo is not None
        assert instance.sq_data["SpecialQuotationDay"].iloc[0].tzinfo is not None

        # LastTradingDayの時間設定を確認（2024-11-05以前）
        early_date = instance.sq_data[
            instance.sq_data["LastTradingDay"]
            < datetime.datetime(2024, 11, 5, tzinfo=pytz.timezone("Asia/Tokyo"))
        ]
        assert early_date["LastTradingDay"].iloc[0].hour == 15
        assert early_date["LastTradingDay"].iloc[0].minute == 15

        # LastTradingDayの時間設定を確認（2024-11-05以降）
        late_date = instance.sq_data[
            instance.sq_data["LastTradingDay"]
            > datetime.datetime(2024, 11, 5, tzinfo=pytz.timezone("Asia/Tokyo"))
        ]
        assert late_date["LastTradingDay"].iloc[0].hour == 15
        assert late_date["LastTradingDay"].iloc[0].minute == 45

        # SpecialQuotationDayの時間設定を確認
        assert instance.sq_data["SpecialQuotationDay"].iloc[0].hour == 9
        assert instance.sq_data["SpecialQuotationDay"].iloc[0].minute == 0

    def test_get_contract_dates_monthly_positive(self, maturity_info):
        """月次限月で正のnth_contract_monthでget_contract_datesをテスト"""
        dt = datetime.datetime(
            2024, 9, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

        # 第1限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, 1, "monthly")
        assert cm == "2024-09"
        assert ltd.year == 2024 and ltd.month == 9 and ltd.day == 12
        assert sq.year == 2024 and sq.month == 9 and sq.day == 13

        # 第2限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, 2, "monthly")
        assert cm == "2024-10"
        assert ltd.year == 2024 and ltd.month == 10 and ltd.day == 10
        assert sq.year == 2024 and sq.month == 10 and sq.day == 11

    def test_get_contract_dates_monthly_negative(self, maturity_info):
        """月次限月で負のnth_contract_monthでget_contract_datesをテスト"""
        dt = datetime.datetime(
            2024, 12, 20, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

        # 直近の前限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, -1, "monthly")
        assert cm == "2024-12"
        assert ltd.year == 2024 and ltd.month == 12 and ltd.day == 12
        assert sq.year == 2024 and sq.month == 12 and sq.day == 13

        # 2つ前の限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, -2, "monthly")
        assert cm == "2024-11"
        assert ltd.year == 2024 and ltd.month == 11 and ltd.day == 7
        assert sq.year == 2024 and sq.month == 11 and sq.day == 8

    def test_get_contract_dates_weekly_positive(self, maturity_info):
        """週次限月で正のnth_contract_monthでget_contract_datesをテスト"""
        dt = datetime.datetime(
            2024, 10, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

        # 第1週次限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, 1, "weekly")
        assert cm == "2024-10-W1"
        assert ltd.year == 2024 and ltd.month == 10 and ltd.day == 3
        assert sq.year == 2024 and sq.month == 10 and sq.day == 4

        # 第2週次限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, 2, "weekly")
        assert cm == "2024-10-W2"
        assert ltd.year == 2024 and ltd.month == 10 and ltd.day == 10
        assert sq.year == 2024 and sq.month == 10 and sq.day == 11

    def test_get_contract_dates_weekly_negative(self, maturity_info):
        """週次限月で負のnth_contract_monthでget_contract_datesをテスト"""
        dt = datetime.datetime(
            2025, 1, 20, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

        # 直近の前週次限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, -1, "weekly")
        assert cm == "2025-01-W3"
        assert ltd.year == 2025 and ltd.month == 1 and ltd.day == 16
        assert sq.year == 2025 and sq.month == 1 and sq.day == 17

        # 2つ前の週次限月をテスト
        ltd, sq, cm = maturity_info.get_contract_dates(dt, -2, "weekly")
        assert cm == "2025-01-W2"
        assert ltd.year == 2025 and ltd.month == 1 and ltd.day == 9
        assert sq.year == 2025 and sq.month == 1 and sq.day == 10

    def test_get_contract_dates_timezone_handling(self, maturity_info):
        """関数がタイムゾーン情報を正しく処理することをテスト"""
        # タイムゾーン情報のない日時でテスト
        dt_naive = datetime.datetime(2024, 10, 1)
        ltd, sq, cm = maturity_info.get_contract_dates(dt_naive, 1, "monthly")
        assert ltd.tzinfo is not None
        assert sq.tzinfo is not None

        # タイムゾーン情報のある日時でテスト
        jst = datetime.timezone(datetime.timedelta(hours=9))
        dt_aware = datetime.datetime(2024, 10, 1, tzinfo=jst)
        ltd, sq, cm = maturity_info.get_contract_dates(dt_aware, 1, "monthly")
        assert ltd.tzinfo is not None
        assert sq.tzinfo is not None

    def test_get_contract_dates_errors(self, maturity_info):
        """get_contract_datesのエラーケースをテスト"""
        dt = datetime.datetime(
            2024, 10, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

        # nth_contract_month = 0 でテスト
        with pytest.raises(
            ValueError, match="nth_contract_monthは0以外で指定してください"
        ):
            maturity_info.get_contract_dates(dt, 0, "monthly")

        # 利用可能なデータを超える将来の日付でテスト
        future_dt = datetime.datetime(
            2026, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )
        with pytest.raises(ValueError, match="以前のみ対応"):
            maturity_info.get_contract_dates(future_dt, 1, "monthly")

        # 無効なcontract_frequencyでテスト
        with pytest.raises(
            ValueError,
            match="contract_frequencyは'monthly' / 'weekly'のみ指定してください",
        ):
            maturity_info.get_contract_dates(dt, 1, "quarterly")

        # 範囲外のnth_contract_monthでテスト
        with pytest.raises(ValueError, match="限月は存在しません"):
            maturity_info.get_contract_dates(dt, 100, "monthly")

    def test_handling_of_non_weekly_contracts(self, maturity_info):
        """週次頻度を使用する場合に月次限月が正しくW2でラベル付けされることをテスト"""
        dt = datetime.datetime(
            2024, 9, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

        # 週次限月をリクエストする場合、月次限月はW2のサフィックスが付けられるべき
        ltd, sq, cm = maturity_info.get_contract_dates(dt, 1, "weekly")
        assert cm == "2024-09-W1"  # 新しいデータセットではW1が最初の週次限月

        # 月次限月を含むケース
        dt = datetime.datetime(
            2024, 9, 7, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )
        ltd, sq, cm = maturity_info.get_contract_dates(dt, 1, "weekly")
        assert cm == "2024-09-W2"  # 月次限月にW2サフィックスが追加される

    def test_november_trading_time_change(self, maturity_info):
        """2024年11月5日前後の取引時間変更が正しく反映されているかテスト"""
        # 11月5日以前の限月
        early_contract = maturity_info.get_contract_dates(
            datetime.datetime(
                2024, 9, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
            ),
            1,
            "monthly",
        )
        assert early_contract[0].hour == 15
        assert early_contract[0].minute == 15

        # 11月5日以降の限月
        late_contract = maturity_info.get_contract_dates(
            datetime.datetime(
                2024, 11, 10, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
            ),
            1,
            "monthly",
        )
        assert late_contract[0].hour == 15
        assert late_contract[0].minute == 45
