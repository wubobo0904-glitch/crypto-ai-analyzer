print("🚀 程式開始")

from binance.client import Client
import pandas as pd
import ta

client = Client()

# 1️⃣ 抓資料
def get_data():

    klines = client.get_klines(
        symbol="BTCUSDT",
        interval="1h",
        limit=200
    )

    df = pd.DataFrame(klines)
    df["close"] = df[4].astype(float)

    return df

df = get_data()

# 2️⃣ 技術指標
df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
df["ema20"] = df["close"].ewm(span=20).mean()
df["ema50"] = df["close"].ewm(span=50).mean()

# 3️⃣ 交易訊號（重點）
def signal(row):

    if row["ema20"] > row["ema50"] and row["rsi"] < 70:
        return "BUY"

    elif row["ema20"] < row["ema50"] and row["rsi"] > 30:
        return "SELL"

    else:
        return "HOLD"

df["signal"] = df.apply(signal, axis=1)

# 4️⃣ 輸出結果
print("💰 最新價格：", df["close"].iloc[-1])
print("📊 RSI：", df["rsi"].iloc[-1])
print("📈 EMA20：", df["ema20"].iloc[-1])
print("📉 EMA50：", df["ema50"].iloc[-1])
print("🎯 最新訊號：", df["signal"].iloc[-1])

print("✅ 完成")