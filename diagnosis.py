import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- ドラクエ風：ダンジョン・スタイル（ボタン背景問題を根絶） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 1. 全体背景 */
    .stApp, [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #000000 !important;
        font-family: 'DotGothic16', sans-serif !important;
    }

    /* 2. 基本テキスト */
    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #ffffff !important;
        font-family: 'DotGothic16', sans-serif !important;
    }

    /* 3. サイドバー境界線 */
    [data-testid="stSidebar"] {
        border-right: 4px solid #ffffff !important;
    }

    /* 4. 入力欄（白枠） */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input {
        color: #ffffff !important;
        background-color: #000000 !important;
    }

    /* 5. ★ 呪文ボタン：Streamlitのデフォルトスタイルを完全に破壊する ★ */
    div.stButton > button {
        background-color: #000000 !important; /* 初期背景：黒 */
        color: #ffffff !important;           /* 初期文字：白 */
        border: 2px solid #ffffff !important; /* 白枠 */
        border-radius: 0px !important;
        width: 100%;
        text-align: left;
        font-family: 'DotGothic16', sans-serif !important;
        opacity: 1 !important;
    }

    /* ホバー時（カーソルを合わせた時） */
    div.stButton > button:hover {
        background-color: #ffffff !important; /* 背景：白 */
        color: #000000 !important;           /* 文字：黒 */
        border: 2px solid #ffffff !important;
    }

    /* クリック後やフォーカス時も黒背景を維持 */
    div.stButton > button:focus, div.stButton > button:active {
        background-color: #000000 !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }

    /* 6. ツールチップ（ポップアップ）の視認性固定 */
    div[data-baseweb="tooltip"] {
        background-color: #000000 !important;
        border: 2px solid #ffffff !important;
    }
    div[data-baseweb="tooltip"] * {
        color: #ffffff !important;
        background-color: #000000 !important;
    }

    /* 7. メトリクス */
    .stMetric {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffff00 !important;
        text-shadow: 2px 2px #ff0000;
    }

    /* 8. レポートウィンドウ */
    .report-card {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 20px;
    }

    h1, h2, h3 {
        color: #ffffff !important;
        border-bottom: 2px solid #ffffff;
    }
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
    
    # 銘柄入力（白枠）
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD").upper()
    
    st.write("▼ おぼえている じゅもん")
    for i, spell in enumerate(st.session_state.spells):
        # 呪文ボタン
        if st.button(spell["name"], key=f"btn_{i}", help=f"{spell['desc']} ({spell['ticker']})"):
            ticker_input = spell["ticker"]

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.write(f"--- じゅもん {i+1} ---")
            st.session_state.spells[i]["name"] = st.text_input("なまえ", value=st.session_state.spells[i]["name"], key=f"name_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input("コード", value=st.session_state.spells[i]["ticker"], key=f"tick_{i}").upper()
            st.session_state.spells[i]["desc"] = st.text_input("かいせつ", value=st.session_state.spells[i]["desc"], key=f"desc_{i}")

    ticker = ticker_input.strip()

# --- 診断ロジックは変更なし ---
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

        # LPPLS
        df_recent = df.reset_index()
        time = [pd.Timestamp.toordinal(d) for d in df_recent['Date']]
        price = np.log(df_recent['Close'].values.flatten())
        lppls_model = lppls.LPPLS(observations=np.array([time, price]))
        tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
        critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

        # 表示
        curr_p = df['Close'].iloc[-1]
        curr_rsi = df['RSI'].iloc[-1]
        curr_div = df['Divergence'].iloc[-1]

        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("かかく (G)", f"{curr_p:,.2f}")
        c2.metric("きりょく (RSI)", f"{curr_rsi:.1f}")
        c3.metric("かいり (DIV)", f"{curr_div:.1f}")

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {ticker} を しらべた！")
        today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
        if curr_rsi > 70: st.markdown('- <span style="color:#ff0000">てきは こうふんしている！</span>', unsafe_allow_html=True)
        elif curr_rsi < 30: st.markdown('- <span style="color:#00ff00">てきは つかれている！ チャンスだ！</span>', unsafe_allow_html=True)
        if abs(curr_div) > 15: st.markdown('- <span style="color:#ff0000">じゅもんが ぼうそうしている！</span>', unsafe_allow_html=True)
        if critical_date > today_str:
            st.markdown(f'- <span style="color:#ff0000">おそろしい よかんがする… くるべきときは {critical_date}！</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'- <span style="color:#00ff00">あらしは すぎさった。 いまは しずかだ。</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="かかく", line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
