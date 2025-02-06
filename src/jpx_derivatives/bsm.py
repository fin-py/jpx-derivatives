"""
Black-Scholes モデルによるオプション評価モジュール

このモジュールでは、Black-Scholes モデルに基づいてオプション（コールおよびプット）の理論価格を計算する関数群を提供します。

提供される関数:
  - d1(s, k, t, r, sigma): オプション評価における d1 の値を計算します。
  - d2(s, k, t, r, sigma): d1 の値から d2 を計算します。
  - price_call(s, k, t, r, sigma): コールオプションの理論価格を計算します。
  - price_put(s, k, t, r, sigma): プットオプションの理論価格を計算します。

使用例:
    >>> import numpy as np
    >>> from bsm import price_call, price_put
    >>> s = 100      # 現在の株価
    >>> k = 100      # 行使価格
    >>> t = 1        # 残存期間（1年）
    >>> r = 0.05     # 無リスク金利 (5%)
    >>> sigma = 0.2  # ボラティリティ (20%)
    >>> call_price = price_call(s, k, t, r, sigma)
    >>> put_price = price_put(s, k, t, r, sigma)
"""

import numpy as np
from scipy.optimize import fsolve
from scipy.stats import norm


def d1(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    Black-Scholes モデルにおける d1 の値を計算します。

    計算式:
        d1 = (log(s / k) + (r + 0.5 * sigma^2) * t) / (sigma * sqrt(t))

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: 計算された d1 の値
    """
    return (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))


def d2(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    Black-Scholes モデルにおける d2 の値を計算します。

    計算式:
        d2 = d1 - sigma * sqrt(t)

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: 計算された d2 の値
    """
    d1_value = d1(s, k, t, r, sigma)
    return d1_value - sigma * np.sqrt(t)


def price_call(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    Black-Scholes モデルに基づき、コールオプションの理論価格を計算します。

    計算式:
        Call Price = s * N(d1) - k * exp(-r * t) * N(d2)
      ※ N(x) は scipy.stats.norm.cdf により計算される標準正規分布の累積分布関数です。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: コールオプションの理論価格
    """
    if t <= 0:
        return max(0, s - k)
    
    d1_value = d1(s, k, t, r, sigma)
    d2_value = d2(s, k, t, r, sigma)
    return s * norm.cdf(d1_value) - k * np.exp(-r * t) * norm.cdf(d2_value)


def price_put(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    Black-Scholes モデルに基づき、プットオプションの理論価格を計算します。

    計算式:
        Put Price = k * exp(-r * t) * N(-d2) - s * N(-d1)
      ※ N(x) は scipy.stats.norm.cdf により計算される標準正規分布の累積分布関数です。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: プットオプションの理論価格
    """
    if t <= 0:
        return max(0, k - s)
    
    d1_value = d1(s, k, t, r, sigma)
    d2_value = d2(s, k, t, r, sigma)
    return k * np.exp(-r * t) * norm.cdf(-d2_value) - s * norm.cdf(-d1_value)


def vega(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    オプションのベガ（ボラティリティの変化に対する感応度）を計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: オプションのベガ
    """
    d1_value = d1(s, k, t, r, sigma)
    return s * norm.pdf(d1_value) * np.sqrt(t)


def delta_call(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    コールオプションのデルタ（原資産価格の変化に対する感応度）を計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: コールオプションのデルタ
    """
    d1_value = d1(s, k, t, r, sigma)
    return norm.cdf(d1_value)


def delta_put(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    プットオプションのデルタ（原資産価格の変化に対する感応度）を計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: プットオプションのデルタ
    """
    d1_value = d1(s, k, t, r, sigma)
    return norm.cdf(d1_value) - 1


def delta(s: float, k: float, t: float, r: float, sigma: float, div: int) -> float:
    """
    オプションのデルタを計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ
        div (int): オプションの種類（1: プット、2: コール）

    Returns:
        float: オプションのデルタ
    """
    return {1: delta_put, 2: delta_call}[div](s, k, t, r, sigma)


def gamma(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    オプションのガンマ（デルタの変化率）を計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: オプションのガンマ
    """
    d1_value = d1(s, k, t, r, sigma)
    return norm.pdf(d1_value) / (s * sigma * np.sqrt(t))


def theta_call(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    コールオプションのシータ（時間経過に対する感応度）を計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: コールオプションのシータ
    """
    d1_value = d1(s, k, t, r, sigma)
    d2_value = d2(s, k, t, r, sigma)
    return (-s * norm.pdf(d1_value) * sigma / (2 * np.sqrt(t))) - (
        r * k * np.exp(-r * t) * norm.cdf(d2_value)
    )


def theta_put(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    プットオプションのシータ（時間経過に対する感応度）を計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ

    Returns:
        float: プットオプションのシータ
    """
    d1_value = d1(s, k, t, r, sigma)
    d2_value = d2(s, k, t, r, sigma)
    return (-s * norm.pdf(d1_value) * sigma / (2 * np.sqrt(t))) + (
        r * k * np.exp(-r * t) * norm.cdf(-d2_value)
    )


def theta(s: float, k: float, t: float, r: float, sigma: float, div: int) -> float:
    """
    オプションのシータを計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        sigma (float): ボラティリティ
        div (int): オプションの種類（1: プット、2: コール）

    Returns:
        float: オプションのシータ
    """
    return {1: theta_put, 2: theta_call}[div](s, k, t, r, sigma)


def implied_volatility(s: float, k: float, t: float, r: float, price: float, div: int) -> float:
    """
    オプションの市場価格から暗示されるボラティリティを計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        price (float): オプションの市場価格
        div (int): オプションの種類（1: プット、2: コール）

    Returns:
        float: インプライド・ボラティリティ
    """
    def find_volatility(sigma):
        return {1: price_put, 2: price_call}[div](s, k, t, r, sigma) - price

    sigma0 = np.sqrt(abs(np.log(s / k) + r * t) * 2 / t)
    return fsolve(find_volatility, sigma0)[0]


def implied_volatility_call(s: float, k: float, t: float, r: float, price: float) -> float:
    """
    コールオプションの市場価格から暗示されるボラティリティを計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        price (float): コールオプションの市場価格

    Returns:
        float: コールオプションのインプライド・ボラティリティ
    """
    return implied_volatility(s, k, t, r, price, 2)


def implied_volatility_put(s: float, k: float, t: float, r: float, price: float) -> float:
    """
    プットオプションの市場価格から暗示されるボラティリティを計算します。

    Args:
        s (float): 現在の株価
        k (float): オプションの行使価格
        t (float): 残存期間（年単位）
        r (float): 無リスク金利
        price (float): プットオプションの市場価格

    Returns:
        float: プットオプションのインプライド・ボラティリティ
    """
    return implied_volatility(s, k, t, r, price, 1)
