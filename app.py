import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import time

# 1. 페이지 및 상태 설정
st.set_page_config(page_title="미주/한주 분석기 (민짱 Pro)", layout="wide", initial_sidebar_state="expanded")

if 'menu' not in st.session_state: st.session_state.menu = "🏠 0. 메인 홈 (대시보드)"
if 'search_ticker' not in st.session_state: st.session_state.search_ticker = ""
if 'market' not in st.session_state: st.session_state.market = "US"

st.markdown("""
<style>
    .stApp { background-color: #111111; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 26px; color: #3B82F6; font-weight: bold; }
    [data-testid="stMetricDelta"] { font-size: 15px; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 🌐 실시간 환율 및 공통 함수 ---
@st.cache_data(ttl=3600)
def get_krw_rate():
    try: return float(yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1])
    except: return 1350.0
krw_rate = get_krw_rate()

def price_format(val, market):
    if market == "US": return f"${val:,.2f} (약 {val * krw_rate:,.0f}원)"
    else: return f"₩{val:,.0f}"

def large_krw(val, market):
    krw = val * krw_rate if market == "US" else val
    if krw >= 1e12: return f"{krw/1e12:.2f}조 원"
    elif krw >= 1e8: return f"{krw/1e8:.0f}억 원"
    return f"{krw:,.0f}원"

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def predict_5d_return(current_price, hist, current_rsi):
    past_5d = (current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100 if len(hist) > 5 else 0
    if current_rsi < 40: return abs(past_5d) * 0.4 + 2.5
    elif current_rsi > 70: return -abs(past_5d) * 0.4 - 2.0
    else: return past_5d * 0.3

def get_safe_history(ticker_symbol, period="3mo"):
    try:
        df = yf.Ticker(ticker_symbol).history(period=period)
        if df is not None and not df.empty and len(df) > 5: return df
        return None
    except: return None

def go_to_analysis(ticker, market):
    st.session_state.search_ticker = ticker
    st.session_state.market = market
    st.session_state.menu = "🔍 1. 종목 분석 & 7대 리포트"

# --- 📚 한글 검색 만능 사전 (미국 + 한국) ---
us_map = {
    "테슬라": "TSLA", "애플": "AAPL", "엔비디아": "NVDA", "팔란티어": "PLTR", "마이크로소프트": "MSFT", 
    "마소": "MSFT", "구글": "GOOGL", "아마존": "AMZN", "나스닥3배": "TQQQ", "반도체3배": "SOXL", "엔비디아2배": "NVDL"
}
kr_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "LG에너지솔루션": "373220.KS", "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS", "기아": "000270.KS", "셀트리온": "068270.KS", "포스코홀딩스": "005490.KS", "네이버": "035420.KS",
    "카카오": "035720.KS", "한화에어로스페이스": "012450.KS", "두산에너빌리티": "034020.KS", "에코프로": "086520.KQ", "알테오젠": "196170.KQ"
}

# --- 2. 사이드바 메뉴 ---
st.sidebar.title("📈 민짱 Pro (Global)")
utc_now = datetime.utcnow()
st.sidebar.markdown(f"⏱️ **한국 기준:** {(utc_now + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')}")
st.sidebar.markdown(f"💵 **적용 환율:** {krw_rate:,.2f}원")
st.sidebar.markdown("---")

menus = ["🏠 0. 메인 홈 (대시보드)", "🔍 1. 종목 분석 & 7대 리포트", "🚀 2. 테마별 종목 모아보기", "🔥 3. 급등주 탐지기", "🏆 4. AI 5일 수익률 랭킹"]
st.sidebar.radio("메뉴를 선택하세요:", menus, key="menu")
menu = st.session_state.menu

# ==========================================
# 메뉴 0: 메인 홈 (미국 + 한국 지수 통합)
# ==========================================
if menu == "🏠 0. 메인 홈 (대시보드)":
    st.title("환영합니다! 📈 미주/한주 통합 분석기 (민짱 Pro)")
    st.markdown("미국 주식부터 한국 주식까지, 글로벌 시장의 맥을 짚어보세요.")
    st.markdown("---")
    st.subheader("🌐 글로벌 증시 & 매크로 현황")
    with st.spinner('데이터 로딩 중...'):
        c1, c2, c3, c4 = st.columns(4)
        indices = {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "KOSPI": "^KS11", "KOSDAQ": "^KQ11"}
        cols = [c1, c2, c3, c4]
        for i, (name, ticker) in enumerate(indices.items()):
            df = get_safe_history(ticker, "5d")
            if df is not None:
                cols[i].metric(name, f"{df['Close'].iloc[-1]:,.2f}", f"{df['Close'].iloc[-1] - df['Close'].iloc[-2]:,.2f}")
    st.markdown("---")
    st.info("👈 왼쪽 메뉴를 클릭해서 분석을 시작하세요!")

# ==========================================
# 메뉴 1: 개별 종목 분석 (국가 선택 스위치 탑재)
# ==========================================
elif menu == "🔍 1. 종목 분석 & 7대 리포트":
    st.title("🔍 글로벌 종목 정밀 분석")
    
    # 국가 선택 라디오 버튼
    market_choice = st.radio("🌍 분석할 시장을 선택하세요:", ["🇺🇸 미국 주식 (US)", "🇰🇷 한국 주식 (KR)"], horizontal=True)
    current_market = "US" if "US" in market_choice else "KR"
    
    placeholder = "종목 코드 또는 기업명 (예: TSLA, 애플)" if current_market == "US" else "기업명 또는 6자리 종목코드 (예: 삼성전자, 005930)"
    user_input = st.text_input(placeholder, st.session_state.search_ticker if st.session_state.market == current_market else "")
    
    if user_input != "":
        clean_in = user_input.replace(" ", "").upper()
        
        # 한국/미국 티커 변환 로직
        if current_market == "US":
            ticker_symbol = us_map.get(user_input.replace(" ", "").lower(), clean_in)
        else:
            # 한국 시장 로직 (사전에 있으면 변환, 6자리 숫자면 .KS 붙이기)
            if user_input.replace(" ", "") in kr_map:
                ticker_symbol = kr_map[user_input.replace(" ", "")]
            elif clean_in.isdigit() and len(clean_in) == 6:
                ticker_symbol = f"{clean_in}.KS" # 기본 코스피 매핑
            else:
                ticker_symbol = clean_in

        with st.spinner(f'{ticker_symbol} 데이터 영혼까지 끌어오는 중...'):
            hist = get_safe_history(ticker_symbol, "1y")
            if hist is None: 
                st.warning("데이터를 찾을 수 없습니다. (한국 주식은 '삼성전자' 또는 '005930' 형식으로 입력하세요)")
            else:
                info = yf.Ticker(ticker_symbol).info
                p, prev_p = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                chg, chg_pct = p - prev_p, (p-prev_p)/prev_p*100
                
                st.markdown(f"### {info.get('longName', ticker_symbol)} ({ticker_symbol})")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("현재가", f"{'₩' if current_market=='KR' else '$'}{p:,.2f}", f"{chg:,.2f} ({chg_pct:.2f}%)")
                if current_market == "US": c1.write(f"🇰🇷 약 {p * krw_rate:,.0f}원")
                
                target = info.get('targetMeanPrice', 'N/A')
                if target != 'N/A': c2.metric("목표가", f"{'₩' if current_market=='KR' else '$'}{target:,.2f}")
                else: c2.metric("52주 고가", f"{'₩' if current_market=='KR' else '$'}{info.get('fiftyTwoWeekHigh', p):,.2f}")
                
                turnover = p * hist['Volume'].iloc[-1]
                c3.metric("당일 거래량", f"{hist['Volume'].iloc[-1]:,.0f}주")
                c3.write(f"💰 {large_krw(turnover, current_market)}")
                
                mcap = info.get('marketCap', 0)
                c4.metric("시가총액", large_krw(mcap, current_market))
                
                hist['SMA20'] = hist['Close'].rolling(20).mean()
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.8])
                fig.add_trace(go.Candlestick(x=hist.index[-126:], open=hist['Open'][-126:], high=hist['High'][-126:], low=hist['Low'][-126:], close=hist['Close'][-126:], name='주가', increasing_line_color='red', decreasing_line_color='blue'), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist.index[-126:], y=hist['SMA20'][-126:], line=dict(color='orange', width=1)), row=1, col=1)
                fig.add_trace(go.Bar(x=hist.index[-126:], y=hist['Volume'][-126:], marker_color='gray'), row=2, col=1)
                fig.update_layout(height=450, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                t1, t2 = st.tabs(["📝 7대 매트릭스", "🤖 실전 매매 타점"])
                with t1:
                    st.write(f"- 애널리스트 의견: **{info.get('recommendationKey', 'N/A').upper()}**")
                    st.write(f"- P/E Ratio: {info.get('trailingPE', 'N/A')}")
                with t2:
                    entry = p * 0.98
                    st.success(f"🎯 **추천 진입가 (눌림목):** {price_format(entry, current_market)}")
                    st.error(f"🚨 **칼손절가 (-5%):** {price_format(entry*0.95, current_market)}")

# ==========================================
# 메뉴 2: 테마별 종목 (네가 요청한 대규모 테마)
# ==========================================
elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 글로벌 테마별 관련주 스캔")
    market_choice = st.radio("🌍 시장 선택:", ["🇺🇸 미국 테마", "🇰🇷 한국 테마"], horizontal=True)
    
    if "US" in market_choice:
        themes = {
            "우주/항공": ["ASTS", "RKLB", "LUNR", "BA", "LMT"], "AI/반도체": ["NVDA", "AMD", "TSM", "PLTR", "ARM"], 
            "빅테크": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"], "방산/밀리터리": ["LMT", "RTX", "NOC", "GD"], 
            "바이오/제약": ["LLY", "NVO", "JNJ", "PFE"], "전력/에너지": ["NEE", "DUK", "SO", "XOM", "CVX"],
            "건설/인프라": ["CAT", "DE", "URI"], "운송/물류": ["DAL", "UAL", "FDX", "UPS"]
        }
        current_market = "US"
    else:
        themes = {
            "반도체 (HBM 등)": ["005930.KS", "000660.KS", "042700.KS", "077360.KQ"], "2차전지": ["373220.KS", "003670.KS", "006400.KS", "086520.KQ"], 
            "바이오/제약": ["207940.KS", "068270.KS", "000100.KS", "196170.KQ"], "방산/우주": ["012450.KS", "047810.KS", "062210.KS", "079550.KS"], 
            "전력/원전": ["015760.KS", "034020.KS", "051600.KS", "241560.KS"], "건설/기계": ["000720.KS", "024110.KS", "042670.KS"], 
            "운송/해운": ["011200.KS", "003280.KS", "028670.KS", "134260.KS"], "금융/지주": ["105560.KS", "055550.KS", "316140.KS"]
        }
        current_market = "KR"

    selected_theme = st.selectbox("테마 선택:", list(themes.keys()))
    
    if st.button("🚀 스캔 시작"):
        my_bar = st.progress(0)
        st.markdown("---")
        for i, t in enumerate(themes[selected_theme]):
            h = get_safe_history(t, "5d")
            if h is not None:
                p, prev_p = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = (p-prev_p)/prev_p*100
                c1, c2, c3 = st.columns([3, 4, 3])
                c1.markdown(f"### {t}")
                c2.markdown(f"**{price_format(p, current_market)}** ({chg:+.2f}%)")
                c3.button(f"🔍 분석", key=f"thm_{t}", on_click=go_to_analysis, args=(t, current_market))
                st.markdown("---")
            my_bar.progress(int(((i+1)/len(themes[selected_theme]))*100))

# ==========================================
# 메뉴 3: 급등주 탐지기
# ==========================================
elif menu == "🔥 3. 급등주 탐지기":
    st.subheader("🔥 실시간 거래대금 급등주 스캐너")
    market_choice = st.radio("🌍 시장 선택:", ["🇺🇸 미국 시장", "🇰🇷 한국 시장"], horizontal=True)
    current_market = "US" if "US" in market_choice else "KR"
    
    if st.button("🚀 스캔 시작"):
        if current_market == "US":
            tickers = ["TSLA", "NVDA", "ASTS", "MSTR", "PLTR", "SOXL", "COIN", "MARA", "LUNR", "GME", "SMCI", "ARM"]
        else:
            tickers = ["005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", "068270.KS", "011200.KS", "042700.KS", "012450.KS", "034020.KS", "086520.KQ", "196170.KQ"]
            
        my_bar = st.progress(0, text="대장주 스캔 중...")
        res = []
        for i, t in enumerate(tickers):
            h = get_safe_history(t, "1mo")
            if h is not None and len(h) > 20:
                p, prev_p, vol = float(h['Close'].iloc[-1]), float(h['Close'].iloc[-2]), float(h['Volume'].iloc[-1])
                chg, turnover = (p - prev_p) / prev_p * 100, p * vol
                if chg > 0: res.append({"t": t, "p": p, "chg": chg, "vol": vol, "turnover": turnover, "score": chg * np.log10(max(turnover, 1))})
            my_bar.progress(int(((i+1)/len(tickers))*100))
            
        if res:
            st.success("✅ 스캔 완료!")
            for i, s in enumerate(sorted(res, key=lambda x: x['score'], reverse=True)[:3]):
                st.markdown(f"### 🥇 {i+1}위: {s['t']} (+{s['chg']:.2f}%)")
                c1, c2 = st.columns([7, 3])
                with c1:
                    st.write(f"**현재가:** {price_format(s['p'], current_market)}")
                    st.write(f"💰 **거래대금:** 약 **{large_krw(s['turnover'], current_market)}** 터짐! 🔥")
                with c2: st.button(f"🔍 분석", key=f"urg_{s['t']}", on_click=go_to_analysis, args=(s['t'], current_market))
                st.info(f"🎯 **추천 진입가:** {price_format(s['p']*0.98, current_market)} | 🚨 **손절가:** {price_format(s['p']*0.98*0.95, current_market)}")
                st.markdown("---")

# ==========================================
# 메뉴 4: AI 5일 수익률 랭킹
# ==========================================
elif menu == "🏆 4. AI 5일 수익률 랭킹":
    st.subheader("🏆 AI 5일 후 예상 수익률 랭킹")
    market_choice = st.radio("🌍 시장 선택:", ["🇺🇸 미국 시장", "🇰🇷 한국 시장"], horizontal=True)
    current_market = "US" if "US" in market_choice else "KR"
    
    if st.button("🔮 전 종목 AI 예측 스캔"):
        if current_market == "US":
            scan_list = ["TSLA", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "PLTR", "ASTS"]
        else:
            scan_list = ["005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", "068270.KS", "035420.KS", "035720.KS", "011200.KS", "042700.KS"]
            
        my_bar = st.progress(0, text="AI 타점 계산 중...")
        pred = []
        for i, t in enumerate(scan_list):
            h = get_safe_history(t, "3mo")
            if h is not None and len(h) > 20:
                p = float(h['Close'].iloc[-1])
                rsi = float(calculate_rsi(h).iloc[-1])
                exp_return = predict_5d_return(p, h, rsi)
                entry_p = p * 0.98
                real_return = ((p * (1 + (exp_return / 100))) - entry_p) / entry_p * 100
                pred.append({"t": t, "entry": entry_p, "return": real_return})
            my_bar.progress(int(((i+1)/len(scan_list))*100))
            
        if pred:
            st.success("✅ 예측 완료!")
            for _, row in pd.DataFrame(pred).sort_values(by="return", ascending=False).head(5).iterrows():
                c1, c2, c3, c4 = st.columns([2, 3, 3, 2])
                c1.markdown(f"**{row['t']}**")
                c2.markdown(f"기대수익: **<span style='color:#ff4b4b;'>+{row['return']:.2f}%</span>**", unsafe_allow_html=True)
                c3.markdown(f"타점: {price_format(row['entry'], current_market)}")
                c4.button(f"🔍 분석", key=f"ai_{row['t']}", on_click=go_to_analysis, args=(row['t'], current_market))
                st.markdown("---")
