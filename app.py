import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 기본 설정 (가장 위에 있어야 함)
st.set_page_config(page_title="미주 분석기 (민짱 Ver.)", layout="wide")

# 2. 실시간 시간 계산 (UTC 기준)
utc_now = datetime.utcnow()
kr_time = (utc_now + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
ny_time = (utc_now - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M') 

st.title("📈 미주 분석기 (민짱 Ver.)")

# 3. 사이드바 (시간, 환율, 테마 검색)
st.sidebar.header("⏱️ 현재 시간 & 💵 환율")
st.sidebar.write(f"🇰🇷 한국: {kr_time}")
st.sidebar.write(f"🇺🇸 미국: {ny_time}")

try:
    krw_data = yf.Ticker("USDKRW=X").history(period="1d")
    if not krw_data.empty:
        krw_price = krw_data['Close'].iloc[-1]
        st.sidebar.metric(label="원/달러 환율", value=f"{krw_price:,.2f} 원")
except:
    st.sidebar.write("환율 정보를 불러올 수 없습니다.")

st.sidebar.markdown("---")
st.sidebar.header("🚀 관심 테마 빠른 검색")
quick_search = st.sidebar.radio(
    "테마를 선택하면 자동으로 분석을 시작합니다.",
    ["직접 검색", "우주/항공 (ASTS)", "AI/반도체 (NVDA)", "로봇 (PLTR)", "에너지 (XOM)"]
)

# 💡 한글 -> 영문 티커 변환 사전
ticker_map = {
    "테슬라": "TSLA",
    "애플": "AAPL",
    "엔비디아": "NVDA",
    "ast스페이스모바일": "ASTS",
    "ast스페이스": "ASTS",
    "팔란티어": "PLTR",
    "엑슨모빌": "XOM",
    "마이크로소프트": "MSFT",
    "마소": "MSFT",
    "구글": "GOOGL",
    "아마존": "AMZN",
    "메타": "META",
    "아이온큐": "IONQ"
}

# 4. 종목 검색기
if quick_search == "직접 검색":
    user_input = st.text_input("🔍 종목 코드 또는 기업명 입력 (예: TSLA, 테슬라, ast스페이스모바일)", "ASTS")
    
    # 입력값 정리 (띄어쓰기 제거 및 소문자 변환)
    clean_input = user_input.replace(" ", "").lower()
    
    # 사전에 한글 이름이 있으면 영문 티커로 변환, 없으면 입력값 그대로 대문자로 사용
    ticker_symbol = ticker_map.get(clean_input, user_input.upper())
    
    if clean_input in ticker_map:
        st.success(f"✅ '{user_input}'을(를) 인식하여 **{ticker_symbol}** 종목을 분석합니다.")

else:
    # 괄호 안의 티커만 쏙 빼오기
    ticker_symbol = quick_search.split("(")[1].replace(")", "")
    st.info(f"💡 '{quick_search.split(' ')[0]}' 테마의 대표 종목 **{ticker_symbol}**을(를) 분석합니다.")

# 5. 본격적인 데이터 분석 시작
if ticker_symbol:
    try:
        with st.spinner(f'{ticker_symbol} 실시간 데이터 불러오는 중...'):
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            hist = ticker.history(period="6mo")

            if hist.empty:
                st.error("데이터를 찾을 수 없습니다. 종목 코드나 이름이 정확한지 확인해 주세요.")
            else:
                # 상단 현재가 요약
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100

                col1, col2, col3 = st.columns(3)
                col1.metric("현재 주가", f"${current_price:,.2f}", f"{change:,.2f} ({change_pct:.2f}%)")
                
                # 차트 그리기 (상승 빨강, 하락 파랑)
                st.subheader("📊 최근 6개월 차트")
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index, open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    increasing_line_color='red', decreasing_line_color='blue'
                )])
                fig.update_layout(height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # 진입/손절가 계산 (최근 20일 기준)
                hist['Max_20'] = hist['Close'].rolling(window=20).max()
                hist['Min_20'] = hist['Close'].rolling(window=20).min()
                support = hist['Min_20'].iloc[-1]
                resist = hist['Max_20'].iloc[-1]

                # 매매 전략 및 지표 화면 표시
                st.subheader("💡 민짱 맞춤형 AI 매매 전략")
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.success(f"🎯 **단기 스윙 전략**\n\n* 추천 진입가: **${support:,.2f}** 부근 (최근 20일 최저점)\n* 단기 목표가: **${resist:,.2f}**\n* 🚨 **칼손절 라인: ${(support*0.95):,.2f}** (진입가 이탈 시)")
                with col_s2:
                    pe = info.get('trailingPE', 'N/A')
                    st.info(f"📈 **장기 가치 투자**\n\n* 현재 P/E (주가수익비율): **{pe}**\n* 섹터: **{info.get('sector', 'N/A')}**\n* AI 분석: 장기 투자 시 회사의 펀더멘털과 다가오는 일정을 꼭 체크하세요.")

                # 공매도 지표
                st.subheader("⚠️ 공매도 잔고 및 숏 스퀴즈 지표")
                short_ratio = info.get('shortRatio', '데이터 없음')
                short_float = info.get('shortPercentOfFloat', 0)
                if short_float != 0:
                    short_float = f"{short_float * 100:.2f}%"
                else:
                    short_float = "데이터 없음"
                
                st.write(f"**공매도 비율 (Short Ratio):** {short_ratio} | **유동주식 대비 공매도:** {short_float}")
                
                if type(short_ratio) == float and short_ratio > 4:
                    st.warning("🔥 **숏 스퀴즈(Short Squeeze) 경보:** 공매도 비율이 꽤 높습니다. 갑작스러운 호재 발생 시 주가가 폭등할 가능성이 있습니다!")
                else:
                    st.write("안정적인 공매도 수준을 유지하고 있습니다.")

    except Exception as e:
        st.error(f"데이터를 분석하는 중 오류가 발생했습니다. (에러: {e})")
