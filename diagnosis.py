import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- ドラクエ風：ダンジョン・スタイル ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    .stApp {
        background-color: #000000;
        background-image: radial-gradient(circle at 2px 2px, #1a1a1a 1px, transparent 0);
        background-size: 40px 40px;
        font-family: 'DotGothic16', sans-serif !important;
    }

    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #ffffff !important;
        font-family: 'DotGothic16', sans-serif !important;
    }

    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 4px solid #ffffff !important;
    }

    .report-card, .stMetric, .stExpander {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
        padding: 20px;
    }

    [data-testid="stMetricValue"] {
        color: #ffff00 !important;
        font-size: 2.5rem !important;
        text-shadow: 2px 2px #ff0000;
    }

    /* じゅもんボタンの装飾 */
    .stButton>button {
        width: 100%;
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 0px !important;
        text-align: left;
        font-family: 'DotGothic16', sans-serif !important;
    }
    .stButton>button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    .status-ok { color: #00ff00 !important; }
    .status-warn { color: #ff0000 !important; }

    /* ツールチップ（紺色） */
    div[data-baseweb="tooltip"] {
        background-color: #050a14 !important;
        border: 1px solid #00f2ff !important;
    }
    div[data-baseweb="tooltip"] * {
        color: #00f2ff !important;
    }

    h1, h2, h3 {
        color: #ffffff !important;
        text-align: center;
        border-bottom: 2px solid #ffffff;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1>▶ DRAGON KING\'S LAIR</h1>', unsafe_allow_html=True)

# --- じゅもんデータの管理 (Session State) ---
if 'spells' not in st.session_state:
    st.session_state.spells = [
        {"name": "りゅうお", "ticker": "XRP-USD", "desc": "リップル(XRP)"},
        {"name": "おうごん", "ticker": "GC=F", "desc": "金(GOLD)先物"},
        {"name": "くるま", "ticker": "7203.T", "desc": "トヨタ自動車"},
        {"name": "ぶつりゅう", "ticker": "3140.T", "desc": "エーアイティー"}
    ]

# --- サイドバー：コマンドウィンドウ ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    # メイン入力
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD").upper()
    
    st.divider()
    st.write("▼ おぼえている じゅもん")
    
    # じゅもんボタンの生成
    for i, spell in enumerate(st.session_state.spells):
        if st.button(spell["name"], key=f"btn_{i}", help=f"銘柄: {spell['desc']} ({spell['ticker']})"):
            ticker_input = spell["ticker"]

    st.divider()
    
    # じゅもん編集エクスパンダー
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.write(f"--- じゅもん {i+1} ---")
            st.session_state.spells[i]["name"] = st.text_input("なまえ", value=st.session_state.spells[i]["name"], key=f"name_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input("コード", value=st.session_state.spells[i]["ticker"], key=f"tick_{i}").upper()
            st.session_state.spells[i]["desc"] = st.text_input("かいせつ", value=st.session_state.spells[i]["desc"], key=f"desc_{i}")

    ticker = ticker_input.strip()

# --- データ取得 & 診断 (ロジック部分は継承) ---
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

        # LPPLS計算
        df_recent = df.reset_index()
        time = [pd.Timestamp.toordinal(d) for d in df_recent['Date']]
        price = np.log(df_recent['Close'].values.flatten())
        lppls_model = lppls.LPPLS(observations=np.array([time, price]))
        tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
        critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

        # ステータス表示
        curr_p = df['Close'].iloc[-1]
        curr_rsi = df['RSI'].iloc[-1]
        curr_div = df['Divergence'].iloc[-1]

        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("かかく (G)", f"{curr_p:,.2f}")
        c2.metric("きりょく (RSI)", f"{curr_rsi:.1f}")
        c3.metric("かいり (DIV)", f"{curr_div:.1f}")

        # メッセージウィンドウ
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {ticker} を しらべた！")
        
        today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
        if curr_rsi > 70: st.markdown('- <span class="status-warn">てきは こうふんしている！</span>', unsafe_allow_html=True)
        elif curr_rsi < 30: st.markdown('- <span class="status-ok">てきは つかれている！ チャンスだ！</span>', unsafe_allow_html=True)
        if abs(curr_div) > 15: st.markdown('- <span class="status-warn">じゅもんが ぼうそうしている！</span>', unsafe_allow_html=True)
        if critical_date > today_str:
            st.markdown(f'- <span class="status-warn">おそろしい よかんがする… くるべきときは {critical_date}！</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'- <span class="status-ok">あらしは すぎさった。 いまは しずかだ。</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # チャート
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="かかく", line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
