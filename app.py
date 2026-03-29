import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# 1. 페이지 기본 설정
st.set_page_config(page_title="미주 분석기 (민짱 Ver.)", layout="wide")

# 15. 실시간 시간/분/초 표시 (새로고침 시점 기준)
utc_now = datetime.utcnow()
kr_time = (utc_now + timedelta(hours=9)).strftime('%Y-%m-%d %H시 %M분 %S초')
ny_time = (utc_now - timedelta(hours=4)).strftime('%Y-%m-%d %H시 %M분 %S초')

st.title("📈 미주 분석기 (민짱 Ver 2.0)")

# 사이드바
st.sidebar.header("⏱️ 현재 시간 (새로고침 기준)")
st.sidebar.write(f"🇰🇷 한국: {kr_time}")
st.sidebar.write(f"🇺🇸 미국: {ny_time}")

# 8. 환율 변동선 (간단히 표시)
try:
    krw_data = yf.Ticker("USDKRW=X").history(period="5d")
    if not krw_data.empty:
        krw_price = krw_data['Close'].iloc[-1]
        krw_prev = krw_data['Close'].iloc[-2]
        st.sidebar.metric(label="원/달러 환율", value=f"{krw_price:,.2f} 원", delta=f"{krw_price - krw_prev:,.2f} 원")
except:
    pass

st.sidebar.markdown("---")
st.sidebar.header("🚀 관심 테마 퀵버튼")
quick_search = st.sidebar.radio(
    "테마를 선택하세요:",
    ["직접 검색", "우주/항공 (ASTS)", "AI/반도체 (NVDA)", "로봇 (PLTR)", "에너지 (XOM)"]
)

ticker_map = {
    "테슬라": "TSLA", "애플": "AAPL", "엔비디아": "NVDA", 
    "ast스페이스모바일": "ASTS", "ast스페이스": "ASTS", "ast": "ASTS",
    "팔란티어": "PLTR", "엑슨모빌": "XOM", "마이크로소프트": "MSFT"
}

# 5. 종목 검색
if quick_search == "직접 검색":
    user_input = st.text_input("🔍 종목 코드 또는 기업명 (예: TSLA, 테슬라)", "ASTS")
    clean_input = user_input.replace(" ", "").lower()
    ticker_symbol = ticker_map.get(clean_input, user_input.upper())
else:
    ticker_symbol = quick_search.split("(")[1].replace(")", "")

if ticker_symbol:
    try:
        with st.spinner(f'{ticker_symbol} 데이터 영혼까지 끌어오는 중...'):
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            hist = ticker.history(period="6mo")

            if hist.empty:
                st.error("데이터를 찾을 수 없습니다.")
            else:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                
                # 상단 헤더
                st.markdown(f"### {info.get('shortName', ticker_symbol)} ({ticker_symbol})")
                st.metric("현재 주가", f"${current_price:,.2f}", f"{(current_price - prev_close):,.2f} ({(current_price - prev_close) / prev_close * 100:.2f}%)")
                
                # 차트
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index, open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    increasing_line_color='red', decreasing_line_color='blue'
                )])
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # 9. 단기 스윙 / 장기 가치 투자 탭 나누기
                tab1, tab2 = st.tabs(["⚡ 단기 스윙 관점", "🌳 장기 가치 투자 관점"])
                
                with tab1:
                    # 11. 진입가/손절가 계산
                    hist['Max_20'] = hist['Close'].rolling(window=20).max()
                    hist['Min_20'] = hist['Close'].rolling(window=20).min()
                    support = hist['Min_20'].iloc[-1]
                    resist = hist['Max_20'].iloc[-1]
                    
                    # 13. 신뢰도 흉내내기 (변동성 기반)
                    volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
                    confidence = max(40, 95 - (volatility / 2)) # 변동성이 적을수록 신뢰도 높음
                    
                    col1, col2 = st.columns(2)
                    col1.success(f"🎯 **단기 매매 전략**\n* 추천 진입가: **${support:,.2f}** (최근 바닥)\n* 목표가: **${resist:,.2f}**\n* 🚨 **칼손절가: ${(support*0.95):,.2f}**")
                    col2.info(f"🤖 **알고리즘 매매 신호**\n* 현재 포지션: **{'대기(관망)' if current_price > (support+resist)/2 else '분할매수'}**\n* 지표 신뢰도: **{confidence:.1f}%**")
                    
                    # 2. 숏 스퀴즈
                    short_ratio = info.get('shortRatio', 0)
                    if short_ratio and short_ratio > 4:
                        st.warning(f"🔥 **숏 스퀴즈 주의:** 공매도 비율({short_ratio})이 높습니다. 급등락 가능성 존재!")

                with tab2:
                    # 4. 구매/판매/대기 (월가 의견 데이터 활용)
                    rec = info.get('recommendationKey', 'N/A').upper()
                    if rec == 'BUY' or rec == 'STRONG_BUY':
                        rec_kr = "적극 매수 (Buy)"
                    elif rec == 'HOLD':
                        rec_kr = "보유/대기 (Hold)"
                    else:
                        rec_kr = "매도 (Sell) 또는 데이터 없음"

                    # 7. 상대적 밸류에이션
                    pe = info.get('trailingPE', 'N/A')
                    forward_pe = info.get('forwardPE', 'N/A')
                    sector = info.get('sector', 'N/A')

                    col3, col4 = st.columns(2)
                    col3.write(f"**섹터 (카테고리):** {sector}")
                    col3.write(f"**현재 P/E:** {pe} / **1년 뒤 예상 P/E:** {forward_pe}")
                    col4.success(f"📈 **월가 애널리스트 종합 의견:**\n### {rec_kr}")

    except Exception as e:
        st.error(f"데이터를 불러오는 중 문제가 발생했습니다.")
