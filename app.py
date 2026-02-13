import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
import plotly.express as px

# ページ設定
st.set_page_config(page_title="Dragon Cyber Terminal", layout="wide")

# --- サイバー・スタイル（宇宙・ネオン） ---
st.markdown("""
    <style>
    /* 全体の背景：宇宙の深い闇 */
    .stApp {
        background-color: #050a14;
        background-image: radial-gradient(circle at 50% 50%, #112244 0%, #050a14 100%);
    }
    
    /* サイバーなカードデザイン */
    .stMetric, .portfolio-card, .stExpander {
        background-color: rgba(16, 20, 35, 0.8) !important;
        border: 1px solid #00f2ff !important;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
    }

    /* ポートフォリオ合計：ネオン・マゼンタ */
    .portfolio-card {
        border: 2px solid #ff00ff !important;
        box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
        padding: 30px;
        margin-bottom: 30px;
    }

    /* メトリクスの光る文字 */
    [data-testid="stMetricValue"] {
        color: #00f2ff !important;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px #00f2ff;
        font-size: 2.5rem !important;
    }

    /* タイトル：サイバーフォント風 */
    h1 {
        color: #00f2ff;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 5px;
        text-shadow: 2px 2px 10px #00f2ff;
    }

    /* ボタンと入力欄のカスタマイズ */
    .stButton>button {
        background: linear-gradient(45deg, #ff00ff, #00f2ff);
        color: white;
        border: none;
        font-weight: bold;
    }
    
    .buy-zone { background-color: rgba(0, 255, 0, 0.1); border: 2px solid #00ff00; color: #00ff00; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; }
    .sell-zone { background-color: rgba(255, 0, 0, 0.1); border: 2px solid #ff4b4b; color: #ff4b4b; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ Dragon Cyber Terminal v3.0")

# --- サイドバー：ポートフォリオ入力（銘柄ごと） ---
st.sidebar.header("🛸 艦隊データ（ポートフォリオ）")

# 銘柄ごとの入力フォーム
if 'rows' not in st.session_state:
    st.session_state.rows = 3  # 初期入力枠の数

with st.sidebar:
    pf_data_list = []
    for i in range(st.session_state.rows):
        st.markdown(f"**Unit {i+1}**")
        col1, col2, col3 = st.columns([2, 2, 2])
        tick = col1.text_input("銘柄", value="XRP-USD" if i==0 else "", key=f"t_{i}")
        price = col2.number_input("単価", value=0.0, key=f"p_{i}")
        qty = col3.number_input("数量", value=0.0, key=f"q_{i}")
        if tick:
            pf_data_list.append({"銘柄": tick.upper(), "単価": price, "数量": qty})
    
    if st.button("🛰️ 入力枠を増やす"):
        st.session_state.rows += 1
        st.rerun()

st.sidebar.divider()
st.sidebar.header("🔍 スキャン対象")
ticker_input = st.sidebar.text_input("分析銘柄", value="XRP-USD, 7203.T, 3140.T, AAPL").upper()
tickers = [t.strip() for t in ticker_input.split(",")]

# アラート設定
alert_ticker = st.sidebar.selectbox("アラート対象", tickers)
target_price = st.sidebar.number_input("通知価格（以下）", value=0.0)

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

# --- メイン：サイバー・ダッシュボード ---
st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
st.markdown("<h3 style='color:#ff00ff; text-align:center;'>🌌 TOTAL ASSET VALUE</h3>", unsafe_allow_html=True)

pf_df, total_cost, total_value = get_live_pf(pf_data_list)

if not pf_df.empty:
    p_profit = total_value - total_cost
    p_ratio = (p_profit / total_cost * 100) if total_cost > 0 else 0
    
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    c1.metric("CURRENT TOTAL", f"¥{total_value:,.0f}" if "T" in ticker_input else f"${total_value:,.2f}")
    c2.metric("TOTAL P/L", f"{p_profit:,.2f}", delta=f"{p_ratio:.2f}%")
    
    fig_pie = px.pie(pf_df, values='評価額', names='銘柄', hole=.6)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          font_color="#fff", height=200, showlegend=False)
    fig_pie.update_traces(marker=dict(colors=['#ff00ff', '#00f2ff', '#7000ff', '#00ff88']))
    c3.plotly_chart(fig_pie, use_container_width=True)
else:
    st.write("左側のサイドバーでポートフォリオを入力してください。")
st.markdown('</div>', unsafe_allow_html=True)

# --- 個別分析 ---
for t_code in tickers:
    try:
        with st.expander(f"🛰️ SCANNING: {t_code}", expanded=True):
            df = yf.download(t_code, start="2025-08-01", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # RSI計算
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss)))
            last_p = float(df['Close'].iloc[-1])

            # アラート判定
            if alert_ticker == t_code and target_price > 0 and last_p <= target_price:
                st.balloons()
                st.warning(f"⚠️ TARGET REACHED: {t_code} @ {last_p:.2f}")

            # LPPLS (臨界点)
            df_c = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_c['Date']]
            price = np.log(df_c['Close'].values.flatten())
            model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = model.fit(max_searches=20)
            crit_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # 表示
            if rsi.iloc[-1] < 30: st.markdown('<div class="buy-zone">🚀 BUY SIGNAL: DRAGON AWAKENING</div>', unsafe_allow_html=True)
            elif rsi.iloc[-1] > 70: st.markdown('<div class="sell-zone">⚠️ SELL SIGNAL: OVERHEATED</div>', unsafe_allow_html=True)

            colA, colB = st.columns(2)
            colA.metric("PRICE", f"{last_p:,.2f}")
            colB.metric("X-DAY (LPPLS)", crit_date)

            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00f2ff', width=2))])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              height=200, margin=dict(l=0,r=0,t=0,b=0), font_color="#00f2ff",
                              xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#112244'))
            st.plotly_chart(fig, use_container_width=True)
    except: continue
