import os
import math
from datetime import datetime
import time
import asyncio

from playwright.async_api import async_playwright, TimeoutError
from scipy.interpolate import CubicSpline
import duckdb

from config import logging, setup_logging, data_dir


def interpolate_interest_rate(
    data_interest_rate: dict[int, float], target_remain_days: list[float]
) -> dict[float, float]:
    """
    ブラックショールズモデルで使用するための金利を線形補完で推測するメソッド
    data_interest_rate: 取得した金利データ（年利）
    target_remain_days: 推測したい残存日数
    Returns: key=残存日数、value=補間された連続複利の金利
    """
    remain_days_known = list(data_interest_rate.keys())
    annual_rates_known = list(data_interest_rate.values())
    cs = CubicSpline(
        remain_days_known, annual_rates_known, bc_type="natural", extrapolate=True
    )
    # 残存日数に合わせて金利を補間
    annual_rates = cs(target_remain_days)

    # 年利から連続複利に変換して返す
    result = {
        days: math.log(1 + annual_rate)
        for days, annual_rate in zip(target_remain_days, annual_rates)
    }
    return result


async def get_interest_rate_torf(
    logger: logging.Logger,
) -> tuple[datetime, dict[int, float]]:
    """
    TORFから金利取得 1M/3M/6M
    Returns datetime: 金利の適用日付
    Returns dict: key=残存日数、value=金利
    空の辞書が返るときはスクレイピングエラー
    """
    url = "https://moneyworld.jp/page/torf.html"
    # TORF 1M/3M/6M
    xpaths = {
        30: '//*[@id="contents"]/div/div[1]/div[3]/div[2]/table/tbody/tr[3]/td[2]/span',
        90: '//*[@id="contents"]/div/div[1]/div[3]/div[2]/table/tbody/tr[3]/td[4]/span',
        180: '//*[@id="contents"]/div/div[1]/div[3]/div[2]/table/tbody/tr[3]/td[6]/span',
    }
    # date
    date_xpath = (
        '//*[@id="contents"]/div/div[1]/div[3]/div[2]/table/tbody/tr[2]/td[2]/span'
    )

    async with async_playwright() as p:
        chromium_args = [
            "--blink-settings=imagesEnabled=false",
            "--disable-remote-fonts",
        ]
        browser = await p.chromium.launch(headless=True, args=chromium_args)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url)
            # 値が読み込まれるまで待機
            await page.wait_for_selector(f"xpath={date_xpath}", timeout=20000)
        except TimeoutError:
            msg = f"InterestRate TORF Timeout ERROR date"
            logger.error(msg)
            return datetime.now(), {}
        date_element = await page.query_selector(date_xpath)
        if not date_element:
            msg = f"InterestRate TORF ERROR date"
            logger.error(msg)
            return datetime.now(), {}
        date_str = await date_element.inner_text()
        target_date = datetime.strptime(date_str, "%Y/%m/%d")

        data = {}
        for tenor, xpath in xpaths.items():
            try:
                # 値が読み込まれるまで待機
                await page.wait_for_selector(f"xpath={xpath}", timeout=20000)
            except TimeoutError:
                msg = f"InterestRate TORF Timeout ERROR {data}"
                logger.error(msg)
                return target_date, {}

            specific_element = await page.query_selector(xpath)

            if not specific_element:
                msg = f"InterestRate TORF ERROR {tenor}"
                logger.error(msg)
                return target_date, {}
            # 金利の値取得
            value = await specific_element.inner_text()
            data[tenor] = float(value)

        await context.close()
        await browser.close()
    return target_date, data


def output_interest_rate_parquet(
    data_interest_rate: dict[int, float], target_date: datetime
) -> bool:
    """
    金利データをparquetファイルに出力する。ファイルがあればデータを更新
    """
    file_path = str(data_dir / "interest_rate_torf.parquet")

    # データが存在するか確認
    if os.path.exists(file_path):
        result = duckdb.sql(
            f"SELECT InterestRate1M FROM '{file_path}' WHERE date = '{target_date}'"
        ).fetchone()
    else:
        result = None

    if result is not None:
        interest_rate_latest = result[0]
        is_interest_rate_exist = interest_rate_latest is not None
    else:
        interest_rate_latest = None
        is_interest_rate_exist = False

    # データが更新されていなければ終了
    if is_interest_rate_exist:
        logger.info("データは最新です, 処理を終了します")
        return True

    con = duckdb.connect(database=":memory:")
    if os.path.exists(file_path):
        con.execute(f"CREATE TABLE interest_rate_torf AS SELECT * FROM '{file_path}'")
    else:
        con.execute(
            "CREATE TABLE interest_rate_torf ("
            "date DATE"
            ", InterestRate1M FLOAT"
            ", InterestRate3M FLOAT"
            ", InterestRate6M FLOAT)"
        )

    logger.info(
        f"TORFの金利を更新します, 日付: {target_date} 金利: {data_interest_rate}"
    )
    con.execute(
        f"INSERT INTO interest_rate_torf VALUES ("
        f"'{target_date}'"
        f", {data_interest_rate[30]}"
        f", {data_interest_rate[90]}"
        f", {data_interest_rate[180]})"
    )
    logger.info(f"{file_path} に書き込みます")
    con.sql(f"COPY (SELECT * FROM interest_rate_torf) TO '{file_path}'")
    return True


if __name__ == "__main__":
    logger_name = setup_logging(__file__)
    logger = logging.getLogger(logger_name)

    # 3回リトライする
    for _ in range(3):
        target_date, data_interest_rate = asyncio.run(get_interest_rate_torf(logger))
        # 失敗した場合時間をおいてリトライ
        if len(data_interest_rate) == 0:
            time.sleep(10)
            continue
        break
    else:
        raise ValueError(f"TORF金利スクレイピングエラー")

    output_interest_rate_parquet(data_interest_rate, target_date)
