# クライアントモジュール

`client.py`は、日本取引所グループ(JPX)のデリバティブデータを取得するためのメインインターフェースを提供します。

## 概要

このモジュールは、JPXのデリバティブ商品（主に株価指数先物・オプション）に関連する静的データと動的データを取得するための機能を提供します。

## 主要クラス

```{eval-rst}
.. py:class:: Client(product_count: int, dt: datetime.datetime = None, contract_frequency: str = "monthly", static_data_provider: str = "auto", data_provider: str = "public")

   JPXデリバティブデータ取得用のメインクラス。

   :param product_count: 取得する限月の数
   :param dt: 基準日（省略時は現在の日付）
   :param contract_frequency: 限月の取得頻度（"monthly"または"weekly"）
   :param static_data_provider: 静的データプロバイダーの種類（"github"、"r2"、または"auto"）
   :param data_provider: データプロバイダーの種類（"public"または"private"）

   .. py:method:: get_contract_months() -> List[str]
      
      限月リストを取得します。

   .. py:method:: get_last_trading_days() -> List[datetime.date]
      
      取引最終年月日リストを取得します。

   .. py:method:: get_special_quotation_days() -> List[datetime.date]
      
      SQ日リストを取得します。

   .. py:method:: get_interest_rates() -> List[float]
      
      理論価格計算用金利リストを取得します。

   .. py:method:: get_current_value(code: str) -> float
      
      指定された銘柄コードの現在値を取得します。

      :param code: 銘柄コード（例: "101" = 日経225先物）
```

## 使用例

```python
from jpx_derivatives.client import Client

# クライアントの初期化
client = Client(product_count=3)

# 限月リストの取得
contract_months = client.get_contract_months()
print(f"限月: {contract_months}")

# 日経225先物の現在値を取得
current_value = client.get_current_value("101")
print(f"日経225先物の現在値: {current_value}")
```

出力例:
```
限月: ['2025-03', '2025-04', '2025-05']
日経225先物の現在値: 38500.0