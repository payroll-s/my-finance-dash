import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：サイドバーの視認性と新コマンド枠の装飾 ---
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

    /* 3. サイドバー内のテキスト（白・影付き） */
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000 !important;
    }

    /* 4. ★ 新・銘柄名表示コマンド枠 ★ */
    .name-window {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 20px !important;
        margin-top: 15px !important;
        color: #ffffff !important;
        font-size: 1.5rem !important;
        text-align: center !important;
        min-height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* 5. 入力欄：白枠・黒背景 */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* 6. メイン画面：ステータス（メトリクス） */
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 15px !important;
    }
    [data-testid="stMetricLabel"] { color: #ffffff !important; }
    [data-testid="stMetricValue"] { color: #ffff00 !important; text-shadow: 2px 2px #ff0000; font-size: 2.2rem !important; }

    /* 7. レポートカード */
    .report-card {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 20px !important;
        margin: 20px 0 !important;
        color: #ffffff !important;
    }
    h1, h2, h3 { color: #ffffff !important; border-bottom: 2px solid #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1>▶ DRAGON KING\'S LAIR</h1>', unsafe_allow_html=True)

# --- サイドバー：入力と銘柄名表示 ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    # 銘柄手入力欄
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD").upper()
    ticker = ticker_input.strip()

    # 銘柄情報の取得
    @st.cache_data(ttl=3600)
    def get_stock_name(symbol):
        try:
            info = yf.Ticker(symbol).info
            return info.get('longName') or info.get('shortName') or symbol
        except:
            return "？？？？"

    stock_name = get_stock_name(ticker) if ticker else "なし"

    st.write("▼ いまの あいて")
    # ★ 銘柄名を表示する新コマンド枠 ★
    st.markdown(f'<div class="name-window">▶ {stock_name}</div>', unsafe_allow_html=True)

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
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        df['MA25'] = df['Close'].rolling(window=25).mean()
        df['Divergence'] = ((df['Close'] - df['MA25']) / df['MA25']) * 100

        # メイン画面：ステータス表示
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        col2.metric("きりょく (RSI)", f"{df['RSI'].iloc[-1]:.1f}")
        col3.metric("かいり (DIV)", f"{df['Divergence'].iloc[-1]:.1f}")

        # レポート表示
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {stock_name} を しらべた！")
        rsi_val = df['RSI'].iloc[-1]
        if rsi_val > 70: st.write("・てきは こうふんしている！")
        elif rsi_val < 30: st.write("・てきは つかれている！")
        st.write("・てきの ようすを うかがっている…")
        st.markdown('</div>', unsafe_allow_html=True)

        # チャート表示
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
