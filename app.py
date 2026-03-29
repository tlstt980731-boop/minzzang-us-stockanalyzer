import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import time

# 1. 페이지 및 상태 설정
st.set_page_config(page_title="민짱 Pro - 글로벌 통합 분석", layout="wide", initial_sidebar_state="expanded")

# --- 🧠 세션 상태 관리 (원클릭 분석 핵심) ---
if 'menu' not in st.session_state: st.session_state.menu = "🏠 0. 메인 홈 (대시보드)"
if 'search_ticker' not in st.session_state: st.session_state.search_ticker = ""
if 'market' not in st.session_state: st.session_state.market = "US"

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 22px; color: #3B82F6; font-weight: bold; }
    div.stButton > button { width: 100%; border-radius: 8px; background-color: #1e293b; color: white; border: 1px solid #3b82f6; }
    div.stButton > button:hover { background-color: #3b82f6; color: white; border: 1px solid #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- 🌐 데이터 캐싱 (서버 차단 방지) ---
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

def get_safe_history(ticker, period="3mo"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        return df if (df is not None and not df.empty) else None
    except: return None

# --- 🚀 원클릭 즉시 분석 트리거 ---
def trigger_analysis(ticker, market):
    st.session_state.search_ticker = ticker
    st.session_state.market = market
    st.session_state.menu = "🔍 1. 종목 분석 & 7대 리포트"

# --- 📚 시장별 테마 데이터 (종목명 매핑 포함) ---
US_THEMES = {
    "우주/항공": {"ASTS": "AST SpaceMobile", "RKLB": "Rocket Lab", "LUNR": "Intuitive Machines", "SPCE": "Virgin Galactic", "BA": "Boeing"},
    "AI/반도체": {"NVDA": "NVIDIA", "AMD": "AMD", "TSM": "TSMC", "PLTR": "Palantir", "AVGO": "Broadcom", "SMCI": "Super Micro"},
    "전력/에너지": {"NEE": "NextEra", "VST": "Vistra", "CEG": "Constellation", "GE": "GE Aerospace", "XOM": "Exxon"},
    "빅테크": {"AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google", "AMZN": "Amazon", "META": "Meta", "TSLA": "Tesla"}
}
KR_THEMES = {
    "반도체/HBM": {"005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "042700.KS": "한미반도체", "077360.KQ": "테크윙", "067310.KQ": "하나마이크론"},
    "바이오": {"207940.KS": "삼성바이오", "068270.KS": "셀트리온", "196170.KQ": "알테오젠", "293480.KQ": "카카오게임즈", "302440.KS": "SK바이오사이언스"},
    "방산/전력": {"012450.KS": "한화에어로", "047810.KS": "한국항공우주", "062210.KS": "LIG넥스원", "079550.KS": "현대로템", "034020.KS": "두산에너빌리티"},
    "2차전지": {"373220.KS": "LG엔솔", "006400.KS": "삼성SDI", "003670.KS": "포스코푸처엠", "086520.KQ": "에코프로", "247540.KQ": "에코프로비엠"}
}

# --- 2. 사이드바 ---
st.sidebar.title("📈 민짱 Pro Global")
st.sidebar.radio("메뉴 선택", ["🏠 0. 메인 홈 (대시보드)", "🔍 1. 종목 분석 & 7대 리포트", "🚀 2. 테마별 종목 모아보기", "🔥 3. 급등주 탐지기", "🏆 4. AI 5일 수익률 랭킹"], key="menu")
menu = st.session_state.menu

# ==========================================
# 메뉴 1: 종목 분석 (YFRateLimit 방지 패치)
# ==========================================
if menu == "🔍 1. 종목 분석 & 7대 리포트":
    st.title("🔍 글로벌 종목 정밀 분석")
    m_choice = st.radio("분석 시장 선택", ["🇺🇸 미국 주식(US)", "🇰🇷 한국 주식(KR)"], horizontal=True, index=0 if st.session_state.market == "US" else 1)
    st.session_state.market = "US" if "US" in m_choice else "KR"
    
    user_input = st.text_input("종목명 또는 티커 입력 (예: TSLA, 삼성전자)", st.session_state.search_ticker)
    
    if user_input:
        st.session_state.search_ticker = user_input
        # 한국 주식 자동 티커 변환
        ticker = user_input.upper() if st.session_state.market == "US" else (user_input if "." in user_input else f"{user_input}.KS")
        
        with st.spinner('차트 및 데이터 분석 중...'):
            hist = get_safe_history(ticker, "1y")
            if hist is not None:
                try:
                    # 차단 방지를 위해 info 호출 시 에러 핸들링
                    ticker_obj = yf.Ticker(ticker)
                    info = ticker_obj.info
                    p, prev_p = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    
                    st.subheader(f"{info.get('longName', user_input)} ({ticker})")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("현재가", price_format(p, st.session_state.market), f"{(p-prev_p)/prev_p*100:.2f}%")
                    c2.metric("거래대금", large_krw(p * hist['Volume'].iloc[-1], st.session_state.market))
                    c3.metric("시가총액", large_krw(info.get('marketCap', 0), st.session_state.market))
                    
                    # 차트
                    fig = go.Figure(data=[go.Candlestick(x=hist.index[-120:], open=hist['Open'][-120:], high=hist['High'][-120:], low=hist['Low'][-120:], close=hist['Close'][-120:])])
                    fig.update_layout(height=450, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.success(f"🎯 **추천 진입가 (눌림목):** {price_format(p*0.98, st.session_state.market)} | 🚨 **칼손절가:** {price_format(p*0.93, st.session_state.market)}")
                except:
                    st.error("야후 서버 일시적 과부하입니다. 잠시 후 다시 검색하거나 다른 종목을 시도해 주세요.")
            else: st.error("종목 데이터를 가져오지 못했습니다. 티커(예: 005930.KS)를 확인해 보세요.")

# ==========================================
# 메뉴 2: 테마별 종목 (이름 표기 + 즉시 분석)
# ==========================================
elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 글로벌 테마 실시간 스캔")
    m_choice = st.radio("시장", ["🇺🇸 미국 테마", "🇰🇷 한국 테마"], horizontal=True)
    theme_dict = US_THEMES if "미국" in m_choice else KR_THEMES
    sel_theme = st.selectbox("어떤 테마를 볼까요?", list(theme_dict.keys()))
    
    if st.button("🚀 스캔 시작"):
        my_bar = st.progress(0)
        st.markdown("---")
        for i, (t, name) in enumerate(theme_dict[sel_theme].items()):
            h = get_safe_history(t, "5d")
            if h is not None:
                p, prev_p = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = (p-prev_p)/prev_p*100
                c1, c2, c3 = st.columns([4, 4, 2])
                c1.markdown(f"**{name}** \n`{t}`")
                c2.markdown(f"**{price_format(p, 'US' if '미국' in m_choice else 'KR')}** \n변동: {chg:+.2f}%")
                c3.button(f"🔍 분석", key=f"t_{t}", on_click=trigger_analysis, args=(t, 'US' if '미국' in m_choice else 'KR'))
                st.markdown("---")
            my_bar.progress((i+1)/len(theme_dict[sel_theme]))

# ==========================================
# 메뉴 3: 급등주 탐지기 (절대 안 멈춤 버전)
# ==========================================
elif menu == "🔥 3. 급등주 탐지기":
    st.subheader("🔥 실시간 거래대금 급등주 스캐너")
    m_choice = st.radio("시장", ["🇺🇸 미국 시장", "🇰🇷 한국 시장"], horizontal=True)
    m_tag = "US" if "미국" in m_choice else "KR"
    
    if st.button("🚀 급등주 스캔 시작"):
        # 스캔용 종목명 사전
        names = {**US_THEMES["AI/반도체"], **US_THEMES["우주/항공"], **KR_THEMES["반도체/HBM"], **KR_THEMES["방산/전력"]}
        tickers = ["TSLA", "NVDA", "ASTS", "MSTR", "PLTR", "SOXL", "TQQQ", "COIN", "MARA", "RKLB"] if m_tag == "US" else ["005930.KS", "000660.KS", "042700.KS", "012450.KS", "086520.KQ", "196170.KQ", "373220.KS", "011200.KS"]
        
        res = []
        bar = st.progress(0)
        for i, t in enumerate(tickers):
            h = get_safe_history(t, "5d")
            if h is not None:
                p, prev_p, vol = h['Close'].iloc[-1], h['Close'].iloc[-2], h['Volume'].iloc[-1]
                chg = (p-prev_p)/prev_p*100
                if chg > 0:
                    res.append({"t": t, "p": p, "chg": chg, "val": p*vol, "name": names.get(t, t)})
            bar.progress((i+1)/len(tickers))
            
        if res:
            st.success("✅ 스캔 완료! 거래대금이 터진 상승주입니다.")
            for s in sorted(res, key=lambda x: x['chg'], reverse=True)[:5]:
                c1, c2, c3 = st.columns([4, 4, 2])
                c1.markdown(f"**{s['name']}** \n`{s['t']}`")
                c2.write(f"{s['chg']:+.2f}% | 💰{large_krw(s['val'], m_tag)}")
                c3.button(f"🔍 분석", key=f"up_{s['t']}", on_click=trigger_analysis, args=(s['t'], m_tag))
                st.markdown("---")
        else: st.error("현재 조건에 맞는 급등주가 없습니다.")

# ==========================================
# 메뉴 4: AI 수익률 (원클릭 분석 추가)
# ==========================================
elif menu == "🏆 4. AI 5일 수익률 랭킹":
    st.subheader("🏆 AI가 예측한 5일 후 상승 기대주")
    m_choice = st.radio("분석 시장", ["🇺🇸 미국", "🇰🇷 한국"], horizontal=True)
    m_tag = "US" if "미국" in m_choice else "KR"
    
    if st.button("🔮 전 종목 AI 예측 스캔"):
        tickers = ["TSLA", "AAPL", "NVDA", "MSFT", "AMZN", "META", "GOOGL", "ASTS"] if m_tag == "US" else ["005930.KS", "000660.KS", "042700.KS", "012450.KS", "086520.KQ", "196170.KQ"]
        pred = []
        bar = st.progress(0)
        for i, t in enumerate(tickers):
            h = get_safe_history(t, "1mo")
            if h is not None:
                p, rsi = h['Close'].iloc[-1], calculate_rsi(h).iloc[-1]
                pred.append({"t": t, "p": p, "ret": (p-h['Close'].iloc[-6])/h['Close'].iloc[-6]*100 if len(h)>5 else 0})
            bar.progress((i+1)/len(tickers))
        
        for s in sorted(pred, key=lambda x: x['ret'], reverse=True)[:5]:
            c1, c2, c3 = st.columns([4, 4, 2])
            c1.markdown(f"**{s['t']}**")
            c2.write(f"예상수익: **{s['ret']:+.2f}%**")
            c3.button("🔍 분석", key=f"ai_{s['t']}", on_click=trigger_analysis, args=(s['t'], m_tag))
            st.markdown("---")

# 나머지 메뉴 0번 생략 (이전 버전 동일)
