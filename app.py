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

st.title("📈 미주 분석기 (민짱 Pro Ver 8.0)")

# --- 2. 나스닥 시장 현황 ---
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

# --- 3. 사이드바 메뉴 ---
st.sidebar.header("🕹️ 민짱 전용 메뉴")
menu = st.sidebar.radio(
    "어떤 분석을 할까요?",
    ["🔍 1. 개별 종목 분석 & AI 예측", "🚀 2. 테마별 종목 모아보기", "🔥 3. 실시간 급등주 탐지기"]
)

ticker_map = {
    "테슬라": "TSLA", "애플": "AAPL", "엔비디아": "NVDA", "ast스페이스모바일": "ASTS", "ast": "ASTS",
    "팔란티어": "PLTR", "엑슨모빌": "XOM", "마이크로소프트": "MSFT", "구글": "GOOGL", "아마존": "AMZN",
    "나스닥3배": "TQQQ", "반도체3배": "SOXL", "엔비디아2배": "NVDL", "테슬라2배": "TSLL"
}

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 메뉴 1: 개별 종목 분석 (사라진 탭들 완벽 복구!)
# ==========================================
if menu == "🔍 1. 개별 종목 분석 & AI 예측":
    user_input = st.text_input("🔍 종목 코드 또는 한글명 입력 (예: TSLA, AAPL)", "ASTS")
    clean_input = user_input.replace(" ", "").lower()
    ticker_symbol = ticker_map.get(clean_input, user_input.upper())

    if ticker_symbol:
        try:
            with st.spinner(f'{ticker_symbol} 데이터 영혼까지 끌어오는 중...'):
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="1y")
                info = ticker.info
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    
                    stock_name = info.get('longName', info.get('shortName', ticker_symbol))
                    st.markdown(f"### {stock_name} ({ticker_symbol})")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("현재가", f"${current_price:,.2f}", f"{change:,.2f} ({change_pct:.2f}%)")
                    
                    target = info.get('targetMeanPrice', 'N/A')
                    if target != 'N/A':
                        c2.metric("월가 목표가", f"${target:,.2f}", f"{(target - current_price)/current_price*100:,.2f}%")
                    else:
                        c2.metric("52주 고가", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
                    
                    c3.metric("거래량", f"{hist['Volume'].iloc[-1]:,}")
                    c4.metric("시가총액", f"${info.get('marketCap', info.get('totalAssets', 0)):,.0f}")

                    # 차트 및 지표
                    hist['SMA20'] = hist['Close'].rolling(20).mean()
                    hist['RSI'] = calculate_rsi(hist)
                    
                    hist_6m = hist.tail(126)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.8])
                    fig.add_trace(go.Candlestick(x=hist_6m.index, open=hist_6m['Open'], high=hist_6m['High'], low=hist_6m['Low'], close=hist_6m['Close'], name='주가', increasing_line_color='red', decreasing_line_color='blue'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['SMA20'], line=dict(color='orange', width=1.5), name='SMA20'), row=1, col=1)
                    fig.add_trace(go.Bar(x=hist_6m.index, y=hist_6m['Volume'], name='거래량', marker_color='gray'), row=2, col=1)
                    fig.update_layout(height=500, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                    # --- 🚀 복구된 탭 + 5일 수익률 AI 탭 ---
                    t1, t2, t3, t4 = st.tabs(["🤖 AI 예측 & 5일 수익률", "⚡ 단기 스윙", "🌳 장기 가치 투자", "🏢 기업 정보"])
                    
                    with t1: # (NEW) 5일 후 수익률 예측!
                        current_rsi = hist['RSI'].iloc[-1]
                        sma20 = hist['SMA20'].iloc[-1]
                        past_5d_return = (current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100 if len(hist)>5 else 0
                        
                        # 간단 퀀트 모델 로직
                        if current_rsi < 40:
                            expected_5d = abs(past_5d_return) * 0.4 + 2.5 # 과매도 반등
                            pred_text = "단기 반등이 강하게 나올 수 있는 저평가 구간입니다."
                        elif current_rsi > 70:
                            expected_5d = -abs(past_5d_return) * 0.4 - 2.0 # 과매수 조정
                            pred_text = "너무 많이 올랐습니다. 곧 차익 실현(하락 조정) 물량이 쏟아질 수 있습니다."
                        else:
                            expected_5d = past_5d_return * 0.3 # 추세 유지
                            pred_text = "현재 추세를 유지하며 박스권에서 움직일 확률이 높습니다."
                        
                        col_ai1, col_ai2 = st.columns(2)
                        with col_ai1:
                            st.markdown(f"#### 🔮 5일 후 예상 수익률")
                            sign = "+" if expected_5d > 0 else ""
                            color = "red" if expected_5d > 0 else "blue"
                            st.markdown(f"<h2 style='color:{color};'>{sign}{expected_5d:.2f}%</h2>", unsafe_allow_html=True)
                            st.write("*과거 모멘텀과 RSI 지표를 결합한 퀀트 통계적 예측치입니다.*")
                        with col_ai2:
                            st.markdown("#### 💡 AI 차트 브리핑")
                            st.write(f"- **현재 RSI:** `{current_rsi:.1f}`")
                            st.write(f"- **방향성:** {pred_text}")

                    with t2: # 복구: 단기 스윙
                        support = hist['Close'].tail(20).min()
                        resist = hist['Close'].tail(20).max()
                        st.success(f"🎯 **추천 진입가:** **${support:,.2f}** 부근 (최근 20일 지지선)")
                        st.error(f"🚨 **칼손절 라인:** **${support*0.95:,.2f}** (진입가 5% 이탈 시)")
                        st.write(f"⚠️ 공매도 비율(Short Ratio): **{info.get('shortRatio', '데이터 없음')}**")

                    with t3: # 복구: 장기 가치
                        st.info(f"📈 월가 애널리스트 투자의견: **{info.get('recommendationKey', '데이터 없음').upper()}**")
                        st.write(f"- 현재 P/E: **{info.get('trailingPE', 'N/A')}**")
                        st.write(f"- 1년 뒤 예상 P/E: **{info.get('forwardPE', 'N/A')}**")

                    with t4: # 복구: 기업 정보
                        st.write(f"- **섹터/산업:** {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}")
                        div = info.get('dividendYield', 'N/A')
                        st.write(f"- **배당 수익률:** `{div * 100:.2f}%` 💰" if div != 'N/A' and div is not None else "- **배당 수익률:** 없음")
                        st.write(f"- **베타(Beta) 변동성:** `{info.get('beta', 'N/A')}`")
                            
        except Exception as e:
            st.error(f"데이터를 불러올 수 없습니다.")

# ==========================================
# 메뉴 2: 테마별 종목 모아보기 (그대로 유지!)
# ==========================================
elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 테마별 관련주 주르르륵 보기")
    themes = {
        "🛰️ 우주/항공": ["ASTS", "RKLB", "LUNR", "SPCE", "BA"],
        "🧠 AI / 반도체": ["NVDA", "AMD", "TSM", "AVGO", "PLTR"],
        "⚡ 빅테크 (M7)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]
    }
    selected_theme = st.selectbox("어떤 테마를 훑어볼까요?", list(themes.keys()))
    tickers_in_theme = themes[selected_theme]
    
    with st.spinner('테마 종목들 스캔 중...'):
        theme_data = []
        for t in tickers_in_theme:
            try:
                tkr = yf.Ticker(t)
                h = tkr.history(period="2d")
                if len(h) >= 2:
                    p = h['Close'].iloc[-1]
                    chg = (p - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
                    theme_data.append({"종목(Ticker)": t, "현재가($)": round(p, 2), "일일 변동률(%)": round(chg, 2)})
            except: pass
                
        if theme_data:
            df = pd.DataFrame(theme_data)
            def color_pct(val):
                return f"color: {'#ff4b4b' if val > 0 else '#0068c9' if val < 0 else 'white'}"
            st.dataframe(df.style.applymap(color_pct, subset=['일일 변동률(%)']), use_container_width=True)

# ==========================================
# 메뉴 3: 실시간 급등주 탐지기 (그대로 유지!)
# ==========================================
elif menu == "🔥 3. 실시간 급등주 탐지기":
    st.subheader("🔥 실시간 급등주 스캐너")
    hot_tickers = ["TSLA", "NVDA", "ASTS", "MSTR", "PLTR", "SOXL", "TQQQ", "LUNR", "RKLB"]
    
    if st.button("🚀 급등주 스캔 시작하기 (클릭)"):
        with st.spinner('스캔 중...'):
            scan_results = []
            for t in hot_tickers:
                try:
                    tkr = yf.Ticker(t)
                    h = tkr.history(period="1mo")
                    if len(h) > 20:
                        p, p_prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                        chg_pct = (p - p_prev) / p_prev * 100
                        rsi = calculate_rsi(h).iloc[-1]
                        scan_results.append({"ticker": t, "price": p, "chg": chg_pct, "rsi": rsi})
                except: pass
            
            if scan_results:
                top_gainers = sorted(scan_results, key=lambda x: x['chg'], reverse=True)[:3]
                st.success("✅ 스캔 완료! TOP 3 종목입니다.")
                for i, stock in enumerate(top_gainers):
                    st.markdown(f"### 🥇 {i+1}위: {stock['ticker']} (+{stock['chg']:.2f}%)")
                    col1, col2 = st.columns(2)
                    col1.metric("현재가", f"${stock['price']:,.2f}")
                    with col2:
                        if stock['rsi'] > 75: st.error(f"❌ 진입 금지! 곧 떨어집니다. (RSI: {stock['rsi']:.1f})")
                        elif stock['rsi'] > 60: st.warning(f"⚠️ 단타만 가능! 꽤 올랐습니다. (RSI: {stock['rsi']:.1f})")
                        else: st.success(f"✅ 진입해볼 만합니다! (RSI: {stock['rsi']:.1f})")
                    st.markdown("---")
