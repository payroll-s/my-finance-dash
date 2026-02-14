import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- 全体スタイル定義（物理的強制上書き） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 1. メイン画面の背景 */
    .stApp {
        background-color: #000000 !important;
        font-family: 'DotGothic16', sans-serif !important;
    }

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

    /* 3. 入力欄：白枠・黒背景 */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* 4. ★ 最強のボタン修正：内側のすべての要素を漆黒にする ★ */
    .spell-master-window {
        border: 4px solid #ffffff !important;
        background-color: #000000 !important;
        padding: 8px !important;
        margin: 10px 0px !important;
    }

    /* ボタン本体・ホバー・フォーカスのすべてを強制固定 */
    .spell-master-window button, 
    .spell-master-window button p, 
    .spell-master-window button div,
    .spell-master-window .stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 0px !important;
        opacity: 1 !important;
    }

    /* ホバー時のみ反転 */
    .spell-master-window button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .spell-master-window button:hover * {
        color: #000000 !important;
    }

    /* 5. ポップアップ（前回成功した設定を維持） */
    div[data-baseweb="tooltip"], div[data-baseweb="tooltip"] * {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
    }

    /* 6. メイン画面の装飾 */
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
        {"name": "りゅうお", "ticker": "XRP-USD", "desc": "リップル(XRP)"},
        {"name": "おうごん", "ticker": "GC=F", "desc": "金(GOLD)先物"},
        {"name": "くるま", "ticker": "7203.T", "desc": "トヨタ自動車"},
        {"name": "ぶつりゅう", "ticker": "3140.T", "desc": "エーアイティー"}
    ]

# --- サイドバー ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    # 銘柄入力
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD", key="final_ticker_v3").upper()
    
    st.write("▼ おぼえている じゅもん")
    
    # 呪文ウィンドウ
    st.markdown('<div class="spell-master-window">', unsafe_allow_html=True)
    for i, spell in enumerate(st.session_state.spells):
        # ボタンの中に span や p が生成されても、すべて強制的に白文字・黒背景にします
        if st.button(f" ・{spell['name']}", key=f"fixed_v3_btn_{i}", help=f"{spell['desc']} ({spell['ticker']})"):
            ticker_input = spell["ticker"]
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.session_state.spells[i]["name"] = st.text_input("なまえ", value=st.session_state.spells[i]["name"], key=f"edit_n3_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input("コード", value=st.session_state.spells[i]["ticker"], key=f"edit_t3_{i}").upper()
            st.session_state.spells[i]["desc"] = st.text_input("かいせつ", value=st.session_state.spells[i]["desc"], key=f"edit_d3_{i}")

    ticker = ticker_input.strip()

# --- 診断ロジック（以下、前回と同じ） ---
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
        window, delta = 14, df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        df['MA25'] = df['Close'].rolling(window=25).mean()
        df['Divergence'] = ((df['Close'] - df['MA25']) / df['MA25']) * 100

        df_recent = df.reset_index()
        time = [pd.Timestamp.toordinal(d) for d in df_recent['Date']]
        price = np.log(df_recent['Close'].values.flatten())
        lppls_model = lppls.LPPLS(observations=np.array([time, price]))
        tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
        critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        c2.metric("きりょく (RSI)", f"{df['RSI'].iloc[-1]:.1f}")
        c3.metric("かいり (DIV)", f"{df['Divergence'].iloc[-1]:.1f}")

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {ticker} を しらべた！")
        st.markdown(f'- <span style="color:#ff0000">運命の日：{critical_date}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="かかく", line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
