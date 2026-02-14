import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King Diagnosis", layout="wide")

# --- サイバー・スタイル（メインアプリと統一） ---
st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #00f2ff !important;
        font-family: 'Courier New', monospace;
    }
    .stApp {
        background-color: #050a14;
        background-image: radial-gradient(circle at 50% 50%, #112244 0%, #050a14 100%);
    }
    .report-card {
        background-color: rgba(16, 20, 35, 0.9);
        border: 2px solid #00f2ff;
        border-radius: 15px;
        padding: 25px;
        margin-top: 20px;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
    }
    .status-ok { color: #00ff00; font-weight: bold; text-shadow: 0 0 5px #00ff00; }
    .status-warn { color: #ff4b4b; font-weight: bold; text-shadow: 0 0 5px #ff4b4b; }
    .status-info { color: #00f2ff; font-weight: bold; text-shadow: 0 0 5px #00f2ff; }
    
    /* ツールチップ（紺色） */
    div[data-baseweb="tooltip"] { background-color: #050a14 !important; border: 1px solid #00f2ff !important; }
    div[data-baseweb="tooltip"] * { color: #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- タイトル ---
st.markdown('<h1 style="text-align:center; letter-spacing:10px; text-shadow: 0 0 20px #00f2ff;">DIAGNOSIS TERMINAL</h1>', unsafe_allow_html=True)

# --- サイドバー：銘柄選択 ---
with st.sidebar:
    st.header("🔍 SCAN SETTINGS")
    # プリセットと自由入力を組み合わせ
    preset_ticker = st.selectbox("PRESET", ["XRP-USD", "BTC-USD", "7203.T", "3140.T", "AAPL", "CUSTOM"])
    
    if preset_ticker == "CUSTOM":
        ticker = st.text_input("ENTER TICKER", value="ETH-USD").upper()
    else:
        ticker = preset_ticker

    st.divider()
    st.info("LPPLS計算には一定期間のデータが必要です。銘柄によっては解析に時間がかかる場合があります。")

# --- 1. データ取得 ---
@st.cache_data(ttl=3600)
def load_data(symbol):
    data = yf.download(symbol, start="2025-08-01", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data[['Close']].dropna()

try:
    df = load_data(ticker)
    if df.empty:
        st.error(f"銘柄データが見つかりません: {ticker}")
        st.stop()

    # --- 2. 指標計算 ---
    # RSI
    window = 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # 25日移動平均線と乖離率
    df['MA25'] = df['Close'].rolling(window=25).mean()
    df['Divergence'] = ((df['Close'] - df['MA25']) / df['MA25']) * 100

    # --- 3. LPPLS計算 ---
    df_recent = df.reset_index()
    time = [pd.Timestamp.toordinal(d) for d in df_recent['Date']]
    price = np.log(df_recent['Close'].values.flatten())
    lppls_model = lppls.LPPLS(observations=np.array([time, price]))
    tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
    critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

    # --- 4. メトリクス表示 ---
    curr_p = df['Close'].iloc[-1]
    curr_rsi = df['RSI'].iloc[-1]
    curr_div = df['Divergence'].iloc[-1]
    today_str = pd.Timestamp.now().strftime('%Y-%m-%d')

    c1, c2, c3 = st.columns(3)
    c1.metric("CURRENT PRICE", f"{curr_p:,.2f}", help="現在の市場価格")
    c2.metric("RSI (14D)", f"{curr_rsi:.1f}%", help="30以下で売られすぎ（チャンス）、70以上で過熱（警戒）")
    c3.metric("MA25 DIV", f"{curr_div:.1f}%", help="25日移動平均線からの乖離率")

    # --- 5. 統合診断レポート ---
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader(f"📑 {ticker} INTEGRATED REPORT")

    diag_results = []
    # RSI
    if curr_rsi > 70: diag_results.append(f'<span class="status-warn">⚠️ 過熱:</span> RSIが70を超えています。短期的調整に注意。')
    elif curr_rsi < 30: diag_results.append(f'<span class="status-ok">✅ 好機:</span> RSIが30を下回っています。絶好の仕込み場です。')
    else: diag_results.append(f'<span class="status-info">📋 安定:</span> RSIは {curr_rsi:.1f}%。トレンドは継続または保ち合いです。')

    # 乖離率
    if abs(curr_div) > 15: diag_results.append(f'<span class="status-warn">⚠️ 乖離:</span> 平均から {curr_div:.1f}% 離脱。急激な揺り戻しを警戒。')
    else: diag_results.append(f'<span class="status-ok">📋 健全:</span> 移動平均線に近い安定した推移です。')

    # LPPLS
    if critical_date <= today_str: diag_results.append(f'<span class="status-ok">✅ 鎮静:</span> 直近の臨界点({critical_date})を通過。大きな崩壊リスクは後退。')
    else: diag_results.append(f'<span class="status-warn">⚠️ 臨界:</span> 次の臨界点 {critical_date} に向けてエネルギーが蓄積中。')

    for res in diag_results:
        st.markdown(f"- {res}", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. チャート描画 ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='#00f2ff', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA25'], name="MA25", line=dict(color='#ff00ff', dash='dash')))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00f2ff",
        height=400, margin=dict(l=0,r=0,t=20,b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#112244')
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"システムエラーが発生しました。銘柄名を確認してください。")
