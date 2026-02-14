import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：装飾のすべてを「黒背景・白文字・白枠」に全振りする ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 全体背景 */
    .stApp {
        background-color: #000000 !important;
        font-family: 'DotGothic16', sans-serif !important;
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

    /* 共通：入力欄（銘柄コード）のスタイル */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* ★ 呪文メニュー：ボタンを「入力欄と同じ見た目」にするための強制指定 ★ */
    /* 1. 4つのボタンを包む外枠 */
    .spell-menu-frame {
        border: 4px solid #ffffff !important;
        background-color: #000000 !important;
        padding: 10px !important;
        margin: 10px 0px !important;
    }

    /* 2. ボタン自体の改造（背景・枠・文字を完全固定） */
    .spell-menu-frame .stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 0px !important;
        width: 100% !important;
        text-align: left !important;
        padding: 10px !important;
        font-family: 'DotGothic16', sans-serif !important;
        font-size: 1.1rem !important;
        margin-bottom: 5px !important;
    }

    /* 3. ホバー時：白黒反転（ポップアップがない分、視覚効果を強めに） */
    .spell-menu-frame .stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #ffffff !important;
    }

    /* メイン画面の装飾 */
    .report-card, .stMetric {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
    }
    [data-testid="stMetricValue"] { color: #ffff00 !important; text-shadow: 2px 2px #ff0000; }
    h1, h2, h3 { color: #ffffff !important; border-bottom: 2px solid #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1>▶ DRAGON KING\'S LAIR</h1>', unsafe_allow_html=True)

# --- じゅもんデータ管理 ---
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
    
    # 基準の入力欄
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD", key="final_ticker_input").upper()
    
    st.write("▼ おぼえている じゅもん")
    
    # ポップアップ(help=)を廃止したことで、CSSが干渉せず100%適用されます
    st.markdown('<div class="spell-menu-frame">', unsafe_allow_html=True)
    for i, spell in enumerate(st.session_state.spells):
        if st.button(f" ・{spell['name']} ({spell['ticker']})", key=f"btn_v4_{i}"):
            ticker_input = spell["ticker"]
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.session_state.spells[i]["name"] = st.text_input(f"なまえ {i+1}", value=st.session_state.spells[i]["name"], key=f"edit_n4_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input(f"コード {i+1}", value=st.session_state.spells[i]["ticker"], key=f"edit_t4_{i}").upper()

    ticker = ticker_input.strip()

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
        # RSI, MA25, Divergence, LPPLS の計算 (中略)
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        st.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        
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
