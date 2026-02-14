import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- スタイル設定（既存のアプリと共通） ---
st.markdown("""
    <style>
    .report-card {
        background-color: rgba(16, 20, 35, 0.9);
        border: 2px solid #00f2ff;
        border-radius: 15px;
        padding: 25px;
        margin-top: 20px;
    }
    .status-ok { color: #00ff00; font-weight: bold; }
    .status-warn { color: #ff4b4b; font-weight: bold; }
    .status-info { color: #00f2ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ XRP INTEGRATED DIAGNOSIS")

# 1. データ取得
ticker = "XRP-USD"
df = yf.download(ticker, start="2025-10-01", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df = df[['Close']].dropna()

# 2. 指標計算
# RSI計算
window = 14
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
df['RSI'] = 100 - (100 / (1 + (gain / loss)))

# 25日移動平均線と乖離率
df['MA25'] = df['Close'].rolling(window=25).mean()
df['Divergence'] = ((df['Close'] - df['MA25']) / df['MA25']) * 100

# 3. LPPLS計算
df_recent = df.reset_index()
time = [pd.Timestamp.toordinal(d) for d in df_recent['Date']]
price = np.log(df_recent['Close'].values.flatten())
observations = np.array([time, price])
lppls_model = lppls.LPPLS(observations=observations)
tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=40)
critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

# 4. メトリクス表示
current_price = df['Close'].iloc[-1]
current_rsi = df['RSI'].iloc[-1]
current_div = df['Divergence'].iloc[-1]
today_str = pd.Timestamp.now().strftime('%Y-%m-%d')

col1, col2, col3 = st.columns(3)
col1.metric("CURRENT PRICE", f"${current_price:.4f}")
col2.metric("RSI (14D)", f"{current_rsi:.2f}%", help="30以下で買い、70以上で売り")
col3.metric("MA25 DIV", f"{current_div:.1f}%", help="25日移動平均線からの離れ具合")

# 5. 統合診断レポート
st.markdown(f'<div class="report-card">', unsafe_allow_html=True)
st.subheader(f"📑 統合診断レポート ({today_str})")

# 判定ロジックの可視化
results = []

# RSI判定
if current_rsi > 70:
    results.append(f'<span class="status-warn">⚠️ 注意:</span> RSIが70を超え「過熱状態」にあります。反落リスクに警戒。')
elif current_rsi < 30:
    results.append(f'<span class="status-ok">✅ チャンス:</span> RSIが30を下回り「売られすぎ」の状態です。絶好の仕込み場。')
else:
    results.append(f'<span class="status-info">📋 中立:</span> RSIは {current_rsi:.1f}%。過熱感はなく、安定圏内です。')

# 乖離率判定
if abs(current_div) > 15:
    results.append(f'<span class="status-warn">⚠️ 注意:</span> 25日線から {current_div:.1f}% 離れています。価格が平均に引き寄せられる「揺り戻し」に注意。')
else:
    results.append(f'<span class="status-ok">📋 安定:</span> 移動平均線に近い健全な価格帯を維持しています。')

# LPPLS判定
if critical_date <= today_str:
    results.append(f'<span class="status-ok">✅ 鎮静:</span> 臨界点({critical_date})を通過しました。バブル崩壊の急落リスクは現時点で低下しています。')
else:
    results.append(f'<span class="status-warn">⚠️ 警戒:</span> 次の臨界点が未来 ({critical_date}) に予測されています。この日に向けてトレンドの急変が起こる可能性があります。')

# 結果の出力
for res in results:
    st.markdown(f"- {res}", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 6. チャート描画
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="XRP Price", line=dict(color='#00f2ff')))
fig.add_trace(go.Scatter(x=df.index, y=df['MA25'], name="MA25", line=dict(color='#ff00ff', dash='dash')))
fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color="#00f2ff", height=300, margin=dict(l=0,r=0,t=20,b=0),
    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#112244')
)
st.plotly_chart(fig, use_container_width=True)
