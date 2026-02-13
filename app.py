import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Ultimate Dragon Portfolio", layout="wide")

# --- スタイル設定（デザイン強化版） ---
st.markdown("""
    <style>
    /* 全体の背景となじむメトリクス設定 */
    .stMetric { 
        background-color: #0e1117; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #30363d; 
    }
    
    /* 1. ポートフォリオ合計枠の特別な塗りつぶし */
    .portfolio-card { 
        background-color: #1a237e; /* 濃いロイヤルブルーで塗りつぶし */
        padding: 25px; 
        border-radius: 15px; 
        border: 2px solid #00d1ff; /* 水色の光る枠線 */
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 209, 255, 0.2); /* ほのかな光彩 */
    }

    /* 2. 総資産の数字を「白」に近い水色で光らせる */
    [data-testid="stMetricValue"] {
        color: #00f2ff !important; 
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);
    }
    
    /* 3. ラベル（文字）も白くして読みやすく */
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 1.1rem !important;
    }

    /* 買い場・売り場シグナルのスタイル（維持） */
    .buy-zone { background-color: #008000; color: #ffffff; font-weight: bold; border: 2px solid #00ff00; padding: 20px; border-radius: 10px; }
    .sell-zone { background-color: #b30000; color: #ffffff; font-weight: bold; border: 2px solid #ff4b4b; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
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
# --- サイドバーに通知設定を追加 ---
st.sidebar.divider()
st.sidebar.header("🔔 価格アラート設定")
alert_ticker = st.sidebar.selectbox("アラート対象", tickers)
target_price = st.sidebar.number_input("ターゲット価格（以下になったら通知）", value=0.0)

# --- 通知のメインロジック（分析ループの中などに追加） ---
if alert_ticker == ticker and target_price > 0:
    if latest['Close'] <= target_price:
        st.balloons() # 画面に風船を飛ばす演出
        st.toast(f"🔔 アラート：{ticker} が目標価格 {target_price} を下回りました！", icon="🔥")
        st.warning(f"🚨 【発動】{ticker} 現在値 {latest['Close']:.2f} が目標価格に到達！")
# --- データ取得・ポートフォリオ計算（修正版） ---
def get_portfolio_data(raw_input):
    lines = raw_input.strip().split('\n')
    data = []
    total_cost = 0
    total_value = 0
    
    for line in lines:
        try:
            parts = line.split(',')
            if len(parts) < 3: continue
            
            t = parts[0].strip().upper()
            price = float(parts[1])
            qty = float(parts[2])
            
            # 現在価格を取得
            curr_df = yf.download(t, period="1d", progress=False)
            if curr_df.empty: continue
            
            # 【修正ポイント】数字だけを確実に取得
            curr_price = float(curr_df['Close'].iloc[-1])
            
            value = curr_price * qty
            cost = price * qty
            profit = value - cost
            
            data.append({"銘柄": t, "保有数": qty, "取得単価": price, "現在値": curr_price, "評価額": value, "損益": profit})
            total_cost += cost
            total_value += value
        except Exception as e:
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

# --- 2. 銘柄分析セクション ---
st.divider()

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

for t_code in tickers: # 変数名を明確に t_code とします
    try:
        with st.expander(f"📉 {t_code} の詳細診断", expanded=True):
            df = yf.download(t_code, start="2025-08-01", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df['RSI'] = calculate_rsi(df['Close'])
            latest = df.iloc[-1]
            curr_val = float(latest['Close']) # 現在の価格
            
            # --- LPPLS計算 ---
            df_clean = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_clean['Date']]
            price = np.log(df_clean['Close'].values.flatten())
            lppls_model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
            critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # --- ★アラート判定ロジック★ ---
            if alert_ticker == t_code and target_price > 0:
                if curr_val <= target_price:
                    st.balloons() # 風船を飛ばす
                    st.toast(f"🚨 ターゲット到達！ {t_code}: {curr_val:.2f}", icon="🔥")
                    st.warning(f"🔔 アラート発動：{t_code} が目標の {target_price} 以下になりました！")

            # 判定と表示 (RSI)
            if latest['RSI'] < 30: st.markdown(f'<div class="buy-zone">🚀 絶好の買い場！ (RSI: {latest["RSI"]:.1f}%)</div>', unsafe_allow_html=True)
            elif latest['RSI'] > 70: st.markdown(f'<div class="sell-zone">⚠️ 警戒ゾーン！ (RSI: {latest["RSI"]:.1f}%)</div>', unsafe_allow_html=True)
            else: st.info(f"📋 観察フェーズです。")
            
            st.metric("現在値", f"{curr_val:.2f}")
            st.metric("臨界点 (X-Day)", critical_date)
            
            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], name="Price")])
            fig.update_layout(height=300, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"{t_code} の分析中にエラーが発生しました: {e}")
