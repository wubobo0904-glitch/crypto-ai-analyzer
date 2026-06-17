import streamlit as st
from binance.client import Client
import pandas as pd
import ta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=10000, key="refresh")

if "cash" not in st.session_state:
    st.session_state.cash = 10000

if "btc" not in st.session_state:
    st.session_state.btc = 0
if "trade_history" not in st.session_state:
    st.session_state.trade_history = []
st.title("🤖 AI Crypto Analyzer")

client = Client()
def backtest(df):

    balance = 10000
    position = 0
    return balance

def ema_strategy(df):
    signals = []

    for i in range(len(df)):
        if df["ema20"].iloc[i] > df["ema50"].iloc[i]:
            signals.append(1)
        else:
            signals.append(0)

    return signals


def rsi_strategy(df):
    signals = []

    for i in range(len(df)):
        if df["rsi"].iloc[i] < 30:
            signals.append(1)
        elif df["rsi"].iloc[i] > 70:
            signals.append(0)
        else:
            signals.append(0)

    return signals


def ema_rsi_strategy(df):
    signals = []

    for i in range(len(df)):
        if df["ema20"].iloc[i] > df["ema50"].iloc[i] and df["rsi"].iloc[i] < 70:
            signals.append(1)
        else:
            signals.append(0)

    return signals
def macd_strategy(df):
    signals = []

    for i in range(len(df)):
        if df["macd"].iloc[i] > df["macd_signal"].iloc[i]:
            signals.append(1)
        else:
            signals.append(0)

    return signals
def backtest_signal(df, signals):

    balance = 10000
    position = 0
    buy_price = 0

    trade_count = 0
    win_count = 0

    equity_curve = []

    for i in range(len(df)):

        price = df["close"].iloc[i]

        if signals[i] == 1 and position == 0:

            buy_price = price
            position = 1
            trade_count += 1

        elif signals[i] == 0 and position == 1:

            profit = price / buy_price

            if profit > 1:
                win_count += 1

            balance *= profit
            position = 0

        current_asset = balance

        if position == 1:
            current_asset = balance * price / buy_price

        equity_curve.append(current_asset)

    if position == 1:

        final_price = df["close"].iloc[-1]
        profit = final_price / buy_price

        if profit > 1:
            win_count += 1

        balance *= profit

    if trade_count > 0:
        win_rate = win_count / trade_count * 100
    else:
        win_rate = 0

    peak = equity_curve[0]
    max_drawdown = 0

    for asset in equity_curve:

        if asset > peak:
            peak = asset

        drawdown = (peak - asset) / peak * 100

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return balance, trade_count, win_rate, max_drawdown
def equity_curve(df, signals):

    balance = 10000
    position = 0
    buy_price = 0

    curve = []

    for i in range(len(df)):

        price = df["close"].iloc[i]

        if signals[i] == 1 and position == 0:
            buy_price = price
            position = 1

        elif signals[i] == 0 and position == 1:
            balance *= price / buy_price
            position = 0

        if position == 1:
            current_asset = balance * price / buy_price
        else:
            current_asset = balance

        curve.append(current_asset)

    return curve
symbol = st.text_input(
    "輸入幣種",
    "BTCUSDT"
)

if st.button("開始分析"):
    st.session_state.analyzed = True

if "analyzed" in st.session_state and st.session_state.analyzed:
    klines = client.get_klines(
        symbol=symbol.upper(),
        interval="1h",
        limit=200
    )

    df = pd.DataFrame(klines)

    df["close"] = df[4].astype(float)

    df["rsi"] = ta.momentum.RSIIndicator(
        df["close"]
    ).rsi()

    df["ema20"] = df["close"].ewm(
        span=20
    ).mean()

    df["ema50"] = df["close"].ewm(
        span=50
    ).mean()
    macd = ta.trend.MACD(df["close"])

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()
    df["future"] = (
    df["close"].shift(-1)
    > df["close"]
    ).astype(int)
    features = [
    "rsi",
    "ema20",
    "ema50",
    "macd",
    "macd_signal"
    ]

    from xgboost import XGBClassifier
    from sklearn.model_selection import train_test_split
    ai_df = df.dropna()

    X = ai_df[features]
    y = ai_df["future"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False
    )

    model = XGBClassifier()

    model.fit(
        X_train,
        y_train
    )
    latest_data = X.iloc[-1:]

    prediction = model.predict(
        latest_data
    )[0]

    prob = model.predict_proba(
        latest_data
    )[0][1]

    latest = df.iloc[-1]
    current_price = float(latest["close"])

    if latest["ema20"] > latest["ema50"] and latest["rsi"] < 70:
        signal = "BUY"

    elif latest["ema20"] < latest["ema50"] and latest["rsi"] > 30:
        signal = "SELL"

    else:
        signal = "HOLD"

    st.metric(
        "最新價格",
        round(latest["close"],2)
    )

    st.metric(
        "RSI",
        round(latest["rsi"],2)
    )
    st.metric("MACD", round(df["macd"].iloc[-1], 2))
    st.metric("MACD Signal", round(df["macd_signal"].iloc[-1], 2))

    st.success(
        f"交易訊號：{signal}"
    )
    st.subheader("🔔 訊號提醒")

    if signal == "BUY":
        st.warning("偵測到買進訊號：目前策略偏多，可以觀察進場機會")

    elif signal == "SELL":
        st.error("偵測到賣出訊號：目前策略偏空，注意風險")

    else:
        st.info("目前沒有明確訊號，建議先觀察")
    # K線圖

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=list(range(len(df))),
                open=df[1].astype(float),
                high=df[2].astype(float),
                low=df[3].astype(float),
                close=df[4].astype(float),
                name="BTC"
            )
        ]
    )

    fig.update_layout(
        title="K線圖",
        xaxis_title="K棒",
        yaxis_title="價格",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
    import plotly.express as px

    rsi_fig = px.line(
        x=list(range(len(df))),
        y=df["rsi"],
        title="RSI 指標"
    )

    rsi_fig.add_hline(y=70)
    rsi_fig.add_hline(y=30)

    st.plotly_chart(
        rsi_fig,
        use_container_width=True
    )
    macd_fig = px.line(
    x=list(range(len(df))),
    y=[df["macd"], df["macd_signal"]],
    title="MACD 指標"
    )

    st.plotly_chart(macd_fig, use_container_width=True)
    final_balance, trade_count, win_rate, max_drawdown = backtest_signal(
        df,
        ema_rsi_strategy(df)
    )

    profit = (
        (final_balance - 10000)
        / 10000
        * 100
    )

    st.subheader("📊 回測結果")
 

    st.metric("最終資金",round(final_balance, 2))
    st.metric("總報酬率",f"{profit:.2f}%")
    st.metric("交易次數", trade_count)
    st.metric("勝率", f"{win_rate:.2f}%")
    st.metric("最大回撤 MDD", f"{max_drawdown:.2f}%")

    st.subheader("💰 Paper Trading")

    st.write(f"現金：{st.session_state.cash:.2f} USDT")
    st.write(f"BTC持倉：{st.session_state.btc:.6f}")
   
    if st.button("模擬買進", key="buy_btn"):

        if st.session_state.cash > 0:

            st.session_state.btc = (
                st.session_state.cash
                / current_price
            )

            st.session_state.cash = 0

            st.session_state.trade_history.append({
                "動作": "買進",
                "價格": round(current_price, 2),
                "現金": round(st.session_state.cash, 2),
                "BTC": round(st.session_state.btc, 6)
            })

            st.success("買進成功")

    if st.button("模擬賣出", key="sell_btn"):

        if st.session_state.btc > 0:

            st.session_state.cash = (
                st.session_state.btc
                * current_price
            )

            st.session_state.btc = 0

            st.session_state.trade_history.append({
                "動作": "賣出",
                "價格": round(current_price, 2),
                "現金": round(st.session_state.cash, 2),
                "BTC": round(st.session_state.btc, 6)
            })

            st.success("賣出成功")

    total_asset = (
        st.session_state.cash
        + st.session_state.btc * current_price
    )

    paper_profit = (
        (total_asset - 10000)
        / 10000
        * 100
    )

    st.metric("總資產", f"{total_asset:.2f} USDT")
    st.metric("報酬率", f"{paper_profit:.2f}%")

    st.subheader("📜 交易紀錄")

    if len(st.session_state.trade_history) > 0:
        st.dataframe(st.session_state.trade_history)
    else:
        st.write("目前尚無交易紀錄")

    if st.button("重置模擬交易", key="reset_btn"):

        st.session_state.cash = 10000
        st.session_state.btc = 0
        st.session_state.trade_history = []

        st.success("已重置模擬交易")
        st.rerun()    
    st.subheader("🏆 多策略比較")

    ema_balance, ema_trades, ema_win, ema_mdd = backtest_signal(
        df,
        ema_strategy(df)
    )

    rsi_balance, rsi_trades, rsi_win, rsi_mdd = backtest_signal(
        df,
        rsi_strategy(df)
    )

    ema_rsi_balance, ema_rsi_trades, ema_rsi_win, ema_rsi_mdd = backtest_signal(
        df,
        ema_rsi_strategy(df)
    )

    strategy_results = {
        "EMA策略": {
            "balance": ema_balance,
            "trades": ema_trades,
            "win_rate": ema_win,
            "mdd": ema_mdd
        },
        "RSI策略": {
            "balance": rsi_balance,
            "trades": rsi_trades,
            "win_rate": rsi_win,
            "mdd": rsi_mdd
        },
        "EMA + RSI策略": {
            "balance": ema_rsi_balance,
            "trades": ema_rsi_trades,
            "win_rate": ema_rsi_win,
            "mdd": ema_rsi_mdd
        }
    }

    for name, data in strategy_results.items():

        profit = (
            (data["balance"] - 10000)
            / 10000
            * 100
        )

        st.write(
            f"{name}：報酬率 {profit:.2f}%｜"
            f"交易次數 {data['trades']}｜"
            f"勝率 {data['win_rate']:.2f}%｜"
            f"MDD {data['mdd']:.2f}%"
        )

    best_strategy = max(
        strategy_results,
        key=lambda name: strategy_results[name]["balance"]
    )

    st.success(f"最佳策略：{best_strategy}")
    st.subheader("📈 策略資金曲線")

    ema_curve = equity_curve(df, ema_strategy(df))
    rsi_curve = equity_curve(df, rsi_strategy(df))
    ema_rsi_curve = equity_curve(df, ema_rsi_strategy(df))

    curve_fig = go.Figure()

    curve_fig.add_trace(
        go.Scatter(
            x=list(range(len(ema_curve))),
            y=ema_curve,
            mode="lines",
            name="EMA策略"
        )
    )

    curve_fig.add_trace(
        go.Scatter(
            x=list(range(len(rsi_curve))),
            y=rsi_curve,
            mode="lines",
            name="RSI策略"
        )
    )

    curve_fig.add_trace(
        go.Scatter(
            x=list(range(len(ema_rsi_curve))),
            y=ema_rsi_curve,
            mode="lines",
            name="EMA + RSI策略"
        )
    )

    curve_fig.update_layout(
        title="多策略資金曲線",
        xaxis_title="K棒",
        yaxis_title="資金 USDT",
        height=500
    )

    st.plotly_chart(
        curve_fig,
        use_container_width=True
    )
    st.subheader("🤖 AI預測")

    st.metric(
        "上漲機率",
        f"{prob*100:.2f}%"
    )

    if prediction == 1:
        st.success("AI建議：BUY")
    else:
        st.error("AI建議：SELL")
    st.subheader("🤖 AI聊天分析師")

    user_question = st.text_input(
        "請輸入問題",
        placeholder="例如：BTC現在適合買嗎？"
    )
    if user_question:

        analysis = []

        if latest["rsi"] > 70:
            analysis.append("RSI過熱，短線可能回檔")

        elif latest["rsi"] < 30:
            analysis.append("RSI超賣，可能出現反彈")

        else:
            analysis.append("RSI位於正常區間")
        if latest["ema20"] > latest["ema50"]:
            analysis.append("EMA20位於EMA50之上，趨勢偏多")

        else:
            analysis.append("EMA20位於EMA50之下，趨勢偏空")
        if latest["macd"] > latest["macd_signal"]:
            analysis.append("MACD黃金交叉")

        else:
            analysis.append("MACD死亡交叉")
        buy_score = 0

        if latest["ema20"] > latest["ema50"]:
            buy_score += 1

        if latest["macd"] > latest["macd_signal"]:
            buy_score += 1

        if 30 < latest["rsi"] < 70:
            buy_score += 1
        st.write("### 🤖 AI分析結果")

        for item in analysis:
            st.write("•", item)

        st.write("---")

        st.write("### 🧠 AI模型判斷")

        st.metric(
            "上漲機率",
            f"{prob*100:.2f}%"
        )

        if prediction == 1:
            st.success("AI最終建議：BUY")
        else:
            st.error("AI最終建議：SELL")
