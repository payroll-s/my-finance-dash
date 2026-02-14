import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：古のコマンドウィンドウとドラクエ風ロゴ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 全体背景 */
    .stApp { background-color: #000000 !important; font-family: 'DotGothic16', sans-serif !important; }

    /* ★ ドラクエ風コマンドロゴ ★ */
    .dq-logo {
        background: linear-gradient(180deg, #0000bb 0%, #000055 100%);
        border: 4px solid #ffffff;
        border-radius: 10px;
        padding: 10px 20px;
        display: inline-block;
        margin-bottom: 20px;
        box-shadow: 0 0 0 2px #000000, 0 0 0 4px #ffffff;
    }
    .dq-logo-text {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: bold;
        text-shadow: 2px 2px #000000;
        letter-spacing: 2px;
    }

    /* サイドバー：レンガ背景 */
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

    /* サイドバーテキスト */
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000 !important;
    }

    /* 銘柄名ウィンドウ（コマンド風） */
    .name-window {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 15px !important;
        margin-top: 15px !important;
        color: #ffffff !important;
    }

    /* HPバー（RSI視覚化） */
    .hp-label { color: #ffffff; font-size: 1.2rem; margin-top: 15px; }
    .hp-container {
        width: 100%;
        background-color: #333;
        border: 3px solid #fff;
        height: 25px;
    }
    .hp-fill { height: 100%; transition: width 0.5s ease-in-out; }

    /* メトリクス（ステータス） */
    [data-testid="stMetricLabel"] p { color: #ffffff !important; }
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
    }
    [data-testid="stMetricValue"] { color: #ffff00 !important; text-shadow: 2px 2px #ff0000; }

    /* レポートカード */
    .report-card { background-color: #000000 !important; border: 4px solid #ffffff !important; padding: 20px !important; color: #ffffff !important; }
    h1, h2, h3 { color: #ffffff !important; border-bottom: 2px solid #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- ロゴ表示 ---
st.markdown('''
    <div class="dq-logo">
        <span class="dq-logo-text">▶ DRAGON KING'S LAIR</span>
    </div>
''', unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD").upper()
    ticker = ticker_input.strip()

    @st.cache_data(ttl=3600)
    def get_stock_info(symbol):
        try:
            info = yf.Ticker(symbol).info
            name = info.get('longName') or info.get('shortName') or symbol
            sector = info.get('sector') or info.get('quoteType') or "不明"
            return name, sector
        except:
            return "？？？？", "未知"

    stock_name, stock_sector = get_stock_info(ticker) if ticker else ("なし", "無")

    st.write("▼ いまの あいて")
    st.markdown(f'''
        <div class="name-window">
            <div style="font-size: 1.2rem;">▶ {stock_name}</div>
            <div style="color: #ffff00; font-size: 0.9rem; margin-top: 5px;">【 属性: {stock_sector} 】</div>
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
        window = 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rsi_val = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        hp_color = "#00ff00"
        if rsi_val > 70: hp_color = "#ff0000"
        elif rsi_val < 30: hp_color = "#ffff00"

        # ステータス
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        col2.metric("きりょく (RSI)", f"{rsi_val:.1f}")
        col3.metric("かいり (DIV)", f"{((df['Close'].iloc[-1] - df['Close'].rolling(25).mean().iloc[-1]) / df['Close'].rolling(25).mean().iloc[-1] * 100):.1f}")

        # レポート
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {stock_name} を しらべた！")
        if rsi_val > 70: st.write("・てきは こうふんしている！")
        elif rsi_val < 30: st.write("・てきは つかれている！")
        else: st.write("・てきは おちついている。")
        st.markdown('</div>', unsafe_allow_html=True)

        # チャート
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)

        # HPバー
        st.markdown(f'''
            <div class="hp-label">▶ てきの きりょく (HP)</div>
            <div class="hp-container">
                <div class="hp-fill" style="width: {rsi_val}%; background-color: {hp_color};"></div>
            </div>
            <div style="text-align:right; font-size: 1.1rem; color: #ffffff;">{rsi_val:.1f} / 100</div>
        ''', unsafe_allow_html=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
