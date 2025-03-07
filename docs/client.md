# Client クラス

`Client`クラスは、日本取引所グループ(JPX)のデリバティブデータを取得するためのメインインターフェースです。

## 概要

このクラスは、JPXのデリバティブ商品（主に株価指数先物・オプション）に関連する静的データと動的データを取得するための機能を提供します。静的データの提供には、GitHubまたはCloudflare R2のリポジトリを使用し、必要に応じて自動的に適切なデータソースを選択します。

## 初期化

```python
Client(
    product_count: int,
    dt: datetime.datetime = None,
    contract_frequency: str = "monthly",
    static_data_provider: str = "auto",
    data_provider: str = "public"
)
```

**パラメータ:**

: `product_count`
  : int型。取得する限月の数。

: `dt`
  : datetime.datetime型（省略可能）。基準日。指定しない場合は現在の日付を使用。

: `contract_frequency`
  : str型（省略可能）。限月の取得頻度。"monthly"（毎月）または"weekly"（毎週）を指定。デフォルトは "monthly"。

: `static_data_provider`
  : str型（省略可能）。静的データプロバイダーの種類。"github"、"r2"、または"auto"を指定。デフォルトは "auto"。

: `data_provider`
  : str型（省略可能）。データプロバイダーの種類。"public"または"private"を指定。デフォルトは "public"。

## メソッド

### get_contract_months()

限月リストを取得します。限月は、デリバティブ商品の取引期限を表す識別子です。

例えば、「2023-03」は2023年3月限を表します。週次商品の場合は「2023-03-W1」のように「-W」が付加されます。

**戻り値:**

: List[str]
  : 限月のリスト（例: ["2023-03", "2023-04", "2023-05", ...]）

**使用例:**
```python
client = Client(product_count=3)
contract_months = client.get_contract_months()
print(contract_months)  # 例: ["2025-03", "2025-04", "2025-05"]
```

### get_last_trading_days()

取引最終年月日リストを取得します。取引最終日は、各限月の商品が取引される最後の日付です。

**戻り値:**

: List[datetime.date]
  : 取引最終年月日のリスト

**使用例:**
```python
client = Client(product_count=3)
last_trading_days = client.get_last_trading_days()
print(last_trading_days)  # 例: [datetime.date(2025, 3, 14), datetime.date(2025, 4, 11), ...]
```

### get_special_quotation_days()

SQ日（特別清算指数算出日）リストを取得します。SQ日は、デリバティブ商品の最終決済価格を決定するための特別な清算指数が算出される日です。通常は取引最終日の翌営業日に設定されます。

**戻り値:**

: List[datetime.date]
  : SQ日のリスト

**使用例:**
```python
client = Client(product_count=3)
sq_days = client.get_special_quotation_days()
print(sq_days)  # 例: [datetime.date(2025, 3, 17), datetime.date(2025, 4, 14), ...]
```

### get_interest_rates()

理論価格計算用金利リストを取得します。この金利は、デリバティブ商品の理論価格を計算する際に使用されます。

**戻り値:**

: List[float]
  : 金利のリスト（パーセント単位）

**使用例:**
```python
client = Client(product_count=3)
interest_rates = client.get_interest_rates()
print(interest_rates)  # 例: [0.12, 0.13, 0.14]
```

### get_current_value(code: str)

指定された銘柄コードの現在値を取得します。これは価格データを提供するプロバイダーから取得されます。

**パラメータ:**

: `code`
  : str型。銘柄コード（例: "101" = 日経225先物）

**戻り値:**

: float
  : 現在値（現在の市場価格）

**使用例:**
```python
client = Client(product_count=3)
current_value = client.get_current_value("101")  # 日経225先物の現在値
print(current_value)  # 例: 38500.0
```

## 使用例

### 基本的な使用方法

```python
import datetime
from jpx_derivatives.client import Client

# 3限月分のデータを取得するクライアントを初期化
client = Client(product_count=3)

# 限月リストを取得
contract_months = client.get_contract_months()
print(f"限月: {contract_months}")

# 取引最終日を取得
last_trading_days = client.get_last_trading_days()
print(f"取引最終日: {last_trading_days}")

# SQ日を取得
sq_days = client.get_special_quotation_days()
print(f"SQ日: {sq_days}")

# 日経225先物（銘柄コード: 101）の現在値を取得
current_value = client.get_current_value("101")
print(f"日経225先物の現在値: {current_value}")
```

### 異なるデータプロバイダーの指定

```python
# GitHubから静的データを取得するクライアント
github_client = Client(
    product_count=3,
    static_data_provider="github"
)

# Cloudflare R2から静的データを取得するクライアント
r2_client = Client(
    product_count=3,
    static_data_provider="r2"
)

# 週次限月データを取得するクライアント
weekly_client = Client(
    product_count=6,
    contract_frequency="weekly"
)