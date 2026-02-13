import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
from datetime import datetime

# ページ設定
st.set_page_config(page_title="ドラゴン検知ダッシュボード", layout="wide")

st.title("🐉 全資産対応：科学的投資診断")
st.sidebar.header("診断ターゲット入力")

# 1. 使いやすい入力ガイド
st.sidebar.markdown("""
**【入力ルールのヒント】**
- **日本株:** `7203.T` (トヨタ)
- **米国株:** `AAPL` (アップル), `TSLA` (テスラ)
- **仮想通貨:** `BTC-USD`, `ETH-USD`, `XRP-USD`
- **指数:** `^N225` (日経平均), `^GSPC` (S&P500)
""")

# 2. 自由入力ボックス
ticker_input = st.sidebar.text_input("ティッカーシンボルを入力", value="XRP-USD").upper()

# --- 共通計算ロジック ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

try:
    with st.spinner(f'{ticker_input} を解析中...'):
        # 過去半年分のデータを取得
        df = yf.download(ticker_input, start="2025-08-01", progress=False)
        
        if df.empty:
            st.error("データが見つかりません。シンボルが正しいか確認してください。")
            st.stop()
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df['RSI'] = calculate_rsi(df['Close'])
        df['MA25'] = df['Close'].rolling(window=25).mean()
        df['Div'] = ((df['Close'] - df['MA25']) / df['MA25']) * 100
        
        # LPPLS計算
        df_clean = df[['Close']].dropna().reset_index()
        time = [pd.Timestamp.toordinal(d) for d in df_clean['Date']]
        price = np.log(df_clean['Close'].values.flatten())
        lppls_model = lppls.LPPLS(observations=np.array([time, price]))
        tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
        critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

    # メイン画面の表示
    st.subheader(f"📊 {ticker_input} 分析結果")
    
    col1, col2, col3 = st.columns(3)
    latest = df.iloc[-1]
    
    # 判定ロジック
    status = "📋 観察"
    if latest['RSI'] < 30: status = "🔥 絶好の買い場 (売られすぎ)"
    elif latest['RSI'] > 70: status = "⚠️ 警戒 (買われすぎ)"

    with col1:
        st.metric("臨界点 (LPPLS)", critical_date)
    with col2:
        st.metric("RSI (14日)", f"{latest['RSI']:.2f}%", help="30以下で売られすぎ")
    with col3:
        st.metric("25日線乖離率", f"{latest['Div']:.2f}%")

    st.info(f"【総合判定】 {status}")

    # グラフ表示
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="価格"))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA25'], name="25日移動平均", line=dict(dash='dash', color='orange')))
    fig.update_layout(title=f"{ticker_input} 価格推移と25日線", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"分析エラー: {e}")
