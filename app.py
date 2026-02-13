import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
from datetime import datetime

# ページ設定
st.set_page_config(page_title="ドラゴン検知ダッシュボード", layout="wide")

st.title("🐉 ドラゴン検知ダッシュボード")
st.sidebar.header("設定")

# 1. 銘柄選択
target_list = {
    "XRP-USD": "リップル (XRP)",
    "BTC-USD": "ビットコイン (BTC)",
    "1514.T": "住石HD",
    "241A.T": "ROXX",
    "6495.T": "宮入バルブ",
    "9432.T": "NTT"
}
selected_ticker = st.sidebar.selectbox("銘柄を選択してください", list(target_list.keys()), format_func=lambda x: target_list[x])

# 2. RSI計算関数
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 3. データ取得と計算
with st.spinner('データを分析中...'):
    df = yf.download(selected_ticker, start="2025-09-01", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 指標計算
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

# 4. メイン表示 (KPIカード)
col1, col2, col3 = st.columns(3)
latest = df.iloc[-1]

with col1:
    st.metric("臨界点 (X-Day)", critical_date, 
              delta="過去" if critical_date <= datetime.now().strftime('%Y-%m-%d') else "要警戒",
              delta_color="normal" if critical_date <= datetime.now().strftime('%Y-%m-%d') else "inverse")
with col2:
    st.metric("RSI (14日)", f"{latest['RSI']:.2f}%", 
              delta="売られすぎ" if latest['RSI'] < 30 else ("買われすぎ" if latest['RSI'] > 70 else "適正"))
with col3:
    st.metric("25日線乖離率", f"{latest['Div']:.2f}%")

# 5. グラフ表示 (Plotly)
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="価格"))
fig.add_trace(go.Scatter(x=df.index, y=df['MA25'], name="25日移動平均線", line=dict(dash='dash')))
st.plotly_chart(fig, use_container_width=True)

st.success(f"診断完了: {target_list[selected_ticker]} は現在、科学的に『{'待機' if latest['RSI'] < 30 else '観察'}』フェーズです。")
