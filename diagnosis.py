import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：RPGスタイルとステータス表示の共存 ---
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

    /* 3. 入力欄：白枠・黒背景 */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* 4. ラジオボタン：箇条書きコマンド */
    div[data-testid="stRadio"] > div {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 15px !important;
        border-radius: 0px !important;
    }
    div[data-testid="stRadio"] label {
        color: #ffffff !important;
        font-size: 1.2rem !important;
    }
    /* 標準の丸を消して「▶」を出す */
    div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child { display: none !important; }
    div[data-testid="stRadio"] label[aria-checked="true"] p::before {
        content: "▶" !important;
        color: #ffffff !important;
        margin-right: 10px;
    }
    div[data-testid="stRadio"] label[aria-checked="false"] p::before {
        content: "　" !important;
        margin-right: 10px;
    }

    /* 5. ステータス・メトリクス装飾 */
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 10px !important;
        border-radius: 0px !important;
    }
    [data-testid="stMetricLabel"] { color: #ffffff !important; font-size: 1rem !important; }
    [data-testid="stMetricValue"] { 
        color: #ffff00 !important; 
        text-shadow: 2px 2px #ff0000;
        font-size: 2rem !important;
    }

    /* レポートカード */
    .report-card {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        padding: 20px !important;
        margin-top: 20px !important;
        color: #ffffff !important;
    }

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
    
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD", key="sidebar_ticker").upper()
    
    st.write("▼ おぼえている じゅもん")
    spell_names = [s["name"] for s in st.session_state.spells]
    selected_spell = st.radio("choice", options=spell_names, label_visibility="collapsed")

    # 選択連動
    for s in st.session_state.spells:
        if s["name"] == selected_spell:
            if 'prev_sel' not in st.session_state or st.session_state.prev_sel != selected_spell:
                ticker_input = s["ticker"]
                st.session_state.prev_sel = selected_spell

    st.divider()
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.session_state.spells[i]["name"] = st.text_input(f"なまえ {i+1}", value=st.session_state.spells[i]["name"], key=f"n_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input(f"コード {i+1}", value=st.session_state.spells[i]["ticker"], key=f"t_{i}").upper()

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

        # LPPLS解析
        df_recent = df.reset_index()
        time = [pd.Timestamp.toordinal(d) for d in df_recent['Date']]
        price = np.log(df_recent['Close'].values.flatten())
        lppls_model = lppls.LPPLS(observations=np.array([time, price]))
        tc, m, w, a, b, c, c1, c2, O, D = lppls_model.fit(max_searches=30)
        critical_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

        # --- 【復活】ステータス表示 ---
        st.markdown(f"<h3>{ticker} の ステータス</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("かかく (G)", f"{df['Close'].iloc[-1]:,.2f}")
        col2.metric("きりょく (RSI)", f"{df['RSI'].iloc[-1]:.1f}")
        col3.metric("かいり (DIV)", f"{df['Divergence'].iloc[-1]:.1f}")

        # --- レポート表示 ---
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(f"▼ {ticker} を しらべた！")
        today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
        
        rsi_val = df['RSI'].iloc[-1]
        if rsi_val > 70: st.markdown('- <span style="color:#ff0000">てきは こうふんしている！</span>', unsafe_allow_html=True)
        elif rsi_val < 30: st.markdown('- <span style="color:#00ff00">てきは つかれている！ チャンスだ！</span>', unsafe_allow_html=True)
        
        if critical_date > today_str:
            st.markdown(f'- <span style="color:#ff0000">おそろしい よかんがする… くるべきときは {critical_date}！</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'- <span style="color:#00ff00">あらしは すぎさった。 いまは しずかだ。</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # チャート
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="かかく", line=dict(color='#ffffff', width=3)))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="DotGothic16", color="#ffffff"),
            xaxis=dict(showgrid=False), 
            yaxis=dict(showgrid=True, gridcolor='#333333')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
