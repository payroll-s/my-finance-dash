import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Ultimate Dragon Portfolio", layout="wide")

# --- スタイル設定 ---
st.markdown("""
    <style>
    .stMetric { background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .portfolio-card { 
        background-color: #1a237e; 
        padding: 25px; 
        border-radius: 15px; 
        border: 2px solid #00d1ff; 
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 209, 255, 0.2);
    }
    [data-testid="stMetricValue"] { color: #00f2ff !important; font-size: 2.2rem !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; }
    .buy-zone { background-color: #008000; color: #ffffff; font-weight: bold; border: 2px solid #00ff00; padding: 20px; border-radius: 10px; }
    .sell-zone { background-color: #b30000; color: #ffffff; font-weight: bold; border: 2px solid #ff4b4b; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🐉 究極・ドラゴン資産司令塔")

# --- サイドバー設定 ---
st.sidebar.header("💰 ポートフォリオ設定")
portfolio_input = st.sidebar.text_area("保有データ (銘柄,単価,数)", value="XRP-USD,0.5,1000\n7203.T,2500,100", height=100)

st.sidebar.header("🔍 分析ターゲット")
ticker_input = st.sidebar.text_input("分析銘柄 (カンマ区切り)", value="XRP-USD, 7203.T, AAPL").upper()
tickers = [t.strip() for t in ticker_input.split(",")]

st.sidebar.divider()
st.sidebar.header("🔔 価格アラート")
alert_ticker = st.sidebar.selectbox("対象を選択", tickers)
target_price = st.sidebar.number_input("この価格以下で通知", value=0.0)

# --- 関数定義 ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_pf_data(raw_input):
    data = []
    t_cost, t_val = 0, 0
    for line in raw_input.strip().split('\n'):
        try:
            t, p, q = [x.strip() for x in line.split(',')]
            curr_df = yf.download(t, period="1d", progress=False)
            curr_p = float(curr_df['Close'].iloc[-1])
            val, cost = curr_p * float(q), float(p) * float(q)
            data.append({"銘柄": t, "評価額": val, "損益": val - cost})
            t_cost += cost
            t_val += val
        except: continue
    return pd.DataFrame(data), t_cost, t_val

# --- メイン表示：ポートフォリオ ---
st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
pf_df, t_cost, t_val = get_pf_data(portfolio_input)
if not pf_df.empty:
    c1, c2, c3 = st.columns([1,1,1.5])
    c1.metric("総資産額", f"¥{t_val:,.0f}" if "T" in ticker_input else f"${t_val:,.2f}")
    c2.metric("合計損益", f"{(t_val-t_cost):,.2f}", delta=f"{((t_val-t_cost)/t_cost*100):.2f}%")
    fig_pie = px.pie(pf_df, values='評価額', names='銘柄', hole=.4, template="plotly_dark")
    fig_pie.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=150, showlegend=False)
    c3.plotly_chart(fig_pie, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- メイン表示：個別銘柄分析 ---
for t_code in tickers:
    try:
        with st.expander(f"📉 {t_code} の詳細診断", expanded=True):
            df = yf.download(t_code, start="2025-08-01", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df['RSI'] = calculate_rsi(df['Close'])
            latest_p = float(df['Close'].iloc[-1])

            # ★アラート判定
            if alert_ticker == t_code and target_price > 0 and latest_p <= target_price:
                st.balloons()
                st.toast(f"🚨 到達！ {t_code}: {latest_p:.2f}", icon="🔥")
                st.warning(f"🔔 アラート：{t_code} が目標の {target_price} を下回りました！")

            # LPPLS
            df_c = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_c['Date']]
            price = np.log(df_c['Close'].values.flatten())
            model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = model.fit(max_searches=20)
            crit_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # 表示
            rsi_val = latest_p # ダミーではなく実際値を表示
            if df['RSI'].iloc[-1] < 30: st.markdown(f'<div class="buy-zone">🚀 絶好の買い場！ (RSI: {df["RSI"].iloc[-1]:.1f}%)</div>', unsafe_allow_html=True)
            elif df['RSI'].iloc[-1] > 70: st.markdown(f'<div class="sell-zone">⚠️ 警戒ゾーン！ (RSI: {df["RSI"].iloc[-1]:.1f}%)</div>', unsafe_allow_html=True)
            
            mc1, mc2 = st.columns(2)
            mc1.metric("現在値", f"{latest_p:.2f}")
            mc2.metric("臨界点 (X-Day)", crit_date)
            
            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00d1ff'))])
            fig.update_layout(height=250, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e: st.error(f"Error {t_code}: {e}")
