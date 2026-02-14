import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：ラベル文字の白色化とスタイル調整 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 1. 全体背景 */
    .stApp { background-color: #000000 !important; font-family: 'DotGothic16', sans-serif !important; }

    /* 2. サイドバー：レンガ背景 */
    [data-testid="stSidebar"] {
        background-color: #4a2c2a !important; 
        background-image: 
            linear-gradient(335deg, #2e1a18 23px, transparent 23px),
            linear-gradient(155deg, #2e1a18 23px, transparent 23px),
            linear-gradient(335deg, #2e1a18 23px, transparent 23px),
            linear-gradient(155deg, #2e1a18 23px, transparent 23px);
        background-size: 58px 58px;
        background-position: 0px 2px, 4px 35px, 29px 31px, 34px 6px;
        border-right: 5px solid #ffffff !important;
    }

    /* 3. サイドバーテキスト */
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000 !important;
    }

    /* 4. 銘柄名・属性ウィンドウ */
    .name-window {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 15px !important;
        margin-top: 15px !important;
        color: #ffffff !important;
        text-align: center !important;
    }
    .sector-tag {
        color: #ffff00 !important;
        font-size: 0.9rem !important;
        margin-top: 5px;
    }

    /* 5. HPバー（RSI視覚化） */
    .hp-label { color: #ffffff; font-size: 1.2rem; margin-bottom: 5px; }
    .hp-container {
        width: 100%;
        background-color: #333;
        border: 4px solid #fff;
        height: 30px;
        margin-bottom: 10px;
    }
    .hp-fill { height: 100%; transition: width 0.5s ease-in-out; }

    /* 6. ★ メトリクス（ステータス）のラベルを白く強制する ★ */
    [data-testid="stMetricLabel"] p {
        color: #ffffff !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
    }
    [data-testid="stMetricValue"] { 
        color: #ffff00 !important; 
        text-shadow: 2px 2px #ff0000; 
    }

    /* 7. レポート・入力欄 */
    div[data-baseweb="input"] { background-color: #000000 !important; border: 4px solid #ffffff !important; }
    input { color: #ffffff !important; background-color: #000000 !important; }
    .report-card { background-color: #000000 !important; border: 4px solid #ffffff !important; padding: 20px !important; color: #ffffff !important; }
    h1, h2, h3 { color: #ffffff !important; border-bottom: 2px solid #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1>▶ DRAGON KING\'S LAIR</h1>', unsafe_allow_html=True)

# --- サイドバー：入力と属性表示 ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD").upper()
    ticker = ticker_input.strip()

    @st.cache_data(ttl=3600)
    def get_stock_info(symbol):
        try:
            info = yf.Ticker(symbol).info
            name = info.get('longName') or info.get('shortName') or symbol
            sector = info.get('sector') or info.get('quoteType') or "不明な属性"
            return name, sector
        except:
            return "？？？？", "未知の属性"

    stock_name, stock_sector = get_stock_info(ticker) if ticker else ("なし", "無")

    st.write("▼ いまの あいて")
    st.markdown(f'''
        <div class="name-window">
            <div style="font-size: 1.3rem;">▶ {stock_name}</div>
            <div class="sector-tag">【 属性: {stock_sector} 】</div>
        </div>
    ''', unsafe_allow_html=True)

# --- 診断ロジック ---
@st.cache_data(ttl=3600)
def load_data(symbol):
    try:
        data = yf.download(symbol, start="2025-06-01", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data[['Close']].dropna()
    except:
        return pd.DataFrame()

if ticker:
    df = load_data(ticker)
    if not df.empty and len(df) > 30:
        # 指標計算
        window = 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rsi_val = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        # HPバーの色決定
        hp_color = "#00ff00"
        if rsi_val > 70: hp_color = "#ff0000"
        elif rsi_val < 30: hp_color = "#ffff00"

        # --- メイン画面：ステータス ---
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        col2.metric("きりょく (RSI)", f"{rsi_val:.1f}")
        col3.metric("かいり (DIV)", f"{((df['Close'].iloc[-1] - df['Close'].rolling(25).mean().iloc[-1]) / df['Close'].rolling(25).mean().iloc[-1] * 100):.1f}")

        # --- レポート ---
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {stock_name} を しらべた！")
        if rsi_val > 70: st.write("・てきは こうふんしている！")
        elif rsi_val < 30: st.write("・てきは つかれている！")
        else: st.write("・てきは おちついている。")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- チャート ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)

        # --- HPバー（グラフ下） ---
        st.markdown(f'''
            <div class="hp-label">▶ てきの きりょく (HP)</div>
            <div class="hp-container">
                <div class="hp-fill" style="width: {rsi_val}%; background-color: {hp_color};"></div>
            </div>
            <div style="text-align:right; font-size: 1.2rem; color: #ffffff;">{rsi_val:.1f} / 100</div>
        ''', unsafe_allow_html=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
