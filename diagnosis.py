import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：レンガの壁に漆黒のボタンを配置 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 1. メイン画面の背景（漆黒） */
    .stApp {
        background-color: #000000 !important;
        font-family: 'DotGothic16', sans-serif !important;
    }

    /* 2. サイドバーを「RPG風レンガ」に変更 */
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

    /* サイドバー内のテキスト（影付き） */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000;
    }

    /* 3. 【統一】入力欄：白枠・黒背景 */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* 4. 【統一】呪文ボタン：入力欄と同じ「黒背景・白文字・白枠」に強制固定 */
    /* サイドバー内のボタンをピンポイントで指定 */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #000000 !important; /* 背景：漆黒 */
        color: #ffffff !important;           /* 文字：白 */
        border: 4px solid #ffffff !important; /* 枠：太い白 */
        border-radius: 0px !important;       /* 角：四角 */
        width: 100% !important;
        text-align: left !important;
        font-family: 'DotGothic16', sans-serif !important;
        padding: 10px !important;
        box-shadow: 4px 4px 0px #000000 !important; /* 黒い影 */
        opacity: 1 !important;
    }

    /* ホバー時：反転（白背景・黒文字） */
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 4px solid #ffffff !important;
    }

    /* クリック後やフォーカス時も黒背景を維持 */
    section[data-testid="stSidebar"] .stButton > button:focus, 
    section[data-testid="stSidebar"] .stButton > button:active {
        background-color: #000000 !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }

    /* 5. ツールチップ（ポップアップ）も黒白で統一 */
    div[data-baseweb="tooltip"] {
        background-color: #000000 !important;
        border: 2px solid #ffffff !important;
    }
    div[data-baseweb="tooltip"] * {
        color: #ffffff !important;
        background-color: #000000 !important;
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

# --- サイドバー：ダンジョン壁面 ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    # 銘柄入力
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD").upper()
    
    st.write("▼ おぼえている じゅもん")
    # ここに表示されるボタンを「漆黒の石板」にしました
    for i, spell in enumerate(st.session_state.spells):
        if st.button(spell["name"], key=f"btn_{i}", help=f"{spell['desc']} ({spell['ticker']})"):
            ticker_input = spell["ticker"]

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.session_state.spells[i]["name"] = st.text_input(f"なまえ {i+1}", value=st.session_state.spells[i]["name"], key=f"name_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input(f"コード {i+1}", value=st.session_state.spells[i]["ticker"], key=f"tick_{i}").upper()
            st.session_state.spells[i]["desc"] = st.text_input(f"かいせつ {i+1}", value=st.session_state.spells[i]["desc"], key=f"desc_{i}")

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

        # チャート
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="かかく", line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
