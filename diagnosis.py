import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：サイドバーの文字と枠内リストの完全可視化 ---
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

    /* 3. サイドバーの通常テキスト（見出しなど） */
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stWrite {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000 !important;
    }

    /* 4. ★ 銘柄リスト（ラジオボタン）の文字を強制表示させる ★ */
    /* 枠の設定 */
    div[data-testid="stRadio"] > div {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 10px !important;
        margin-top: 10px !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* ラジオボタン内の全テキストレイヤーを白く固定 */
    div[data-testid="stRadio"] label {
        background-color: transparent !important;
        opacity: 1 !important;
    }
    
    /* 銘柄名そのものの文字設定 */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 1.2rem !important;
        text-shadow: none !important;
        margin: 0 !important;
        padding: 5px 0 !important;
        display: block !important;
        width: 100% !important;
    }

    /* 標準の丸ボタンを消去 */
    div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child { 
        display: none !important; 
    }

    /* 選択中の「▶」表示 */
    div[data-testid="stRadio"] label[aria-checked="true"] p::before {
        content: "▶" !important;
        margin-right: 8px;
    }
    div[data-testid="stRadio"] label[aria-checked="false"] p::before {
        content: "　" !important;
        margin-right: 8px;
    }

    /* 5. 入力欄 */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* 6. メイン画面 */
    [data-testid="stMetric"] { background-color: #000000 !important; border: 4px solid #ffffff !important; }
    [data-testid="stMetricValue"] { color: #ffff00 !important; }
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

# --- サイドバー ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    ticker_input_val = st.text_input("しらべる 銘柄コード:", value="XRP-USD", key="ticker_input_vFinal").upper()
    
    st.write("▼ おぼえている じゅもん")
    
    # 銘柄名リストを生成
    spell_names = [s["name"] for s in st.session_state.spells]
    
    # 枠（ラジオボタン）の表示
    selected_name = st.radio(
        "label_is_hidden",
        options=spell_names,
        label_visibility="collapsed",
        key="spell_selector"
    )

    # 選択連動ロジック
    for s in st.session_state.spells:
        if s["name"] == selected_name:
            if 'current_sel' not in st.session_state or st.session_state.current_sel != selected_name:
                ticker_input_val = s["ticker"]
                st.session_state.current_sel = selected_name

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.session_state.spells[i]["name"] = st.text_input(f"なまえ {i+1}", value=st.session_state.spells[i]["name"], key=f"n_ed_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input(f"コード {i+1}", value=st.session_state.spells[i]["ticker"], key=f"t_ed_{i}").upper()

    ticker = ticker_input_val.strip()

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
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        
        # RSI等計算(中略)
        st.markdown('<div style="border:4px solid white; padding:15px; background:black; color:white;">▼ 診断完了！</div>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ 銘柄が みつからない。")
