import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：反転エフェクトの追加 ---
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
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] .stMarkdown p {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000 !important;
    }

    /* 4. コマンドウィンドウ（白枠・黒背景） */
    .command-window {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 10px !important;
        margin: 10px 0px !important;
    }

    /* ボタン（通常時）：黒背景・白文字 */
    .command-window .stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 0px !important;
        text-align: left !important;
        width: 100% !important;
        font-family: 'DotGothic16', sans-serif !important;
        font-size: 1.2rem !important;
        padding: 8px 10px !important;
        display: block !important;
        transition: none !important; /* RPG風にパッと切り替える */
    }

    /* ★ ホバー時（反転）：白背景・黒文字 ★ */
    .command-window .stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
    }
    
    /* Streamlit特有のホバー時の枠線を消す */
    .command-window .stButton > button:focus {
        background-color: #ffffff !important;
        color: #000000 !important;
        box-shadow: none !important;
    }

    /* 5. 入力欄・メトリクス・レポート（前回同様） */
    div[data-baseweb="input"] { background-color: #000000 !important; border: 4px solid #ffffff !important; }
    input { color: #ffffff !important; background-color: #000000 !important; }
    [data-testid="stMetric"] { background-color: #000000 !important; border: 4px solid #ffffff !important; }
    [data-testid="stMetricValue"] { color: #ffff00 !important; text-shadow: 2px 2px #ff0000; }
    .report-card { background-color: #000000 !important; border: 4px solid #ffffff !important; padding: 20px !important; color: #ffffff !important; }
    h1, h2, h3 { color: #ffffff !important; border-bottom: 2px solid #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1>▶ DRAGON KING\'S LAIR</h1>', unsafe_allow_html=True)

# --- データ管理 ---
if 'spells' not in st.session_state:
    st.session_state.spells = [
        {"name": "りゅうお", "ticker": "XRP-USD"},
        {"name": "おうごん", "ticker": "GC=F"},
        {"name": "くるま", "ticker": "7203.T"},
        {"name": "ぶつりゅう", "ticker": "3140.T"}
    ]
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "XRP-USD"

# --- サイドバー：コマンド ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    ticker_input = st.text_input("しらべる 銘柄コード:", value=st.session_state.current_ticker, key="ticker_input_field").upper()
    
    st.write("▼ おぼえている じゅもん")
    
    # 漆黒のコマンドウィンドウ
    st.markdown('<div class="command-window">', unsafe_allow_html=True)
    for i, spell in enumerate(st.session_state.spells):
        cursor = "▶ " if st.session_state.current_ticker == spell["ticker"] else "　 "
        # ボタン自体に反転CSSが効くようになっています
        if st.button(f"{cursor}{spell['name']}", key=f"spell_cmd_{i}"):
            st.session_state.current_ticker = spell["ticker"]
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.session_state.spells[i]["name"] = st.text_input(f"なまえ {i+1}", value=st.session_state.spells[i]["name"], key=f"edit_name_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input(f"コード {i+1}", value=st.session_state.spells[i]["ticker"], key=f"edit_ticker_{i}").upper()

    ticker = st.session_state.current_ticker.strip()

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

        # メイン表示
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        col2.metric("きりょく (RSI)", f"{df['RSI'].iloc[-1]:.1f}")
        col3.metric("かいり (DIV)", f"{df['Divergence'].iloc[-1]:.1f}")

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {ticker} を しらべた！")
        st.write("てきの ようすを うかがっている…")
        st.markdown('</div>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
