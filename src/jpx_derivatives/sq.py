import logging
import sys

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from config import data_dir, setup_logging
from dateutil.relativedelta import relativedelta
from lxml import html

logger_name = setup_logging(__file__)
logger = logging.getLogger(logger_name)
holidays = pd.read_parquet(data_dir / "holidays.parquet").loc[:, "Date"].to_list()


def drift_trading_date(dt: pd.Timestamp) -> pd.Timestamp:
    if dt.date() not in holidays:
        return dt
    else:
        for _ in range(7):
            dt = dt - pd.DateOffset(days=1)
            if dt.date() not in holidays:
                return dt


def get_special_quotation_day(contract_month: str):
    contract_month_split = contract_month.split("-")
    if len(contract_month_split) == 2:
        sq_day = (
            pd.Timestamp(contract_month)
            + relativedelta(weekday=4)
            + pd.DateOffset(days=7)
        )
        return drift_trading_date(sq_day)
    elif len(contract_month_split) == 3:
        y, m, w = contract_month_split
        shift_days = (int(w.replace("W", "")) - 1) * 7
        first_day = pd.Timestamp(f"{y}-{m}") + relativedelta(weekday=4)
        sq_day = first_day + relativedelta(days=shift_days)
        return drift_trading_date(sq_day)
    else:
        raise ValueError


def fill_na_days(df: pd.DataFrame) -> pd.DataFrame:
    sq_days_raw = df.loc[:, "SpecialQuotationDay"]
    sq_na_days = sq_days_raw[sq_days_raw.isna()]
    sq_na_days.loc[:] = sq_na_days.index.map(get_special_quotation_day)
    sq_days = pd.concat([sq_days_raw.dropna(), sq_na_days]).sort_index()
    last_trading_days_raw = df.loc[:, "LastTradingDay"]
    last_trading_na_days = last_trading_days_raw[last_trading_days_raw.isna()]
    last_trading_na_days.loc[:] = (
        pd.concat([sq_days, last_trading_na_days], axis=1, join="inner").loc[
            :, "SpecialQuotationDay"
        ]
        - pd.DateOffset(days=1)
    ).map(drift_trading_date)
    last_trading_days = pd.concat(
        [last_trading_days_raw.dropna(), last_trading_na_days]
    ).sort_index()
    return pd.concat(
        [df.loc[:, "FinalSettlementPrices"], sq_days, last_trading_days], axis=1
    ).sort_index()


def get_historical_sq_month() -> pd.DataFrame:
    import camelot

    tables = camelot.read_pdf(
        "https://www.jpx.co.jp/markets/derivatives/special-quotation/mklp7700000028jz-att/sq_his.pdf",
        pages="all",
    )
    raw_df = pd.concat([table.df.iloc[1:, :2] for table in tables]).iloc[:, :2]
    contract_month = []
    year = int(tables[0].df.iloc[1, 0].split("年")[0])
    for row in raw_df.iloc[:, 0]:
        if "年" in row:
            row_split = row.split("年")
            year = int(row_split[0])
            month = int(row_split[1].replace("月", ""))
        else:
            month = int(row.replace("月", ""))
        contract_month.append(f"{year}-{month:02}")

    final_settlement_prices = (
        raw_df.loc[:, 1].map(lambda x: float(x.replace(",", ""))).tolist()
    )
    return pd.DataFrame(
        {
            "ContractMonth": contract_month,
            "FinalSettlementPrices": final_settlement_prices,
        }
    )


def get_historical_sq_week() -> pd.DataFrame:
    import camelot

    tables = camelot.read_pdf(
        "https://www.jpx.co.jp/markets/derivatives/special-quotation/mklp7700000028jz-att/sq_his(mini,weekly).pdf",
        pages="all",
        flavor="stream",
    )
    raw_df = (
        pd.concat([table.df.iloc[2:, :] for table in tables])
        .reset_index(drop=True)
        .set_axis(["ym", "w", "sq"], axis=1)
    )
    ym = (
        raw_df.loc[:, "ym"]
        .replace("", pd.NA)
        .ffill()
        .str.split("年", expand=True)
        .set_axis(["y", "m"], axis=1)
    )
    year = ym.loc[:, "y"].astype(int)
    month = ym.loc[:, "m"].str.replace("月", "").astype(int)
    week = raw_df.loc[:, "w"].str.replace("第", "").str.replace("週", "").astype(int)
    ymw = pd.concat([year, month, week], axis=1)
    contract_month = ymw.apply(lambda x: f"{x.y}-{x.m:02}-W{x.w}", axis=1)
    final_settlement_prices = raw_df.loc[:, "sq"].str.replace(",", "").astype(float)
    return pd.DataFrame(
        {
            "ContractMonth": contract_month,
            "FinalSettlementPrices": final_settlement_prices,
        }
    )


def _get_trading_day(url: str) -> pd.DataFrame:
    raw_df = pd.read_excel(
        url,
        skiprows=1,
    ).iloc[:-2, 1:]
    option = raw_df.groupby("商品").get_group("日経225オプション")
    contract_month_option_ = pd.to_datetime(option.loc[:, "限月取引"])
    contract_month_option = pd.DataFrame(
        {"y": contract_month_option_.dt.year, "m": contract_month_option_.dt.month}
    ).apply(lambda x: f"{x.y}-{x.m:02}", axis=1)
    trading_day_option = pd.DataFrame(
        {
            "ContractMonth": contract_month_option,
            "SpecialQuotationDay": pd.to_datetime(option.loc[:, "権利行使日"]),
            "LastTradingDay": pd.to_datetime(option.loc[:, "取引最終日"]),
        }
    )
    mini_option = raw_df.groupby("商品").get_group("日経225ミニオプション")
    y_mw = (
        mini_option.loc[:, "限月取引"]
        .str.split("年", expand=True)
        .set_axis(["y", "mw"], axis=1)
    )
    mw = y_mw.loc[:, "mw"].str.split("月", expand=True).set_axis(["m", "w"], axis=1)
    ymw = pd.DataFrame(
        {
            "y": y_mw.loc[:, "y"].astype(int),
            "m": mw.loc[:, "m"].astype(int),
            "w": mw.loc[:, "w"]
            .str.replace("第", "")
            .str.replace("週限", "")
            .astype(int),
        }
    )
    contract_month_mini_option = ymw.apply(lambda x: f"{x.y}-{x.m:02}-W{x.w}", axis=1)
    trading_day_mini_option = pd.DataFrame(
        {
            "ContractMonth": contract_month_mini_option,
            "SpecialQuotationDay": pd.to_datetime(mini_option.loc[:, "権利行使日"]),
            "LastTradingDay": pd.to_datetime(mini_option.loc[:, "取引最終日"]),
        }
    )
    return pd.concat([trading_day_option, trading_day_mini_option]).reset_index(
        drop=True
    )


def get_trading_day() -> pd.DataFrame:
    return pd.concat(
        [
            _get_trading_day(
                "https://www.jpx.co.jp/derivatives/rules/last-trading-day/tvdivq0000004gz8-att/2025_indexfutures_options_1_j.xlsx"
            ),
            _get_trading_day(
                "https://www.jpx.co.jp/derivatives/rules/last-trading-day/tvdivq0000004gz8-att/2026_indexfutures_options_1_j.xlsx"
            ),
        ]
    ).reset_index(drop=True)


def get_historical_data() -> pd.DataFrame:
    historical_sq_month = get_historical_sq_month().set_index("ContractMonth")
    historical_sq_week = get_historical_sq_week().set_index("ContractMonth")
    trading_day = get_trading_day().set_index("ContractMonth")
    df = pd.concat(
        [pd.concat([historical_sq_month, historical_sq_week]), trading_day], axis=1
    )
    return df.drop(df.index[df.index.str.endswith("-W2")]).sort_index()


def store_historical_data() -> None:
    df = fill_na_days(get_historical_data()).reset_index(drop=False)
    table = pa.table(
        {
            "ContractMonth": pa.array(df.loc[:, "ContractMonth"], type=pa.string()),
            "SpecialQuotationDay": pa.array(
                df.loc[:, "SpecialQuotationDay"], type=pa.date32()
            ),
            "LastTradingDay": pa.array(df.loc[:, "LastTradingDay"], type=pa.date32()),
            "FinalSettlementPrices": pa.array(
                df.loc[:, "FinalSettlementPrices"], type=pa.float32()
            ),
        }
    )
    pq.write_table(table, data_dir / "special_quotation.parquet")


def get_sq_data() -> tuple[int] | int:
    """
    SQ値を取得する
    https://www.jpx.co.jp/markets/derivatives/special-quotation/index.html
    """
    res = requests.get(
        "https://www.jpx.co.jp/markets/derivatives/special-quotation/index.html"
    )
    tree = html.fromstring(res.content)
    product_category_1 = tree.xpath(
        '//*[@id="readArea"]//div[@class="component-normal-table"]//table/tbody/tr[2]/td[1]'
    )[0].text_content()
    product_category_2 = tree.xpath(
        '//*[@id="readArea"]//div[@class="component-normal-table"]//table/tbody/tr[3]/td[1]'
    )[0].text_content()

    try:
        assert product_category_1.startswith("日経225")
        assert product_category_2.startswith("日経225ミニオプション")
    except AssertionError:
        logger.error(
            "Webサイトの構成が変更されている可能性があります, https://www.jpx.co.jp/markets/derivatives/special-quotation/index.html"
        )
        return 1

    sq_date_n225 = tree.xpath('//*[@id="readArea"]//div[@class="component-normal-table"]//table/tbody/tr[2]/td[2]')[
        0
    ].text_content()
    sq_date_n225_mini = tree.xpath(
        '//*[@id="readArea"]//div[@class="component-normal-table"]//table/tbody/tr[3]/td[2]'
    )[0].text_content()
    sq_n225_raw = tree.xpath('//*[@id="readArea"]//div[@class="component-normal-table"]//table/tbody/tr[2]/td[3]')[
        0
    ].text_content()
    sq_n225_mini_raw = tree.xpath(
        '//*[@id="readArea"]//div[@class="component-normal-table"]//table/tbody/tr[3]/td[3]'
    )[0].text_content()
    sq_n225 = float(sq_n225_raw.replace(",", ""))
    sq_n225_mini = float(sq_n225_mini_raw.replace(",", ""))
    return sq_date_n225, sq_n225, sq_date_n225_mini, sq_n225_mini


def update_data() -> int:
    """
    SQ値を更新する
    https://www.jpx.co.jp/markets/derivatives/special-quotation/index.html
    """
    file_path = str(data_dir / "special_quotation.parquet")
    sq_date_n225, sq_n225, sq_date_n225_mini, sq_n225_mini = get_sq_data()

    logger.info(f"日経225 SQ日: {sq_date_n225}, SQ値 {sq_n225}")
    logger.info(f"日経225ミニオプション SQ日: {sq_date_n225_mini}, SQ値 {sq_n225_mini}")

    n225_latest = duckdb.sql(
        f"SELECT FinalSettlementPrices FROM '{file_path}' WHERE SpecialQuotationDay = '{sq_date_n225}'"
    ).fetchone()[0]
    n225_mini_latest = duckdb.sql(
        f"SELECT FinalSettlementPrices FROM '{file_path}' WHERE SpecialQuotationDay = '{sq_date_n225_mini}'"
    ).fetchone()[0]
    is_n225_value_exist = n225_latest is not None
    is_n225_mini_value_exist = n225_mini_latest is not None

    # データが更新されていなければ終了
    if all((is_n225_value_exist, is_n225_mini_value_exist)):
        logger.info("データは最新です, 処理を終了します")
        return 0

    con = duckdb.connect(database=":memory:")
    con.execute(f"CREATE TABLE special_quotation AS SELECT * FROM '{file_path}'")
    if not is_n225_value_exist:
        logger.info(f"日経225のSQ値を更新します, SQ日: {sq_date_n225} SQ値: {sq_n225}")
        con.execute(
            f"UPDATE special_quotation SET FinalSettlementPrices = {sq_n225} WHERE SpecialQuotationDay = '{sq_date_n225}'"
        )
    if not is_n225_mini_value_exist:
        logger.info(
            f"日経225ミニオプションのSQ値を更新します, SQ日: {sq_date_n225_mini} SQ値: {sq_n225_mini}"
        )
        con.execute(
            f"UPDATE special_quotation SET FinalSettlementPrices = {sq_n225_mini} WHERE SpecialQuotationDay = '{sq_date_n225_mini}'"
        )
    logger.info(f"{file_path} に書き込みます")
    con.sql(f"COPY (SELECT * FROM special_quotation) TO '{file_path}'")
    return 0


if __name__ == "__main__":
    # store_historical_data()
    code = update_data()
    sys.exit(code)
