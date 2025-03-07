# Black-Scholes モデル

このモジュールでは、Black-Scholes モデルに基づいてオプション（コールおよびプット）の理論価格と各種指標（Greeks）を計算するための関数群を提供します。

## 基本関数

```{eval-rst}
.. py:function:: d1(s: float, k: float, t: float, r: float, sigma: float) -> float

   Black-Scholes モデルにおける d1 の値を計算します。

   計算式:
      d1 = (log(s / k) + (r + 0.5 * sigma^2) * t) / (sigma * sqrt(t))

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: 計算された d1 の値
```

```{eval-rst}
.. py:function:: d2(s: float, k: float, t: float, r: float, sigma: float) -> float

   Black-Scholes モデルにおける d2 の値を計算します。

   計算式:
      d2 = d1 - sigma * sqrt(t)

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: 計算された d2 の値
```

## オプション価格計算

```{eval-rst}
.. py:function:: price_call(s: float, k: float, t: float, r: float, sigma: float) -> float

   Black-Scholes モデルに基づき、コールオプションの理論価格を計算します。

   計算式:
      Call Price = s * N(d1) - k * exp(-r * t) * N(d2)

   ※ N(x) は標準正規分布の累積分布関数です。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: コールオプションの理論価格
```

```{eval-rst}
.. py:function:: price_put(s: float, k: float, t: float, r: float, sigma: float) -> float

   Black-Scholes モデルに基づき、プットオプションの理論価格を計算します。

   計算式:
      Put Price = k * exp(-r * t) * N(-d2) - s * N(-d1)

   ※ N(x) は標準正規分布の累積分布関数です。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: プットオプションの理論価格
```

## Greeks - オプションの感応度指標

```{eval-rst}
.. py:function:: vega(s: float, k: float, t: float, r: float, sigma: float) -> float

   オプションのベガ（ボラティリティの変化に対する感応度）を計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: オプションのベガ
```

```{eval-rst}
.. py:function:: delta_call(s: float, k: float, t: float, r: float, sigma: float) -> float

   コールオプションのデルタ（原資産価格の変化に対する感応度）を計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: コールオプションのデルタ
```

```{eval-rst}
.. py:function:: delta_put(s: float, k: float, t: float, r: float, sigma: float) -> float

   プットオプションのデルタ（原資産価格の変化に対する感応度）を計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: プットオプションのデルタ
```

```{eval-rst}
.. py:function:: delta(s: float, k: float, t: float, r: float, sigma: float, div: int) -> float

   オプションのデルタを計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :param div: オプションの種類（1: プット、2: コール）
   :return: オプションのデルタ
```

```{eval-rst}
.. py:function:: gamma(s: float, k: float, t: float, r: float, sigma: float) -> float

   オプションのガンマ（デルタの変化率）を計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: オプションのガンマ
```

```{eval-rst}
.. py:function:: theta_call(s: float, k: float, t: float, r: float, sigma: float) -> float

   コールオプションのシータ（時間経過に対する感応度）を計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: コールオプションのシータ
```

```{eval-rst}
.. py:function:: theta_put(s: float, k: float, t: float, r: float, sigma: float) -> float

   プットオプションのシータ（時間経過に対する感応度）を計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :return: プットオプションのシータ
```

```{eval-rst}
.. py:function:: theta(s: float, k: float, t: float, r: float, sigma: float, div: int) -> float

   オプションのシータを計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param sigma: ボラティリティ
   :param div: オプションの種類（1: プット、2: コール）
   :return: オプションのシータ
```

## インプライド・ボラティリティの計算

```{eval-rst}
.. py:function:: implied_volatility(s: float, k: float, t: float, r: float, price: float, div: int) -> float

   オプションの市場価格から暗示されるボラティリティを計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param price: オプションの市場価格
   :param div: オプションの種類（1: プット、2: コール）
   :return: インプライド・ボラティリティ
```

```{eval-rst}
.. py:function:: implied_volatility_call(s: float, k: float, t: float, r: float, price: float) -> float

   コールオプションの市場価格から暗示されるボラティリティを計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param price: コールオプションの市場価格
   :return: コールオプションのインプライド・ボラティリティ
```

```{eval-rst}
.. py:function:: implied_volatility_put(s: float, k: float, t: float, r: float, price: float) -> float

   プットオプションの市場価格から暗示されるボラティリティを計算します。

   
   :param s: 現在の株価
   :param k: オプションの行使価格
   :param t: 残存期間（年単位）
   :param r: 無リスク金利
   :param price: プットオプションの市場価格
   :return: プットオプションのインプライド・ボラティリティ
```

## 使用例

```python
import numpy as np
from jpx_derivatives.bsm import price_call, price_put, implied_volatility_call

# 基本的なパラメータ設定
s = 100      # 現在の株価
k = 100      # 行使価格
t = 1        # 残存期間（1年）
r = 0.05     # 無リスク金利 (5%)
sigma = 0.2  # ボラティリティ (20%)

# オプション価格の計算
call_price = price_call(s, k, t, r, sigma)
put_price = price_put(s, k, t, r, sigma)

print(f"コールオプション価格: {call_price:.4f}")
print(f"プットオプション価格: {put_price:.4f}")

# 市場価格からインプライド・ボラティリティを計算
market_price = 10.5
implied_vol = implied_volatility_call(s, k, t, r, market_price)
print(f"インプライド・ボラティリティ: {implied_vol:.4f} (約 {implied_vol*100:.2f}%)")
```

出力例:
```
コールオプション価格: 10.4506
プットオプション価格: 5.5739
インプライド・ボラティリティ: 0.2063 (約 20.63%)