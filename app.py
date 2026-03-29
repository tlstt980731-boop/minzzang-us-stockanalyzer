import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# 1. 페이지 기본 설정
st.set_page_config(page_title="미주 분석기 (민짱 Pro)", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #111111; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 26px; color: #3B82F6; }
</style>
""", unsafe_allow_html=True)

st.title("📈 미주 분석기 (민짱 Pro Ver 7.0)")

# --- 2. 나스닥 시장 현황 (항상 위) ---
try:
    ndx = yf.Ticker("^IXIC").history(period="5d")
    if not ndx.empty:
        n_p, n_prev = ndx['Close'].iloc[-1], ndx['Close'].iloc[-2]
        chg, pct = n_p - n_prev, (n_p - n_prev) / n_prev * 100
        trend = "🔴 상승장 (Bull)" if chg > 0 else "🔵 하락장 (Bear)"
        st.markdown(f"**🌐 뉴욕 증시 (NASDAQ):** `{n_p:,.2f}` | 변화: `{chg:,.2f} ({pct:.2f}%)` 👉 **{trend}**")
except:
    pass
st.markdown("---")

# --- 3. 사이드바 메뉴 선택 ---
st.sidebar.header("🕹️ 민짱 전용 메뉴")
menu = st.sidebar.radio(
    "어떤 분석을 할까요?",
    ["🔍 1. 개별 종목 정밀 분석 & 예측", "🚀 2. 테마별 종목 모아보기", "🔥 3. 실시간 급등주 탐지기"]
)

# 한글 검색 사전
ticker_map = {
    "테슬라": "TSLA", "애플": "AAPL", "엔비디아": "NVDA", "ast스페이스모바일": "ASTS", "ast": "ASTS",
    "팔란티어": "PLTR", "엑슨모빌": "XOM", "마이크로소프트": "MSFT", "구글": "GOOGL", "아마존": "AMZN",
    "나스닥3배": "TQQQ", "반도체3배": "SOXL", "엔비디아2배": "NVDL", "테슬라2배": "TSLL"
}

# 보조 지표(RSI) 계산 함수 (설치 없이 pandas로 직접 계산)
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 메뉴 1: 개별 종목 분석 및 차트 예측
# ==========================================
if menu == "🔍 1. 개별 종목 정밀 분석 & 예측":
    st.subheader("🔍 개별 종목 검색 및 AI 차트 예측")
    user_input = st.text_input("종목 코드 또는 한글명 입력 (예: TSLA, AAPL, 테슬라)", "ASTS")
    clean_input = user_input.replace(" ", "").lower()
    ticker_symbol = ticker_map.get(clean_input, user_input.upper())

    if ticker_symbol:
        try:
            with st.spinner(f'{ticker_symbol} 데이터 및 차트 분석 중...'):
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="1y")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change_pct = (current_price - prev_price) / prev_price * 100
                    
                    st.markdown(f"### {ticker_symbol} (현재가: ${current_price:,.2f} / {change_pct:.2f}%)")
                    
                    # 지표 계산
                    hist['SMA20'] = hist['Close'].rolling(20).mean()
                    hist['SMA50'] = hist['Close'].rolling(50).mean()
                    hist['RSI'] = calculate_rsi(hist)
                    current_rsi = hist['RSI'].iloc[-1]
                    sma20 = hist['SMA20'].iloc[-1]
                    
                    # 차트 그리기
                    hist_6m = hist.tail(126)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.8])
                    fig.add_trace(go.Candlestick(x=hist_6m.index, open=hist_6m['Open'], high=hist_6m['High'], low=hist_6m['Low'], close=hist_6m['Close'], name='주가', increasing_line_color='red', decreasing_line_color='blue'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['SMA20'], line=dict(color='orange', width=1.5), name='SMA20'), row=1, col=1)
                    fig.add_trace(go.Bar(x=hist_6m.index, y=hist_6m['Volume'], name='거래량', marker_color='gray'), row=2, col=1)
                    fig.update_layout(height=500, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                    # 🚀 차트 기반 다음 방향 예측 (네가 원한 기능!)
                    st.markdown("### 🤖 민짱 AI의 차트 분석 및 향후 예측")
                    col_p1, col_p2 = st.columns(2)
                    
                    with col_p1:
                        st.write(f"- **현재 RSI (매수/매도 강도):** `{current_rsi:.1f}`")
                        if current_rsi > 70:
                            st.error("🚨 **상태:** [과매수 구간] 사람들이 흥분해서 너무 많이 샀습니다.")
                            pred_text = "단기적으로 가격이 하락(조정)할 확률이 높습니다. 신규 진입은 보류하세요."
                        elif current_rsi < 30:
                            st.success("✨ **상태:** [과매도 구간] 너무 많이 떨어져서 저평가 상태입니다.")
                            pred_text = "단기 반등(상승)이 나올 가능성이 높은 자리입니다. 분할 매수를 고려해볼 만합니다."
                        else:
                            st.info("⚖️ **상태:** [중립 구간] 매수와 매도세가 팽팽합니다.")
                            pred_text = "현재 추세를 따라가며, 갑작스러운 급등/급락보다는 박스권 횡보가 예상됩니다."
                            
                    with col_p2:
                        st.markdown(f"#### 💡 다음 예상 시나리오")
                        st.write(pred_text)
                        if current_price > sma20:
                            st.write("- **추세:** 20일선 위에 있어 단기 상승 추세가 살아있습니다.")
                        else:
                            st.write("- **추세:** 20일선 아래로 깨져서 당분간 하락 압력이 강합니다.")
                            
        except Exception as e:
            st.error(f"데이터를 불러올 수 없습니다. (에러: {e})")

# ==========================================
# 메뉴 2: 테마별 종목 모아보기
# ==========================================
elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 테마별 관련주 주르르륵 보기")
    
    themes = {
        "🛰️ 우주/항공": ["ASTS", "RKLB", "LUNR", "SPCE", "BA", "LMT"],
        "🧠 AI / 반도체": ["NVDA", "AMD", "TSM", "AVGO", "ASML", "PLTR"],
        "⚡ 빅테크 (M7)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
        "🔋 전기차 / 에너지": ["TSLA", "LCID", "RIVN", "XOM", "CVX"]
    }
    
    selected_theme = st.selectbox("어떤 테마를 훑어볼까요?", list(themes.keys()))
    tickers_in_theme = themes[selected_theme]
    
    st.write(f"**{selected_theme}** 관련 종목들을 실시간으로 비교합니다.")
    
    # 여러 종목 한 번에 표로 보여주기
    with st.spinner('테마 종목들 데이터 긁어오는 중...'):
        theme_data = []
        for t in tickers_in_theme:
            try:
                tkr = yf.Ticker(t)
                h = tkr.history(period="2d")
                if len(h) >= 2:
                    p = h['Close'].iloc[-1]
                    chg = (p - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
                    theme_data.append({"종목(Ticker)": t, "현재가($)": round(p, 2), "일일 변동률(%)": round(chg, 2)})
            except:
                pass
                
        if theme_data:
            df = pd.DataFrame(theme_data)
            # 변동률 기준으로 색상 입히기 (스타일링)
            def color_pct(val):
                color = '#ff4b4b' if val > 0 else '#0068c9' if val < 0 else 'white'
                return f'color: {color}'
            
            st.dataframe(df.style.applymap(color_pct, subset=['일일 변동률(%)']), use_container_width=True)
            st.info("💡 위 표의 열 제목을 클릭하면 많이 오른 순서대로 정렬할 수 있습니다.")

# ==========================================
# 메뉴 3: 실시간 급등주 탐지기
# ==========================================
elif menu == "🔥 3. 실시간 급등주 탐지기":
    st.subheader("🔥 실시간 변동성/급등주 탐지기")
    st.write("미국 시장에서 변동성이 크고 핫한 20개 종목을 스캔하여 급등 중인 종목을 찾습니다.")
    
    # 핫한 종목 리스트 (레버리지, 밈주식, 인기주 믹스)
    hot_tickers = ["TSLA", "NVDA", "ASTS", "MSTR", "CVNA", "SMCI", "PLTR", "SOXL", "TQQQ", "LUNR", "RKLB", "COIN", "MARA", "NVDL", "TSLL"]
    
    if st.button("🚀 급등주 스캔 시작하기 (클릭)"):
        with st.spinner('미국 증시 전역을 스캔 중입니다... (약 5초 소요)'):
            scan_results = []
            for t in hot_tickers:
                try:
                    tkr = yf.Ticker(t)
                    h = tkr.history(period="1mo")
                    if len(h) > 20:
                        p = h['Close'].iloc[-1]
                        chg_pct = (p - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
                        rsi = calculate_rsi(h).iloc[-1]
                        scan_results.append({"ticker": t, "price": p, "chg": chg_pct, "rsi": rsi})
                except:
                    continue
            
            if scan_results:
                # 변동률 높은 순으로 정렬
                scan_results = sorted(scan_results, key=lambda x: x['chg'], reverse=True)
                top_gainers = scan_results[:3] # 탑 3만 뽑기
                
                st.success("✅ 스캔 완료! 현재 가장 많이 급등 중인 TOP 3 종목입니다.")
                
                for i, stock in enumerate(top_gainers):
                    st.markdown(f"### 🥇 {i+1}위: {stock['ticker']} (+{stock['chg']:.2f}%)")
                    col1, col2 = st.columns(2)
                    col1.metric("현재가", f"${stock['price']:,.2f}")
                    
                    # 🚀 진입 타당성 분석 (네가 원한 기능!)
                    with col2:
                        st.markdown("**🛡️ 민짱의 진입 타당성 판독기**")
                        if stock['rsi'] > 75:
                            st.error(f"❌ **지금 타면 물립니다!** (RSI: {stock['rsi']:.1f})\n너무 급하게 올랐습니다. 조정(하락)이 올 때까지 기다리세요.")
                        elif stock['rsi'] > 60:
                            st.warning(f"⚠️ **단타만 가능!** (RSI: {stock['rsi']:.1f})\n추세는 좋지만 이미 꽤 올랐습니다. 짧게 먹고 나오는 전략만 유효합니다.")
                        else:
                            st.success(f"✅ **진입해볼 만합니다!** (RSI: {stock['rsi']:.1f})\n아직 과열되지 않은 상태에서 오르고 있습니다.")
                    st.markdown("---")
