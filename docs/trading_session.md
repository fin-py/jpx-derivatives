# 取引時間管理モジュール

`trading_session.py`は日本取引所グループ（JPX）のデリバティブ取引における取引時間を管理するためのモジュールです。

## 概要

このモジュールは、JPXのデリバティブ商品（主に株価指数先物・オプション）の取引時間に関連する機能を提供します。

## 主要機能

```{eval-rst}
.. py:function:: load_trading_hours() -> Dict[str, Any]

   取引時間設定を返します。

   :return: 取引時間設定を含む辞書
```

```{eval-rst}
.. py:class:: TradingSession

   取引セッションを表す列挙型クラスです。

   .. py:attribute:: DAY
      
      日中取引セッション（8:45〜15:40）

   .. py:attribute:: DAY_CLOSING
      
      日中クロージングオークション（15:40〜15:45）

   .. py:attribute:: NIGHT
      
      夜間取引セッション（17:00〜5:55）

   .. py:attribute:: NIGHT_CLOSING
      
      夜間クロージングオークション（5:55〜6:00）

   .. py:attribute:: OFF_HOURS
      
      立会時間外
```

## 使用例

```python
from jpx_derivatives.trading_session import TradingSession, load_trading_hours

# 取引時間設定の取得
trading_hours = load_trading_hours()
print(trading_hours)

# 取引セッションの使用
current_session = TradingSession.DAY
if current_session == TradingSession.DAY:
    print("現在は日中取引セッションです")
```

出力例:
```
{
    'day_session': {'start': '08:45', 'end': '15:40'},
    'day_closing': {'start': '15:40', 'end': '15:45'},
    'night_session': {'start': '17:00', 'end': '05:55'},
    'night_closing': {'start': '05:55', 'end': '06:00'}
}
現在は日中取引セッションです
```

## 取引時間の設定

取引時間は以下のように定義されています：

- 日中取引: 8:45〜15:40
- 日中クロージングオークション: 15:40〜15:45
- 夜間取引: 17:00〜5:55
- 夜間クロージングオークション: 5:55〜6:00

## 取引セッション

`TradingSession` Enumは以下の取引セッションを定義しています：

- `DAY`: 日中取引
- `DAY_CLOSING`: 日中クロージングオークション
- `NIGHT`: 夜間取引
- `NIGHT_CLOSING`: 夜間クロージングオークション
- `OFF_HOURS`: 立会時間外

## 主要関数

### load_trading_hours()

取引時間設定を返します。
