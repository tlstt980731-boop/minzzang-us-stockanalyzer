import streamlit as st
import yfinance as yf
from datetime import datetime
import pytz

# 제목
st.title("🇺🇸 미주 분석기 (민짱 Ver.)")

# 시간 표시
korea_tz = pytz.timezone('Asia/Seoul')
us_tz = pytz.timezone('America/New_York')

korea_time = datetime.now(korea_tz).strftime('%Y-%m-%d %H:%M:%S')
us_time = datetime.now(us_tz).strftime('%Y-%m-%d %H:%M:%S')

col1, col2 = st.columns(2)
with col1:
    st.metric("🇰🇷 한국 시간", korea_time)
with col2:
    st.metric("🇺🇸 미국 시간 (EST)", us_time)

# 종목 검색
ticker = st.text_input("분석할 티커를 입력하세요", "ASTS")

if ticker:
    data = yf.Ticker(ticker)
    info = data.info
    current_price = info.get('currentPrice', '데이터 없음')
    st.header(f"현재가: ${current_price}")