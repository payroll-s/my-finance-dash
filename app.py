import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ultimate Dragon Hunter", layout="wide")

# スタイル設定（CSSで少し豪華に）
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    .buy-zone { background-color: #004d00; border: 2px solid #00ff00; padding: 20px; border-radius: 10px; }
    .sell-zone { background-color: #4d0000; border: 2px solid #ff0000; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🐉 究極・ドラゴン検知システム v2.0")

# --- サイドバー ---
st.sidebar.header("🔍 ターゲット指定")
ticker_input = st.sidebar.text_input("複数入力（カンマ区切り）もOK", value="XRP-USD, 7203.T, AAPL").upper()
tickers = [t.strip() for t in ticker_input.split(",")]

# --- 計算関数 ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- メインループ ---
for ticker in tickers:
    try:
        with st.expander(f"📉 {ticker} の詳細診断結果を表示", expanded=True):
            df = yf.download(ticker, start="2025-08-01", progress=False)
            if df.empty:
                st.warning(f"データ取得不可: {ticker}")
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 指標計算
            df['RSI'] = calculate_rsi(df['Close'])
            df['MA25'] = df['Close'].rolling(window=25).mean()
            df['Div'] = ((df['Close'] - df['MA25']) / df['MA25']) * 100
            latest = df.iloc[-1]
            
            # LPPLS
            df_clean = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_clean['Date']]
            price = np.log(df_clean['Close'].values.flatten())
            lppls_model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
            critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # --- 日本株限定：配当取得 ---
            div_info = ""
            if ticker.endswith(".T"):
                info = yf.Ticker(ticker).info
                yield_val = info.get('dividendYield', 0)
                if yield_val:
                    div_info = f" | 💰 予想配当利回り: {yield_val*100:.2f}%"

            # --- 判定演出 ---
            if latest['RSI'] < 30:
                st.markdown(f'<div class="buy-zone">🚀 <b>絶好の買い場シグナル！</b> (RSI: {latest["RSI"]:.1f}%){div_info}</div>', unsafe_allow_html=True)
            elif latest['RSI'] > 70:
                st.markdown(f'<div class="sell-zone">⚠️ <b>警戒・利益確定ゾーン！</b> (RSI: {latest["RSI"]:.1f}%){div_info}</div>', unsafe_allow_html=True)
            else:
                st.info(f"📋 現在は「静観・観察」フェーズです。{div_info}")

            # --- メトリクス表示 ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("現在価格", f"{latest['Close']:.2f}")
            c2.metric("臨界点 (X-Day)", critical_date)
            c3.metric("RSI (14日)", f"{latest['RSI']:.1f}%")
            c4.metric("25日線乖離率", f"{latest['Div']:.1f}%")

            # --- グラフ表示 ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='#00d1ff')))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA25'], name="25MA", line=dict(dash='dash', color='#ff9900')))
            fig.update_layout(height=400, template="plotly_dark", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"エラー分析 ({ticker}): {e}")
