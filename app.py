import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from lppls import lppls
import plotly.graph_objects as go
import plotly.express as px

# ページ基本設定
st.set_page_config(page_title="Dragon King Theory", layout="wide")

# --- サイバー・スタイル（翻訳アイコン修復版） ---
st.markdown("""
    <style>
    /* 全テキストをシアン（水色）に統一 */
    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #00f2ff !important;
        font-family: 'Courier New', monospace;
    }
    .stApp {
        background-color: #050a14;
        background-image: radial-gradient(circle at 50% 50%, #112244 0%, #050a14 100%);
    }
    
    /* ヘルプアイコン（？）の色と視認性を修復 */
    [data-testid="stMarker"] {
        color: #00f2ff !important;
        opacity: 1 !important;
    }
    div[data-testid="stTooltipHoverTarget"] svg {
        fill: #00f2ff !important;
    }

    /* サイドバー・スタイル */
    [data-testid="stSidebar"] {
        background-color: rgba(5, 10, 20, 0.95) !important;
        border-right: 1px solid #00f2ff;
    }

    /* 各種カード・エクスパンダー */
    .stMetric, .portfolio-card, .stExpander {
        background-color: rgba(16, 20, 35, 0.8) !important;
        border: 1px solid #00f2ff !important;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.3);
    }
    
    .portfolio-card {
        border: 2px solid #00f2ff !important;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.4);
        padding: 30px;
        margin-bottom: 30px;
    }

    /* タイトル：DRAGON KING THEORY */
    .main-title {
        color: #00f2ff !important;
        text-transform: uppercase;
        letter-spacing: 12px;
        text-shadow: 0 0 25px #00f2ff;
        text-align: center;
        font-size: 3.5rem !important;
        margin-top: 20px;
        margin-bottom: 40px;
        cursor: help;
    }

    [data-testid="stMetricValue"] {
        color: #00f2ff !important;
        text-shadow: 0 0 15px #00f2ff;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }

    input, textarea, select, .stTextInput div, .stNumberInput div {
        background-color: #050a14 !important;
        color: #00f2ff !important;
        border-color: #00f2ff !important;
    }

    .stButton>button {
        width: 100%;
        background: transparent !important;
        color: #00f2ff !important;
        border: 1px solid #00f2ff !important;
    }
    .stButton>button:hover {
        background: #00f2ff !important;
        color: #050a14 !important;
        box-shadow: 0 0 20px #00f2ff;
    }
    </style>
    """, unsafe_allow_html=True)

/* ツールチップ（吹き出し）自体のデザインを紺色に変更 */
    div[data-baseweb="tooltip"] {
        background-color: #050a14 !important; /* 深い紺色 */
        border: 1px solid #00f2ff !important; /* 水色の枠線 */
        border-radius: 8px !important;
    }

    /* ツールチップ内の文字色を水色に */
    div[data-baseweb="tooltip"] * {
        color: #00f2ff !important;
        background-color: transparent !important;
    }

    /* 吹き出しの「矢印」部分も紺色に */
    div[data-baseweb="tooltip"] div {
        background-color: transparent !important;
    }

# 1. ページタイトル（マウスオーバーで「龍王理論」と表示）
st.markdown('<h1 class="main-title" title="龍王理論：資産運用ターミナル">DRAGON KING THEORY</h1>', unsafe_allow_html=True)

# --- サイドバー構成 ---
with st.sidebar:
    st.markdown('<h2 title="監視銘柄の入力">🔍 SCAN TARGETS</h2>', unsafe_allow_html=True)
    ticker_input = st.text_input("SCAN TICKERS", value="XRP-USD, 7203.T, 3140.T, AAPL", help="分析したい銘柄コードをカンマ区切りで入力。日本株は末尾に .T").upper()
    tickers = [t.strip() for t in ticker_input.split(",")]

    st.divider()
    st.markdown('<h2 title="保有艦隊データ">🛸 FLEET DATA</h2>', unsafe_allow_html=True)
    if 'rows' not in st.session_state: st.session_state.rows = 3
    pf_data_list = []
    for i in range(st.session_state.rows):
        st.markdown(f"**Unit {i+1}**")
        col1, col2, col3 = st.columns([2, 1.5, 1.5])
        tick = col1.text_input("UNIT ID", value="XRP-USD" if i==0 else "", key=f"t_{i}", help="銘柄コードを入力")
        price = col2.number_input("ENTRY", value=0.0, key=f"p_{i}", help="取得単価を入力")
        qty = col3.number_input("SIZE", value=0.0, key=f"q_{i}", help="保有数量を入力")
        if tick: pf_data_list.append({"銘柄": tick.upper(), "単価": price, "数量": qty})
    
    if st.button("🛰️ ADD UNIT SLOT", help="入力枠を拡張します"):
        st.session_state.rows += 1
        st.rerun()

    st.divider()
    st.markdown('<h2 title="アラート設定">🔔 ALERTS</h2>', unsafe_allow_html=True)
    alert_ticker = st.selectbox("TARGET TICKET", tickers, help="アラート対象銘柄を選択")
    target_price = st.number_input("TARGET PRICE", value=0.0, help="この価格以下で通知発動")

# --- 関数定義 ---
def get_live_pf(data_list):
    res = []
    t_cost, t_val = 0, 0
    for item in data_list:
        try:
            t, p, q = item["銘柄"], item["単価"], item["数量"]
            if q <= 0: continue
            df = yf.download(t, period="1d", progress=False)
            curr_p = float(df['Close'].iloc[-1])
            val, cost = curr_p * q, p * q
            res.append({"銘柄": t, "評価額": val, "損益": val - cost})
            t_cost += cost
            t_val += val
        except: continue
    return pd.DataFrame(res), t_cost, t_val

# --- 2. ポートフォリオ合計エリア ---
st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
st.markdown("<h3 title='艦隊評価額の合計' style='color:#00f2ff; text-align:center;'>🌌 TOTAL ASSET VALUE</h3>", unsafe_allow_html=True)

pf_df, total_cost, total_value = get_live_pf(pf_data_list)
if not pf_df.empty:
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    c1.metric("TOTAL VALUE", f"¥{total_value:,.0f}" if "T" in ticker_input else f"${total_value:,.2f}", help="現在の総評価額（円/ドル）")
    c2.metric("TOTAL P/L", f"{(total_value-total_cost):,.2f}", delta=f"{((total_value-total_cost)/total_cost*100):.2f}%", help="通算損益額と損益率")
    
    fig_pie = px.pie(pf_df, values='評価額', names='銘柄', hole=.6)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00f2ff", height=180, showlegend=False)
    fig_pie.update_traces(marker=dict(colors=['#00f2ff', '#00d1ff', '#00a0ff', '#0070ff']))
    c3.plotly_chart(fig_pie, use_container_width=True)
else:
    st.markdown('<p style="color:#00f2ff; text-align:center; border:1px dashed #00f2ff; padding:20px;" title="サイドバーでデータを入力してください">⚠️ SYSTEM IDLE: PLEASE ENTER FLEET DATA.</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 個別分析セクション ---
for t_code in tickers:
    try:
        with st.expander(f"🛰️ SCANNING: {t_code}", expanded=True):
            stock = yf.Ticker(t_code)
            df = stock.history(start="2025-08-01")
            
            # 配当
            info = stock.info
            div_yield = info.get('dividendYield', 0)
            div_text = f"{div_yield * 100:.2f}%" if div_yield else "N/A"

            # 指標
            last_p = float(df['Close'].iloc[-1])
            delta = df['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]

            # LPPLS
            df_c = df[['Close']].dropna().reset_index()
            time = [pd.Timestamp.toordinal(d) for d in df_c['Date']]
            price = np.log(df_c['Close'].values.flatten())
            model = lppls.LPPLS(observations=np.array([time, price]))
            tc, m, w, a, b, c, c1, c2, O, D = model.fit(max_searches=20)
            crit_date = pd.Timestamp.fromordinal(int(tc)).strftime('%Y-%m-%d')

            # メトリクス（help引数で翻訳表示）
            ca, cb, cc = st.columns(3)
            ca.metric("PRICE", f"{last_p:,.2f}", help="現在の市場価格")
            cb.metric("DIV YIELD", div_text, help="予想配当利回り")
            cc.metric("X-DAY", crit_date, help="トレンド変化の臨界点（予測日）")

            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00f2ff', width=2))])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=220, margin=dict(l=0,r=0,t=0,b=0), font_color="#00f2ff", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#112244'))
            st.plotly_chart(fig, use_container_width=True)
    except: continue

