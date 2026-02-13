import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
import plotly.express as px

# ページ設定
st.set_page_config(page_title="Dragon King Theory", layout="wide")

# --- サイバー・スタイル（ALL-CYBER BLUE） ---
st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, span, label {
        color: #00f2ff !important;
        font-family: 'Courier New', monospace;
    }
    .stApp {
        background-color: #050a14;
        background-image: radial-gradient(circle at 50% 50%, #112244 0%, #050a14 100%);
    }
    [data-testid="stSidebar"] {
        background-color: rgba(5, 10, 20, 0.95) !important;
        border-right: 1px solid #00f2ff;
    }
    .stMetric, .portfolio-card, .stExpander {
        background-color: rgba(16, 20, 35, 0.8) !important;
        border: 1px solid #00f2ff !important;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.3);
    }
    .portfolio-card {
        border: 2px solid #00f2ff !important;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.4);
        padding: 30px;
        margin-bottom: 30px;
    }
    [data-testid="stMetricValue"] {
        color: #00f2ff !important;
        text-shadow: 0 0 15px #00f2ff;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    h1 {
        color: #00f2ff !important;
        text-transform: uppercase;
        letter-spacing: 10px;
        text-shadow: 0 0 20px #00f2ff;
        text-align: center;
        font-size: 3.5rem !important;
        margin-bottom: 40px;
    }
    input, textarea, select, .stTextInput div, .stNumberInput div {
        background-color: #050a14 !important;
        color: #00f2ff !important;
        border-color: #00f2ff !important;
    }
    .stButton>button {
        width: 100%;
        background: transparent !important;
        color: #00f2ff !important;
        border: 1px solid #00f2ff !important;
    }
    .stButton>button:hover {
        background: #00f2ff !important;
        color: #050a14 !important;
        box-shadow: 0 0 20px #00f2ff;
    }
    .warning-text { color: #00f2ff !important; text-shadow: 0 0 10px #00f2ff; border: 1px dashed #00f2ff; text-align: center; padding: 20px; }
    .buy-zone { border: 2px solid #00ff00; color: #00ff00 !important; text-shadow: 0 0 10px #00ff00; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; }
    .sell-zone { border: 2px solid #ff4b4b; color: #ff4b4b !important; text-shadow: 0 0 10px #ff4b4b; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 最上部にタイトルを配置
st.markdown("<h1>DRAGON KING THEORY</h1>", unsafe_allow_html=True)

# --- サイドバー構成 ---
with st.sidebar:
    st.header("🔍 SCAN TARGETS")
    ticker_input = st.text_input("分析銘柄", value="XRP-USD, 7203.T, 3140.T, AAPL").upper()
    tickers = [t.strip() for t in ticker_input.split(",")]

    st.divider()
    st.header("🛸 FLEET DATA")
    if 'rows' not in st.session_state: st.session_state.rows = 3
    pf_data_list = []
    for i in range(st.session_state.rows):
        st.markdown(f"**Unit {i+1}**")
        col1, col2, col3 = st.columns([2, 1.5, 1.5])
        tick = col1.text_input("銘柄", value="XRP-USD" if i==0 else "", key=f"t_{i}")
        price = col2.number_input("単価", value=0.0, key=f"p_{i}")
        qty = col3.number_input("数量", value=0.0, key=f"q_{i}")
        if tick: pf_data_list.append({"銘柄": tick.upper(), "単価": price, "数量": qty})
    
    if st.button("🛰️ ADD UNIT"):
        st.session_state.rows += 1
        st.rerun()

    st.divider()
    st.header("🔔 ALERTS")
    alert_ticker = st.selectbox("対象", tickers)
    target_price = st.number_input("通知価格（以下）", value=0.0)

# --- 関数 ---
def get_live_pf(data_list):
    res = []
    t_cost, t_val = 0, 0
    for item in data_list:
        try:
            t, p, q = item["銘柄"], item["単価"], item["数量"]
            if q <= 0: continue
            df = yf.download(t, period="1d", progress=False)
            curr_p = float(df['Close'].iloc[-1])
            val, cost = curr_p * q, p * q
            res.append({"銘柄": t, "評価額": val, "損益": val - cost})
            t_cost += cost
            t_val += val
        except: continue
    return pd.DataFrame(res), t_cost, t_val

# --- メイン：ポートフォリオ表示 ---
st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
pf_df, total_cost, total_value = get_live_pf(pf_data_list)
if not pf_df.empty:
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    c1.metric("TOTAL VALUE", f"¥{total_value:,.0f}" if "T" in ticker_input else f"${total_value:,.2f}")
    c2.metric("TOTAL P/L", f"{(total_value-total_cost):,.2f}", delta=f"{((total_value-total_cost)/total_cost*100):.2f}%")
    fig_pie = px.pie(pf_df, values='評価額', names='銘柄', hole=.6)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00f2ff", height=180, showlegend=False)
    fig_pie.update_traces(marker=dict(colors=['#00f2ff', '#00d1ff', '#00a0ff', '#0070ff']))
    c3.plotly_chart(fig_pie, use_container_width=True)
else:
    st.markdown('<p class="warning-text">⚠️ SYSTEM READY: PLEASE ENTER FLEET DATA IN SIDEBAR.</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 個別分析：配当利回り追加 ---
for t_code in tickers:
    try:
        with st.expander(f"🛰️ SCANNING: {t_code}", expanded=True):
            stock = yf.Ticker(t_code)
            df = stock.history(start="2025-08-01")
            
            # 配当利回りの取得
            info = stock.info
            div_yield = info.get('dividendYield', 0)
            div_text = f"{div_yield * 100:.2f}%" if div_yield else "N/A"

            # RSI & LPPLS
            last_p = float(df['Close'].iloc[-1])
            delta = df['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]

            df_c = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_c['Date']]
            price = np.log(df_c['Close'].values.flatten())
            model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = model.fit(max_searches=20)
            crit_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # 表示
            if rsi < 30: st.markdown('<div class="buy-zone">🚀 BUY SIGNAL: DRAGON AWAKENING</div>', unsafe_allow_html=True)
            elif rsi > 70: st.markdown('<div class="sell-zone">⚠️ SELL SIGNAL: OVERHEATED</div>', unsafe_allow_html=True)

            ca, cb, cc = st.columns(3)
            ca.metric("PRICE", f"{last_p:,.2f}")
            cb.metric("DIV YIELD", div_text)
            cc.metric("X-DAY", crit_date)

            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00f2ff'))])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=200, margin=dict(l=0,r=0,t=0,b=0), font_color="#00f2ff", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#112244'))
            st.plotly_chart(fig, use_container_width=True)
    except: continue
