import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# 1. 페이지 기본 설정 (와이드 모드, 다크 테마)
st.set_page_config(page_title="미주 분석기 (민짱 Pro)", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .stApp { background-color: #111111; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #3B82F6; font-weight: bold; }
    [data-testid="stMetricDelta"] { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# 공통 함수: RSI 계산
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 공통 함수: 5일 수익률 AI 예측
def predict_5d_return(current_price, hist, current_rsi):
    past_5d = (current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100 if len(hist)>5 else 0
    if current_rsi < 40: return abs(past_5d) * 0.4 + 2.5
    elif current_rsi > 70: return -abs(past_5d) * 0.4 - 2.0
    else: return past_5d * 0.3

# 한글 검색 사전 (만능)
ticker_map = {
    "테슬라": "TSLA", "애플": "AAPL", "엔비디아": "NVDA", "ast스페이스모바일": "ASTS", "ast": "ASTS",
    "팔란티어": "PLTR", "엑슨모빌": "XOM", "마이크로소프트": "MSFT", "마소": "MSFT", "구글": "GOOGL",
    "아마존": "AMZN", "메타": "META", "나스닥3배": "TQQQ", "반도체3배": "SOXL", "엔비디아2배": "NVDL",
    "테슬라2배": "TSLL", "나스닥2배": "QLD", "비트코인2배": "BITU", "코인베이스": "COIN"
}

# --- 2. 사이드바 메뉴 ---
st.sidebar.title("📈 민짱 Pro")
utc_now = datetime.utcnow()
st.sidebar.markdown(f"⏱️ **한국 기준:** {(utc_now + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')}")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "메뉴를 선택하세요:",
    [
        "🏠 0. 메인 홈 (대시보드)", 
        "🔍 1. 종목 분석 & 7대 리포트", 
        "🚀 2. 테마별 종목 모아보기", 
        "🔥 3. 급등주 탐지기",
        "🏆 4. AI 5일 수익률 랭킹"
    ]
)

# ==========================================
# 메뉴 0: 🏠 메인 홈 (대시보드) - 네가 원하던 바로 그 첫 화면!
# ==========================================
if menu == "🏠 0. 메인 홈 (대시보드)":
    st.title("환영합니다! 📈 미주 분석기 (민짱 Pro Ver 11.0)")
    st.markdown("여의도/월스트리트 전문가 수준의 심층 데이터와 AI 예측을 무료로 경험해 보세요.")
    st.markdown("---")
    
    st.subheader("🌐 오늘의 거시 경제 (Macro) 현황")
    with st.spinner('실시간 시장 데이터를 불러오는 중...'):
        c_m1, c_m2, c_m3 = st.columns(3)
        try:
            # 나스닥
            ndx = yf.Ticker("^IXIC").history(period="2d")
            n_p, n_prev = ndx['Close'].iloc[-1], ndx['Close'].iloc[-2]
            c_m1.metric("NASDAQ (나스닥 종합)", f"{n_p:,.2f}", f"{n_p - n_prev:,.2f} ({(n_p - n_prev)/n_prev*100:.2f}%)")
            
            # S&P 500
            spx = yf.Ticker("^GSPC").history(period="2d")
            s_p, s_prev = spx['Close'].iloc[-1], spx['Close'].iloc[-2]
            c_m2.metric("S&P 500", f"{s_p:,.2f}", f"{s_p - s_prev:,.2f} ({(s_p - s_prev)/s_prev*100:.2f}%)")
            
            # 원/달러 환율 (네가 원했던 거 복구!)
            krw = yf.Ticker("USDKRW=X").history(period="2d")
            k_p, k_prev = krw['Close'].iloc[-1], krw['Close'].iloc[-2]
            c_m3.metric("원/달러 환율 (KRW/USD)", f"{k_p:,.2f} 원", f"{k_p - k_prev:,.2f} 원")
        except:
            st.error("시장 데이터를 불러오는 데 실패했습니다.")

    st.markdown("---")
    st.subheader("💡 100% 활용 가이드")
    st.info("""
    👈 **왼쪽 사이드바 메뉴 설명**
    - **🔍 1. 종목 분석:** 궁금한 종목(한글/영어)을 치면 차트, 목표가, 7대 심층 매트릭스 리포트를 제공합니다.
    - **🚀 2. 테마별 모아보기:** 우주/항공, AI 등 특정 테마에 묶인 주식들의 실시간 흐름을 비교합니다.
    - **🔥 3. 급등주 탐지기:** 지금 미국 장에서 가장 핫하게 미쳐 날뛰는 종목과 진입 타당성을 알려줍니다.
    - **🏆 4. AI 5일 수익률 랭킹:** 주요 종목 20개를 스캔해 향후 5일간 오를 종목과 내릴 종목을 점쳐줍니다.
    """)

# ==========================================
# 메뉴 1: 개별 종목 분석 & 7대 매트릭스 리포트
# ==========================================
elif menu == "🔍 1. 종목 분석 & 7대 리포트":
    st.title("🔍 개별 종목 정밀 분석")
    # 기본값을 없애서 처음에 아무것도 안 뜨게 만듦!
    user_input = st.text_input("종목 코드 또는 한글명 입력 (예: TSLA, AAPL, 테슬라2배)", "")
    
    if user_input == "":
        st.info("👆 위에 궁금한 미국 주식 티커나 한글 이름을 입력하고 Enter를 누르세요!")
    else:
        clean_input = user_input.replace(" ", "").lower()
        ticker_symbol = ticker_map.get(clean_input, user_input.upper())

        try:
            with st.spinner(f'{ticker_symbol} 데이터 영혼까지 끌어오는 중...'):
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="1y")
                info = ticker.info
                
                if hist.empty:
                    st.warning(f"'{user_input}'(으)로 검색된 데이터가 없습니다. 영어 티커를 확인해 보세요.")
                else:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    
                    stock_name = info.get('longName', info.get('shortName', ticker_symbol))
                    st.markdown(f"### {stock_name} ({ticker_symbol})")
                    
                    # 숏 스퀴즈 경보 복구 (12번 요구사항)
                    short_ratio = info.get('shortRatio', 0)
                    if type(short_ratio) in [float, int] and short_ratio > 4.0:
                        st.error(f"🚨 **숏 스퀴즈 경보 발령:** 공매도 비율({short_ratio})이 매우 높습니다. 급등락 주의!")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("현재가", f"${current_price:,.2f}", f"{change:,.2f} ({change_pct:.2f}%)")
                    
                    target = info.get('targetMeanPrice', 'N/A')
                    if target != 'N/A':
                        c2.metric("월가 목표가", f"${target:,.2f}", f"{(target - current_price)/current_price*100:,.2f}% (기대수익)")
                    else:
                        target = current_price * 1.1 # 기본값
                        c2.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
                    
                    c3.metric("거래량", f"{hist['Volume'].iloc[-1]:,}")
                    c4.metric("시가총액", f"${info.get('marketCap', info.get('totalAssets', 0)):,.0f}")

                    hist['SMA20'] = hist['Close'].rolling(20).mean()
                    hist['RSI'] = calculate_rsi(hist)
                    current_rsi = hist['RSI'].iloc[-1]
                    
                    # 🎯 투자 매력도 산출 로직
                    charm_score = 50
                    rec = info.get('recommendationKey', 'hold').lower()
                    if rec in ['buy', 'strong_buy']: charm_score += 20
                    elif rec in ['sell', 'underperform']: charm_score -= 20
                    if current_rsi < 35: charm_score += 15
                    elif current_rsi > 70: charm_score -= 15
                    if target != 'N/A' and target > current_price: charm_score += 10
                    charm_score = max(0, min(100, charm_score))
                    
                    # 차트
                    hist_6m = hist.tail(126)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.8])
                    fig.add_trace(go.Candlestick(x=hist_6m.index, open=hist_6m['Open'], high=hist_6m['High'], low=hist_6m['Low'], close=hist_6m['Close'], name='주가', increasing_line_color='red', decreasing_line_color='blue'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['SMA20'], line=dict(color='orange', width=1.5), name='SMA20'), row=1, col=1)
                    fig.add_trace(go.Bar(x=hist_6m.index, y=hist_6m['Volume'], name='거래량', marker_color='gray'), row=2, col=1)
                    fig.update_layout(height=450, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                    # 탭 분석
                    t1, t2, t3 = st.tabs(["📝 7대 매트릭스 심층 리포트", "🤖 AI 단기/스윙 예측", "🏢 펀더멘털 (가치)"])
                    
                    with t1:
                        st.markdown(f"## 🎯 **투자 매력도: {int(charm_score)} 점** / 100점")
                        st.progress(int(charm_score))
                        
                        support = hist['Close'].tail(20).min()
                        resist = hist['Close'].tail(20).max()
                        beta = info.get('beta', 1.0)
                        
                        st.markdown(f"""
                        ### 1. Executive Summary (핵심 요약)
                        - **현재 위치**: 월가 애널리스트 투자의견 **{rec.upper()}**. RSI 지표상 {current_rsi:.1f}로 매수/매도 압력 주시.

                        ### 2. Business & Moat (비즈니스 및 해자)
                        - P/E 비율이 **{info.get('trailingPE', 'N/A')}**이며 섹터 내 모멘텀에 따라 주가 연동성이 큼.

                        ### 3. Financials & Macro (재무 및 거시환경)
                        - **거시 연동성**: 베타(Beta)가 **{beta}**로, 시장 변동에 대한 민감도를 나타냄.
                        - **수급 리스크**: 공매도 비율(Short Ratio) **{info.get('shortRatio', 'N/A')}**.

                        ### 4. Management & Psychology (시장 심리)
                        - **기술적 심리**: 현재 RSI {current_rsi:.1f} (70 이상 과열, 30 이하 공포).

                        ### 5. The 3-Scenario Analysis (3대 시나리오)
                        - **🟢 Bull Case (강세)**: 저항선 **${resist:,.2f}** 돌파 시 단기 급등.
                        - **🟡 Base Case (기본)**: 현재가 **${current_price:,.2f}** 부근에서 이동평균선 지지 테스트.
                        - **🔴 Bear Case (약세)**: 지지선 **${support:,.2f}** 붕괴 시 투매 가능성.

                        ### 6. Risk Map (치명적 리스크)
                        - 시장 유동성 변화 및 섹터 내 대형 악재 발생 시 변동폭 극대화.

                        ### 7. Final Decision Framework (매매 가이드)
                        - **종합 투자 의견**: **{'BUY (매수)' if charm_score >= 65 else 'HOLD (관망/대기)' if charm_score >= 40 else 'SELL (매도/주의)'}**
                        - **진입가 (타점)**: **${support:,.2f}** (강력 지지선)
                        - **목표 익절가**: **${resist:,.2f}**
                        - **손절가 (Kill Switch)**: **${support*0.95:,.2f}** (-5% 이탈 시)
                        """)

                    with t2:
                        expected_5d = predict_5d_return(current_price, hist, current_rsi)
                        st.markdown(f"#### 🔮 5일 후 예상 수익률: <span style='color:{'red' if expected_5d > 0 else 'blue'};'>**{expected_5d:+.2f}%**</span>", unsafe_allow_html=True)
                        st.write(f"- **현재 RSI:** `{current_rsi:.1f}`")
                        st.success(f"🎯 **단기 스윙 진입가:** **${support:,.2f}**")
                        
                    with t3:
                        st.write(f"- **섹터/산업:** {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}")
                        div = info.get('dividendYield', 'N/A')
                        st.write(f"- **배당 수익률:** `{div * 100:.2f}%` 💰" if div != 'N/A' and div is not None else "- 배당 없음")

        except Exception as e:
            st.error(f"데이터를 불러올 수 없습니다.")

# ==========================================
# (메뉴 2, 3, 4 유지)
# ==========================================
elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 테마별 관련주 비교하기")
    themes = {"🛰️ 우주/항공": ["ASTS", "RKLB", "LUNR", "SPCE"], "🧠 AI / 반도체": ["NVDA", "AMD", "TSM", "PLTR"], "⚡ 빅테크 (M7)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]}
    selected_theme = st.selectbox("테마 선택:", list(themes.keys()))
    with st.spinner('스캔 중...'):
        data = []
        for t in themes[selected_theme]:
            try:
                h = yf.Ticker(t).history(period="2d")
                if len(h)>1: data.append({"종목": t, "현재가($)": round(h['Close'].iloc[-1], 2), "변동률(%)": round((h['Close'].iloc[-1]-h['Close'].iloc[-2])/h['Close'].iloc[-2]*100, 2)})
            except: pass
        if data:
            st.dataframe(pd.DataFrame(data).style.applymap(lambda x: f"color: {'#ff4b4b' if x>0 else '#0068c9'}", subset=['변동률(%)']), use_container_width=True)

elif menu == "🔥 3. 급등주 탐지기":
    st.subheader("🔥 실시간 급등주 스캐너")
    if st.button("🚀 급등주 스캔 시작"):
        with st.spinner('스캔 중...'):
            res = []
            for t in ["TSLA", "NVDA", "ASTS", "MSTR", "PLTR", "SOXL", "TQQQ"]:
                try:
                    h = yf.Ticker(t).history(period="1mo")
                    if len(h)>20: res.append({"t": t, "p": h['Close'].iloc[-1], "chg": (h['Close'].iloc[-1]-h['Close'].iloc[-2])/h['Close'].iloc[-2]*100, "rsi": calculate_rsi(h).iloc[-1]})
                except: pass
            if res:
                for i, s in enumerate(sorted(res, key=lambda x: x['chg'], reverse=True)[:3]):
                    st.markdown(f"### 🥇 {i+1}위: {s['t']} (+{s['chg']:.2f}%)")
                    st.write(f"현재가: ${s['p']:,.2f} | RSI: {s['rsi']:.1f}")
                    st.markdown("---")

elif menu == "🏆 4. AI 5일 수익률 랭킹":
    st.subheader("🏆 AI 5일 후 예상 수익률 랭킹")
    if st.button("🔮 전 종목 AI 예측 스캔"):
        with st.spinner('AI 분석 중...'):
            pred = []
            for t in ["TSLA", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "PLTR", "ASTS", "SOXL", "TQQQ", "MSTR"]:
                try:
                    h = yf.Ticker(t).history(period="1mo")
                    if len(h)>20: pred.append({"Ticker": t, "현재가($)": round(h['Close'].iloc[-1], 2), "예상 수익률(%)": round(predict_5d_return(h['Close'].iloc[-1], h, calculate_rsi(h).iloc[-1]), 2)})
                except: continue
            if pred:
                df = pd.DataFrame(pred).sort_values(by="예상 수익률(%)", ascending=False).reset_index(drop=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.success("📈 **상승 기대 TOP 5**")
                    st.dataframe(df.head(5).style.applymap(lambda x: "color: #ff4b4b; font-weight: bold;", subset=['예상 수익률(%)']), use_container_width=True)
                with c2:
                    st.error("📉 **하락 주의 WORST 5**")
                    st.dataframe(df.tail(5).sort_values(by="예상 수익률(%)", ascending=True).reset_index(drop=True).style.applymap(lambda x: "color: #0068c9; font-weight: bold;", subset=['예상 수익률(%)']), use_container_width=True)
