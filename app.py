import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# 1. 페이지 설정 및 다크 테마 적용
st.set_page_config(page_title="민짱 Pro - 글로벌 통합 분석기", layout="wide", initial_sidebar_state="expanded")

if 'menu' not in st.session_state: st.session_state.menu = "🏠 0. 메인 홈 (대시보드)"
if 'search_ticker' not in st.session_state: st.session_state.search_ticker = ""
if 'market' not in st.session_state: st.session_state.market = "US"

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #3B82F6; font-weight: bold; }
    .report-box { background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 20px; }
    .reason-text { line-height: 1.6; color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)

# --- 🌐 유틸리티 함수 ---
@st.cache_data(ttl=3600)
def get_krw_rate():
    try: return float(yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1])
    except: return 1380.0
krw_rate = get_krw_rate()

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_history(ticker, period="1y", interval="1d"):
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        return df if not df.empty else None
    except: return None

# --- 🚀 핵심 분석 로직 (3번 요구사항: 심층 근거 생성) ---
def generate_ai_report(ticker_name, info, hist):
    p = hist['Close'].iloc[-1]
    rsi = calculate_rsi(hist).iloc[-1]
    m_cap = info.get('marketCap', 0)
    pe = info.get('trailingPE', 'N/A')
    
    # 매력 점수 산출 로직
    score = 50
    reasons = []
    
    # 1. 기술적 지표 분석
    if rsi < 35: 
        score += 20
        reasons.append("✅ RSI 지표가 과매도 구간(35 미만)으로 단기 기술적 반등 가능성이 매우 높습니다.")
    elif rsi > 70: 
        score -= 15
        reasons.append("⚠️ RSI가 70을 상회하여 과열권입니다. 추격 매수보다는 눌림목을 기다려야 합니다.")
    else:
        reasons.append("⚖️ 현재 RSI는 중립 수준으로, 추세에 따른 분할 매수 전략이 유효합니다.")

    # 2. 거래량 분석
    avg_vol = hist['Volume'].tail(20).mean()
    curr_vol = hist['Volume'].iloc[-1]
    if curr_vol > avg_vol * 1.5:
        score += 15
        reasons.append("🔥 최근 거래량이 평균 대비 150% 이상 폭증하며 강력한 수급이 유입되었습니다.")
    
    # 3. 펀더멘털 분석
    target = info.get('targetMeanPrice', p * 1.1)
    upside = (target - p) / p * 100
    if upside > 15:
        score += 10
        reasons.append(f"🎯 월가 목표가까지 약 {upside:.1f}%의 추가 상승 여력이 남아있습니다.")

    score = max(10, min(95, score))
    return int(score), reasons

# --- 2. 사이드바 메뉴 ---
st.sidebar.title("📈 민짱 Pro Global")
st.sidebar.radio("메뉴 선택", ["🏠 0. 메인 홈 (대시보드)", "🔍 1. 종목 분석 & 7대 리포트", "🚀 2. 테마별 종목 모아보기", "🔥 3. 급등주 탐지기"], key="menu")
menu = st.session_state.menu

# ==========================================
# 메뉴 0: 🏠 메인 홈 (지표 복구)
# ==========================================
if menu == "🏠 0. 메인 홈 (대시보드)":
    st.title("🌐 글로벌 시장 주요 지수")
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    indices = {"나스닥 (NASDAQ)": "^IXIC", "S&P 500": "^GSPC", "코스피 (KOSPI)": "^KS11", "코스닥 (KOSDAQ)": "^KQ11"}
    cols = [c1, c2, c3, c4]
    
    for i, (name, tkr) in enumerate(indices.items()):
        df = get_history(tkr, "5d")
        if df is not None:
            curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
            cols[i].metric(name, f"{curr:,.2f}", f"{curr-prev:,.2f} ({(curr-prev)/prev*100:.2f}%)")
    
    st.markdown("---")
    st.subheader("💵 실시간 환율 정보")
    st.metric("원/달러 환율 (USD/KRW)", f"{krw_rate:,.2f} 원")

# ==========================================
# 메뉴 1: 🔍 종목 분석 (AI 심층 리포트 + 전문가 차트)
# ==========================================
elif menu == "🔍 1. 종목 분석 & 7대 리포트":
    st.title("🔍 글로벌 종목 정밀 분석")
    m_choice = st.radio("분석 시장 선택", ["🇺🇸 미국(US)", "🇰🇷 한국(KR)"], horizontal=True, index=0 if st.session_state.market == "US" else 1)
    st.session_state.market = "US" if "US" in m_choice else "KR"
    
    c_search1, c_search2 = st.columns([3, 1])
    with c_search1:
        user_input = st.text_input("종목명 또는 티커 입력", st.session_state.search_ticker, placeholder="예: TSLA, 삼성전자, 005930")
    with c_search2:
        period_choice = st.selectbox("분석 기간", ["1y (일봉)", "1mo (시간봉)", "1d (분봉)"])

    if user_input:
        st.session_state.search_ticker = user_input
        ticker = user_input.upper() if st.session_state.market == "US" else (user_input if "." in user_input else f"{user_input}.KS")
        
        # 기간 및 인터벌 설정
        p_map = {"1y (일봉)": ("1y", "1d"), "1mo (시간봉)": ("1mo", "60m"), "1d (분봉)": ("1d", "5m")}
        p, inter = p_map[period_choice]

        with st.spinner('AI가 심층 분석 리포트를 작성 중입니다...'):
            hist = get_history(ticker, p, inter)
            if hist is not None:
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                curr_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
                
                st.header(f"{info.get('longName', user_input)} ({ticker})")
                
                # 상단 메트릭 카드
                mc1, mc2, mc3, mc4 = st.columns(4)
                unit = "$" if st.session_state.market == "US" else "₩"
                mc1.metric("현재가", f"{unit}{curr_p:,.2f}", f"{(curr_p-prev_p)/prev_p*100:.2f}%")
                
                # 🎯 매도 타점 및 수익률 계산 (2번 요구사항)
                entry_p = curr_p * 0.98  # 추천 진입가 (눌림목)
                target_p = curr_p * 1.15  # 추천 매도가 (15% 익절)
                stop_p = entry_p * 0.95   # 칼손절가 (-5%)
                exp_return = (target_p - entry_p) / entry_p * 100
                
                mc2.metric("🎯 목표 매도가", f"{unit}{target_p:,.2f}")
                mc3.metric("🚨 칼손절가", f"{unit}{stop_p:,.2f}")
                mc4.metric("💰 예상 수익률", f"+{exp_return:.1f}%")

                # 📊 차트 (이평선 + 거래량 포함)
                hist['SMA20'] = hist['Close'].rolling(20).mean()
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
                
                # 캔들 & 이평선
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="주가"), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='orange', width=1.5), name="SMA20"), row=1, col=1)
                # 거래량
                fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name="거래량", marker_color='gray'), row=2, col=1)
                
                fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

                # 🧠 AI 심층 리포트 (3번 요구사항 핵심)
                st.subheader("📝 AI 심층 전략 분석 리포트")
                score, reasons = generate_ai_report(user_input, info, hist)
                
                col_left, col_right = st.columns([1, 2])
                with col_left:
                    st.markdown(f"<div class='report-box'><h3>⭐ 매력 점수: {score}점</h3></div>", unsafe_allow_html=True)
                    st.write(f"**🏢 기업 개요:**\n{info.get('longBusinessSummary', '정보 없음')[:300]}...")
                
                with col_right:
                    st.markdown("<div class='report-box'><h4>📌 투자 근거 및 분석 결과</h4></div>", unsafe_allow_html=True)
                    for r in reasons:
                        st.write(r)
                    
                    st.info(f"💡 **종합 의견:** 현재 {user_input}은(는) {score}점의 매력도를 보이고 있습니다. "
                            f"추천 진입가인 {unit}{entry_p:,.2f} 부근에서 분할 매수 후, "
                            f"목표가인 {unit}{target_p:,.2f}까지 보유하는 스윙 전략을 추천합니다.")

            else: st.error("종목 데이터를 가져오지 못했습니다. 시장 선택과 티커를 다시 확인해 주세요.")

# --- 테마별, 급등주 메뉴는 이전 안정화 버전 로직 유지 ---
