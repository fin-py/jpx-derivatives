import datetime
import logging
from abc import ABC, abstractmethod
from typing import List

import duckdb
import pandas as pd

from jpx_derivatives.config import setup_logging

# ロガーの設定
logger_name = setup_logging(__file__)
logger = logging.getLogger(logger_name)


class StaticDataProviderBase(ABC):
    """静的データ（限月情報など）を提供する抽象基底クラス"""

    @abstractmethod
    def get_contract_months(self) -> List[str]:
        """限月リストを取得する"""
        pass

    @abstractmethod
    def get_last_trading_days(self) -> List[datetime.date]:
        """取引最終年月日リストを取得する"""
        pass

    @abstractmethod
    def get_special_quotation_days(self) -> List[datetime.date]:
        """SQ日リストを取得する"""
        pass

    @abstractmethod
    def get_interest_rates(self) -> List[float]:
        """理論価格計算用金利リストを取得する"""
        pass


class GitHubStaticDataProvider(StaticDataProviderBase):
    """GitHubリポジトリから静的データを取得するプロバイダー"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime = None,
        contract_frequency: str = "monthly",
    ):
        """
        Args:
            product_count: 限月数
        """
        self.product_count = product_count
        self.base_url = (
            "https://github.com/fin-py/jpx-derivatives/raw/refs/heads/main/data/"
        )
        self.sq_url = f"{self.base_url}/special_quotation.parquet"
        self.interest_rate_url = f"{self.base_url}/interest_rate_torf.parquet"
        if dt is None:
            dt = datetime.datetime.now()

        yyyymmdd = f"{dt:%Y-%m-%d}"
        special_quotation = duckdb.read_parquet(self.sq_url)
        if contract_frequency == "monthly":
            self.sq_data = (
                special_quotation.filter(f"SpecialQuotationDay > '{yyyymmdd}'")
                .filter("ContractMonth NOT LIKE '%-W%'")
                .order("SpecialQuotationDay")
                .limit(self.product_count)
                .df()
            )
        elif contract_frequency == "weekly":
            self.sq_data = (
                special_quotation.filter(f"SpecialQuotationDay > '{yyyymmdd}'")
                .filter("ContractMonth NOT LIKE '%-W%'")
                .order("SpecialQuotationDay")
                .limit(self.product_count)
                .df()
            )
        else:
            raise ValueError

    def get_contract_months(self) -> List[str]:
        return self.sq_data.loc[:, "ContractMonth"].to_list()

    def get_last_trading_days(self) -> List[datetime.date]:
        return self.sq_data.loc[:, "LastTradingDay"].dt.date.to_list()

    def get_special_quotation_days(self) -> List[datetime.date]:
        return self.sq_data.loc[:, "SpecialQuotationDay"].dt.date.to_list()

    def get_interest_rates(self) -> List[float]:
        return [] * self.product_count


class CloudflareR2StaticDataProvider(StaticDataProviderBase):
    """Cloudflare R2(public)から静的データを取得するプロバイダー"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime,
        contract_frequency: str = "monthly",
    ):
        self.product_count = product_count

    def get_contract_months(self) -> List[str]:
        return [] * self.product_count

    def get_last_trading_days(self) -> List[datetime.date]:
        return [] * self.product_count

    def get_special_quotation_days(self) -> List[datetime.date]:
        return [] * self.product_count

    def get_interest_rates(self) -> List[float]:
        return [] * self.product_count


class DataProviderBase(ABC):
    """動的データ（価格情報など）を提供する抽象基底クラス"""

    @abstractmethod
    def get_current_value(self, code: str) -> pd.DataFrame:
        """現在値を取得する"""
        pass


class CloudflareR2PublicDataProvider(DataProviderBase):
    def get_current_value(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()


class CloudflareR2PrivateDataProvider(DataProviderBase):
    def get_current_value(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()


class Client:
    """デリバティブデータ取得クライアント"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime = None,
        contract_frequency: str = "monthly",
        static_data_provider: str = "github",
        data_provider: str = "public",
    ):
        static_providers = {
            "github": GitHubStaticDataProvider,
            "r2": CloudflareR2StaticDataProvider,
        }
        data_providers = {
            "public": CloudflareR2PublicDataProvider,
            "private": CloudflareR2PrivateDataProvider,
        }

        self.static_provider = static_providers[static_data_provider](
            product_count, dt, contract_frequency
        )
        self.data_provider = data_providers[data_provider]()

    def get_contract_months(self) -> List[str]:
        return self.static_provider.get_contract_months()

    def get_last_trading_days(self) -> List[datetime.date]:
        return self.static_provider.get_last_trading_days()

    def get_special_quotation_days(self) -> List[datetime.date]:
        return self.static_provider.get_special_quotation_days()

    def get_interest_rates(self) -> List[float]:
        return self.static_provider.get_interest_rates()

    def get_current_value(self, code: str) -> pd.DataFrame:
        return self.data_provider.get_current_value(code)

