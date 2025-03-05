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
        """限月リストを取得する

        Returns:
            List[str]: 限月のリスト
        """
        pass

    @abstractmethod
    def get_last_trading_days(self) -> List[datetime.date]:
        """取引最終年月日リストを取得する

        Returns:
            List[datetime.date]: 取引最終年月日のリスト
        """
        pass

    @abstractmethod
    def get_special_quotation_days(self) -> List[datetime.date]:
        """SQ日リストを取得する

        Returns:
            List[datetime.date]: SQ日のリスト
        """
        pass

    @abstractmethod
    def get_interest_rates(self) -> List[float]:
        """理論価格計算用金利リストを取得する

        Returns:
            List[float]: 金利のリスト
        """
        pass


class HttpsStaticDataProvider(StaticDataProviderBase):
    """HTTPSリポジトリから静的データを取得するプロバイダー"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime = None,
        contract_frequency: str = "monthly",
    ):
        """
        Args:
            product_count (int): 限月数
            dt (datetime.datetime, optional): 日付。指定しない場合は現在の日付を使用
            contract_frequency (str, optional): 限月の取得頻度。デフォルトは "monthly"
        """
        self.product_count = product_count
        self.contract_frequency = contract_frequency
        if dt is None:
            self.dt = datetime.datetime.now()
        else:
            self.dt = dt

    def set_data(self, base_url: str):
        self.base_url = base_url
        self.sq_url = f"{self.base_url}/special_quotation.parquet"
        self.interest_rate_url = f"{self.base_url}/interest_rate_torf.parquet"
        yyyymmdd = f"{self.dt:%Y-%m-%d}"
        special_quotation = duckdb.read_parquet(self.sq_url)
        self.sq_data = self._fetch_sq_data(
            special_quotation, yyyymmdd, self.contract_frequency
        )

    def _fetch_sq_data(self, special_quotation, yyyymmdd, contract_frequency):
        """限月データを取得する共通メソッド

        Args:
            special_quotation: 特殊見積もりデータ
            yyyymmdd (str): 日付（YYYY-MM-DD形式）
            contract_frequency (str): 限月の取得頻度

        Returns:
            pd.DataFrame: 限月データのデータフレーム
        """
        if contract_frequency == "monthly":
            return (
                special_quotation.filter(f"SpecialQuotationDay > '{yyyymmdd}'")
                .filter("ContractMonth NOT LIKE '%-W%'")
                .order("SpecialQuotationDay")
                .limit(self.product_count)
                .df()
            )
        elif contract_frequency == "weekly":
            return (
                special_quotation.filter(f"SpecialQuotationDay > '{yyyymmdd}'")
                .order("SpecialQuotationDay")
                .limit(self.product_count)
                .df()
            )
        else:
            raise ValueError("Invalid contract frequency")

    def get_contract_months(self) -> List[str]:
        return self.sq_data.loc[:, "ContractMonth"].to_list()

    def get_last_trading_days(self) -> List[datetime.date]:
        return self.sq_data.loc[:, "LastTradingDay"].dt.date.to_list()

    def get_special_quotation_days(self) -> List[datetime.date]:
        return self.sq_data.loc[:, "SpecialQuotationDay"].dt.date.to_list()

    def get_interest_rates(self) -> List[float]:
        return [] * self.product_count


class GitHubStaticDataProvider(HttpsStaticDataProvider):
    """GitHubリポジトリから静的データを取得するプロバイダー"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime = None,
        contract_frequency: str = "monthly",
    ):
        super().__init__(product_count, dt, contract_frequency)
        self.set_data(
            "https://github.com/fin-py/jpx-derivatives/raw/refs/heads/main/data"
        )


class CloudflareR2StaticDataProvider(HttpsStaticDataProvider):
    """Cloudflare R2(public)から静的データを取得するプロバイダー"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime = None,
        contract_frequency: str = "monthly",
    ):
        super().__init__(product_count, dt, contract_frequency)
        self.set_data(
            "https://jpx-derivatives-public.quokka.trade"
        )


class AutoStaticDataProvider(StaticDataProviderBase):
    """r2を優先して使用し、例外が発生した場合はgithubにフォールバックするプロバイダー"""

    def __init__(
        self,
        product_count: int,
        dt: datetime.datetime = None,
        contract_frequency: str = "monthly",
    ):
        """
        Args:
            product_count (int): 限月数
            dt (datetime.datetime, optional): 日付。指定しない場合は現在の日付を使用
            contract_frequency (str, optional): 限月の取得頻度。デフォルトは "monthly"
        """
        self.product_count = product_count

        # まずr2を試す
        try:
            logger.debug("Trying to use CloudflareR2StaticDataProvider")
            self.provider = CloudflareR2StaticDataProvider(
                product_count, dt, contract_frequency
            )
        except Exception as e:
            # 例外が発生した場合はgithubにフォールバック
            logger.info(
                f"Failed to use CloudflareR2StaticDataProvider: {e}. Falling back to GitHubStaticDataProvider"
            )
            self.provider = GitHubStaticDataProvider(
                product_count, dt, contract_frequency
            )

    def get_contract_months(self) -> List[str]:
        return self.provider.get_contract_months()

    def get_last_trading_days(self) -> List[datetime.date]:
        return self.provider.get_last_trading_days()

    def get_special_quotation_days(self) -> List[datetime.date]:
        return self.provider.get_special_quotation_days()

    def get_interest_rates(self) -> List[float]:
        return self.provider.get_interest_rates()


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
        static_data_provider: str = "auto",
        data_provider: str = "public",
    ):
        static_providers = {
            "github": GitHubStaticDataProvider,
            "r2": CloudflareR2StaticDataProvider,
            "auto": AutoStaticDataProvider,
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
