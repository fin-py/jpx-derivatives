import datetime
import logging
import time
import urllib.error

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from jpx_derivatives.config import data_dir, setup_logging


def store_symbolcode() -> str:
    """
    先物の銘柄コード一覧を作成し、dataフォルダにsymbolcode_futures.parquetとして保存する

    Returns:
        エラーメッセージ、成功した場合は空文字
    """
    logger_name = setup_logging(__file__)
    logger = logging.getLogger(logger_name)

    year = datetime.datetime.now().year
    urls = [
        f"https://www.jpx.co.jp/derivatives/rules/last-trading-day/tvdivq0000004gz8-att/{year}_indexfutures_options_1_j.xlsx",
        f"https://www.jpx.co.jp/derivatives/rules/last-trading-day/tvdivq0000004gz8-att/{year + 1}_indexfutures_options_1_j.xlsx",
    ]

    spancode = {
        "日経225先物": "NK225F",
        "日経225mini": "NK225MF",
        "日経225マイクロ先物": "NK225MCF",
    }
    cols_rename = {
        "商品": "SPANcode",
        "限月取引": "ContractMonth",
        "9桁コード": "SymbolCode",
    }

    code_path = data_dir / "symbolcode_futures.parquet"
    if code_path.is_file():
        codes = pd.read_parquet(code_path)
    else:
        codes = pd.DataFrame()

    for i, url in enumerate(urls):
        for retry in range(3):
            try:
                raw_df = pd.read_excel(url, skiprows=1).iloc[:-2, 1:]
                break
            except urllib.error.HTTPError:
                logger.error(f"エクセル取得エラー{retry}: {url}")
            time.sleep(3)
        else:
            # 一つ目のURLでなければ問題ないこととする。次の年のファイルが作られていない可能性があるため
            if i != 0:
                continue
            msg = f"エクセル取得エラー: {url}"
            return msg

        df = raw_df[cols_rename.keys()].rename(columns=cols_rename).copy()
        df = df[df["SPANcode"].isin(spancode.keys())].copy()
        # 商品名からSPANcodeに変換
        df["SPANcode"] = df["SPANcode"].map(spancode)
        # datetimeから文字列に変換
        df["ContractMonth"] = pd.to_datetime(df["ContractMonth"]).dt.strftime("%Y-%m")

        codes = pd.concat([codes, df], axis=0)

        # 連続アクセスを防ぐため待機
        time.sleep(1)

    # 既にデータがあった場合を考慮して重複を除去
    codes = codes.drop_duplicates(subset=["SPANcode", "ContractMonth"], keep="last")
    codes = codes.sort_values(["SPANcode", "ContractMonth"])
    codes["SymbolCode"] = codes["SymbolCode"].astype(str)

    # 型を確実にするためにpaでtable作成してから出力
    table = pa.table(
        {
            "SPANcode": pa.array(codes["SPANcode"], type=pa.string()),
            "ContractMonth": pa.array(codes["ContractMonth"], type=pa.string()),
            "SymbolCode": pa.array(codes["SymbolCode"], type=pa.string()),
        }
    )
    pq.write_table(table, data_dir / "symbolcode_futures.parquet")
    return ""
