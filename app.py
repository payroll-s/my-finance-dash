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
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    .buy-zone { background-color: #008000; color: #ffffff; font-weight: bold; border: 2px solid #00ff00; padding: 20px; border-radius: 10px; }
    .sell-zone { background-color: #b30000; color: #ffffff; font-weight: bold; border: 2px solid #ff4b4b; padding: 20px; border-radius: 10px; }
    .portfolio-card { background-color: #11141c; padding: 20px; border-radius: 15px; border-left: 5px solid #00d1ff; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🐉 究極・ドラゴン資産司令塔")

# --- サイドバー：ポートフォリオ設定 ---
st.sidebar.header("💰 自分のポートフォリオ設定")
st.sidebar.info("例: 銘柄,平均取得単価,保有数")
# 初期のサンプルデータ
portfolio_input = st.sidebar.text_area("カンマ区切りで入力 (銘柄,単価,数)", 
                                    value="XRP-USD,0.5,1000\n7203.T,2500,100\nAAPL,180,10", height=150)

# 銘柄分析用の入力欄
st.sidebar.header("🔍 銘柄分析ターゲット")
ticker_input = st.sidebar.text_input("分析したい銘柄（カンマ区切り）", value="XRP-USD, 7203.T, AAPL").upper()
tickers = [t.strip() for t in ticker_input.split(",")]

# --- データ取得・ポートフォリオ計算 ---
def get_portfolio_data(raw_input):
    lines = raw_input.strip().split('\n')
    data = []
    total_cost = 0
    total_value = 0
    
    for line in lines:
        try:
            t, price, qty = line.split(',')
            t = t.strip().upper()
            price = float(price)
            qty = float(qty)
            
            # 現在価格を取得
            curr_df = yf.download(t, period="1d", progress=False)
            curr_price = curr_df['Close'].iloc[-1]
            
            value = curr_price * qty
            cost = price * qty
            profit = value - cost
            
            data.append({"銘柄": t, "保有数": qty, "取得単価": price, "現在値": curr_price, "評価額": value, "損益": profit})
            total_cost += cost
            total_value += value
        except:
            continue
    return pd.DataFrame(data), total_cost, total_value

# --- 1. ポートフォリオ・ダッシュボード ---
st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
st.subheader("🏦 マイ・ポートフォリオ合計")

pf_df, t_cost, t_value = get_portfolio_data(portfolio_input)

if not pf_df.empty:
    total_profit = t_value - t_cost
    profit_pct = (total_profit / t_cost) * 100 if t_cost > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("総資産（評価額）", f"${t_value:,.2f}" if "USD" in portfolio_input else f"¥{t_value:,.0f}")
    c2.metric("合計損益", f"{total_profit:,.2f}", delta=f"{profit_pct:.2f}%")
    c3.write("🍎 資産構成比")
    fig_pie = px.pie(pf_df, values='評価額', names='銘柄', hole=.4, template="plotly_dark")
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=150)
    c3.plotly_chart(fig_pie, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 銘柄分析セクション（これまでの機能） ---
st.divider()
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

for ticker in tickers:
    # (以前の分析ロジックとグラフ表示 - スペースの都合上同様のコードをここに維持)
    try:
        with st.expander(f"📉 {ticker} の詳細診断", expanded=True):
            df = yf.download(ticker, start="2025-08-01", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df['RSI'] = calculate_rsi(df['Close'])
            latest = df.iloc[-1]
            
            # LPPLS (簡易化して表示)
            df_clean = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_clean['Date']]
            price = np.log(df_clean['Close'].values.flatten())
            lppls_model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
            critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # 判定と表示
            if latest['RSI'] < 30: st.markdown(f'<div class="buy-zone">🚀 絶好の買い場！ (RSI: {latest["RSI"]:.1f}%)</div>', unsafe_allow_html=True)
            elif latest['RSI'] > 70: st.markdown(f'<div class="sell-zone">⚠️ 警戒ゾーン！ (RSI: {latest["RSI"]:.1f}%)</div>', unsafe_allow_html=True)
            else: st.info(f"📋 観察フェーズです。")
            
            st.metric("臨界点 (X-Day)", critical_date)
            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], name="Price")])
            fig.update_layout(height=300, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.error(f"{ticker} の分析に失敗しました。")
