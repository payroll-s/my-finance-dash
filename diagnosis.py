import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go

# --- ページ設定 ---
st.set_page_config(page_title="Dragon King's Lair", layout="wide")

# --- CSS：レンガ壁に「絶対に白くならない」黒い窓を設置 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&display=swap');

    /* 1. メイン背景 */
    .stApp { background-color: #000000 !important; font-family: 'DotGothic16', sans-serif !important; }

    /* 2. レンガ造りのサイドバー */
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

    /* 3. テキストの視認性向上 */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ffffff !important;
        text-shadow: 2px 2px 0px #000000;
    }

    /* 4. 入力欄（マスターデザイン） */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border: 4px solid #ffffff !important;
        border-radius: 0px !important;
    }
    input { color: #ffffff !important; background-color: #000000 !important; }

    /* 5. ★ 呪文ボタンの最終物理改造 ★ */
    /* 全てのボタンのデフォルトスタイルを完全に破壊して上書き */
    div.stButton > button {
        background-color: #000000 !important; /* 絶対に黒 */
        color: #ffffff !important;           /* 絶対に白 */
        border: 4px solid #ffffff !important; /* 絶対に太い白枠 */
        border-radius: 0px !important;
        width: 100% !important;
        height: 50px !important;              /* 高さを出して入力欄に寄せる */
        font-family: 'DotGothic16', sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        text-align: center !important;
        margin-top: 10px !important;
        box-shadow: 6px 6px 0px #000000 !important; /* 強い影で立体化 */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* ホバー時だけ反転させる */
    div.stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 4px solid #ffffff !important;
    }

    /* ボタンの中の余計なレイヤーを非表示にする */
    div.stButton > button div {
        color: inherit !important;
    }

    /* 6. その他装飾 */
    .report-card, .stMetric { background-color: #000000 !important; border: 4px solid #ffffff !important; }
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

# --- サイドバー：コマンドウィンドウ ---
with st.sidebar:
    st.markdown("<h3>[ コマンド ]</h3>", unsafe_allow_html=True)
    
    # 銘柄入力（これが基準のデザイン）
    ticker_input = st.text_input("しらべる 銘柄コード:", value="XRP-USD", key="main_ticker_input").upper()
    
    st.write("▼ おぼえている じゅもん")
    
    # ★ 呪文メニュー専用スタイル（ポップアップには干渉しません）
    st.markdown("""
        <style>
        /* 4つのボタンを包む白い枠（入力欄と同じ仕様） */
        .spell-box {
            border: 4px solid #ffffff !important;
            background-color: #000000 !important;
            padding: 5px !important;
            margin-bottom: 20px !important;
        }

        /* 枠の中のボタンを「文字だけの選択肢」にする */
        .spell-box .stButton > button {
            background-color: transparent !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 0px !important;
            width: 100% !important;
            text-align: left !important;
            font-family: 'DotGothic16', sans-serif !important;
            font-size: 1.1rem !important;
            padding: 5px 10px !important;
        }

        /* ホバー時のみ反転 */
        .spell-box .stButton > button:hover {
            background-color: #ffffff !important;
            color: #000000 !important;
        }

        /* クリック時の余計なエフェクトを削除 */
        .spell-box .stButton > button:focus {
            box-shadow: none !important;
            outline: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 白枠の開始
    st.markdown('<div class="spell-box">', unsafe_allow_html=True)
    
    # 重複エラーを避けるため、一意のKey（final_spell_...）を設定
    for i, spell in enumerate(st.session_state.spells):
        if st.button(f"・{spell['name']}", key=f"final_spell_{i}", help=f"{spell['desc']} ({spell['ticker']})"):
            ticker_input = spell["ticker"]
            
    st.markdown('</div>', unsafe_allow_html=True)
    # 白枠の終了

    st.divider()
    
    # 「じゅもんを書き換える」部分もKeyの重複を避けるために修正
    with st.expander("じゅもんを 書き換える"):
        for i in range(len(st.session_state.spells)):
            st.write(f"--- じゅもん {i+1} ---")
            st.session_state.spells[i]["name"] = st.text_input("なまえ", value=st.session_state.spells[i]["name"], key=f"edit_name_{i}")
            st.session_state.spells[i]["ticker"] = st.text_input("コード", value=st.session_state.spells[i]["ticker"], key=f"edit_tick_{i}").upper()
            st.session_state.spells[i]["desc"] = st.text_input("かいせつ", value=st.session_state.spells[i]["desc"], key=f"edit_desc_{i}")

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

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="かかく", line=dict(color='#ffffff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="DotGothic16", color="#ffffff"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("▼ お返事がない。 ただの しかばね の ようだ。")
