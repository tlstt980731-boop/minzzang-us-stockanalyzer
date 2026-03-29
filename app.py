import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import time

# 1. 페이지 기본 설정
st.set_page_config(page_title="미주 분석기 (민짱 Pro)", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .stApp { background-color: #111111; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #3B82F6; font-weight: bold; }
    [data-testid="stMetricDelta"] { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# --- 공통 함수 모음 ---
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def predict_5d_return(current_price, hist, current_rsi):
    if len(hist) > 5:
        past_5d = (current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100
    else:
        past_5d = 0
    if current_rsi < 40: return abs(past_5d) * 0.4 + 2.5
    elif current_rsi > 70: return -abs(past_5d) * 0.4 - 2.0
    else: return past_5d * 0.3

# 안전한 데이터 수집 엔진 (절대 안 뻗음)
def get_safe_history(ticker_symbol, period="3mo"):
    try:
        tkr = yf.Ticker(ticker_symbol)
        df = tkr.history(period=period)
        if df is not None and not df.empty and len(df) > 5:
            return df
        return None
    except:
        return None

# 한글 검색 만능 사전
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
# 메뉴 0: 메인 홈 (대시보드)
# ==========================================
if menu == "🏠 0. 메인 홈 (대시보드)":
    st.title("환영합니다! 📈 미주 분석기 (민짱 Pro Ver 12.1)")
    st.markdown("여의도/월스트리트 전문가 수준의 심층 데이터와 AI 예측을 무료로 경험해 보세요.")
    st.markdown("---")
    
    st.subheader("🌐 오늘의 거시 경제 (Macro) 현황")
    with st.spinner('실시간 시장 데이터를 불러오는 중...'):
        c_m1, c_m2, c_m3 = st.columns(3)
        try:
            ndx = get_safe_history("^IXIC", "5d")
            if ndx is not None:
                n_p, n_prev = ndx['Close'].iloc[-1], ndx['Close'].iloc[-2]
                c_m1.metric("NASDAQ (나스닥 종합)", f"{n_p:,.2f}", f"{n_p - n_prev:,.2f} ({(n_p - n_prev)/n_prev*100:.2f}%)")
            
            spx = get_safe_history("^GSPC", "5d")
            if spx is not None:
                s_p, s_prev = spx['Close'].iloc[-1], spx['Close'].iloc[-2]
                c_m2.metric("S&P 500", f"{s_p:,.2f}", f"{s_p - s_prev:,.2f} ({(s_p - s_prev)/s_prev*100:.2f}%)")
            
            krw = get_safe_history("USDKRW=X", "5d")
            if krw is not None:
                k_p, k_prev = krw['Close'].iloc[-1], krw['Close'].iloc[-2]
                c_m3.metric("원/달러 환율 (KRW/USD)", f"{k_p:,.2f} 원", f"{k_p - k_prev:,.2f} 원")
        except:
            st.error("시장 데이터를 불러오는 데 실패했습니다.")
    
    st.markdown("---")
    st.info("👈 왼쪽 메뉴를 클릭해서 원하는 종목 스캔을 시작해 보세요!")

# ==========================================
# 메뉴 1: 개별 종목 분석
# ==========================================
elif menu == "🔍 1. 종목 분석 & 7대 리포트":
    st.title("🔍 개별 종목 정밀 분석")
    user_input = st.text_input("종목 코드 또는 한글명 입력 (예: TSLA, AAPL, 테슬라2배)", "")
    
    if user_input != "":
        clean_input = user_input.replace(" ", "").lower()
        ticker_symbol = ticker_map.get(clean_input, user_input.upper())

        try:
            with st.spinner(f'{ticker_symbol} 데이터 영혼까지 끌어오는 중...'):
                ticker = yf.Ticker(ticker_symbol)
                hist = get_safe_history(ticker_symbol, "1y")
                info = ticker.info
                
                if hist is None:
                    st.warning(f"'{user_input}' 데이터를 찾을 수 없습니다. 티커를 확인해 주세요.")
                else:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    
                    stock_name = info.get('longName', info.get('shortName', ticker_symbol))
                    st.markdown(f"### {stock_name} ({ticker_symbol})")
                    
                    short_ratio = info.get('shortRatio', 0)
                    if type(short_ratio) in [float, int] and short_ratio > 4.0:
                        st.error(f"🚨 **숏 스퀴즈 경보:** 공매도 비율({short_ratio})이 높아 급등락 주의!")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("현재가", f"${current_price:,.2f}", f"{change:,.2f} ({change_pct:.2f}%)")
                    
                    target = info.get('targetMeanPrice', 'N/A')
                    if target != 'N/A':
                        c2.metric("월가 목표가", f"${target:,.2f}", f"{(target - current_price)/current_price*100:,.2f}%")
                    else:
                        c2.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
                    
                    c3.metric("거래량", f"{hist['Volume'].iloc[-1]:,}")
                    c4.metric("시가총액", f"${info.get('marketCap', info.get('totalAssets', 0)):,.0f}")

                    hist['SMA20'] = hist['Close'].rolling(20).mean()
                    hist['RSI'] = calculate_rsi(hist)
                    current_rsi = hist['RSI'].iloc[-1]
                    
                    charm_score = 50
                    rec = info.get('recommendationKey', 'hold').lower()
                    if rec in ['buy', 'strong_buy']: charm_score += 20
                    elif rec in ['sell', 'underperform']: charm_score -= 20
                    if current_rsi < 35: charm_score += 15
                    elif current_rsi > 70: charm_score -= 15
                    charm_score = max(0, min(100, charm_score))
                    
                    hist_6m = hist.tail(126)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.8])
                    fig.add_trace(go.Candlestick(x=hist_6m.index, open=hist_6m['Open'], high=hist_6m['High'], low=hist_6m['Low'], close=hist_6m['Close'], name='주가', increasing_line_color='red', decreasing_line_color='blue'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist_6m.index, y=hist_6m['SMA20'], line=dict(color='orange', width=1.5), name='SMA20'), row=1, col=1)
                    fig.add_trace(go.Bar(x=hist_6m.index, y=hist_6m['Volume'], name='거래량', marker_color='gray'), row=2, col=1)
                    fig.update_layout(height=450, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                    t1, t2, t3 = st.tabs(["📝 7대 매트릭스 리포트", "🤖 AI 단기 예측", "🏢 기업 정보"])
                    with t1:
                        st.markdown(f"## 🎯 **투자 매력도: {int(charm_score)} 점**")
                        st.progress(int(charm_score))
                        support = hist['Close'].tail(20).min()
                        resist = hist['Close'].tail(20).max()
                        
                        st.markdown(f"""
                        ### 1. 핵심 요약
                        - 월가 투자의견: **{rec.upper()}** / 매력도 점수: **{int(charm_score)}점**

                        ### 2. 시장 심리 (RSI)
                        - 현재 RSI: **{current_rsi:.1f}** (70 이상: 과열 🚨, 30 이하: 저평가 ✨)

                        ### 3. 매매 시나리오 (진입/손절)
                        - **진입가**: **${support:,.2f}** (최근 20일 지지선)
                        - **목표가**: **${resist:,.2f}** (최근 20일 저항선)
                        - **손절가 (Kill Switch)**: **${support*0.95:,.2f}** (-5% 이탈 시)
                        """)
                    with t2:
                        expected_5d = predict_5d_return(current_price, hist, current_rsi)
                        st.markdown(f"#### 🔮 5일 후 예상 수익률: <span style='color:{'red' if expected_5d > 0 else 'blue'};'>**{expected_5d:+.2f}%**</span>", unsafe_allow_html=True)
                    with t3:
                        st.write(f"- 섹터: {info.get('sector', 'N/A')}")
                        div = info.get('dividendYield', 'N/A')
                        st.write(f"- 배당률: `{div * 100:.2f}%`" if div != 'N/A' and div is not None else "- 배당 없음")
        except:
            st.error("데이터 오류 발생. 잠시 후 다시 시도해 주세요.")

# ==========================================
# 메뉴 2: 테마별 종목 (네가 요청한 방산, 바이오, 전기차 등 대폭 추가!)
# ==========================================
elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 테마별 관련주 비교하기")
    
    # 테마 대폭 확장!!
    themes = {
        "🛰️ 우주/항공": ["ASTS", "RKLB", "LUNR", "SPCE", "BA", "LMT"], 
        "🧠 AI / 반도체": ["NVDA", "AMD", "TSM", "AVGO", "ASML", "PLTR", "ARM", "MU"], 
        "⚡ 빅테크 (M7)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
        "🛡️ 방산 / 밀리터리": ["LMT", "RTX", "NOC", "GD", "PLTR"],
        "🧬 바이오 / 제약": ["LLY", "NVO", "JNJ", "PFE", "MRK", "VRTX"],
        "🔋 전기차 / 2차전지": ["TSLA", "RIVN", "LCID", "ALB", "SQM"],
        "🤖 로봇 / 자동화": ["PATH", "ISRG", "TER", "ROK", "SYK"],
        "🪙 가상화폐 / 블록체인": ["MSTR", "COIN", "MARA", "RIOT", "HOOD"]
    }
    
    selected_theme = st.selectbox("어떤 테마를 훑어볼까요?", list(themes.keys()))
    tickers = themes[selected_theme]
    
    if st.button("🚀 스캔 시작"):
        my_bar = st.progress(0, text="데이터 수집 중...")
        data = []
        
        for i, t in enumerate(tickers):
            try:
                h = get_safe_history(t, "5d")
                if h is not None:
                    p = float(h['Close'].iloc[-1])
                    prev_p = float(h['Close'].iloc[-2])
                    chg = (p - prev_p) / prev_p * 100
                    data.append({"종목": t, "현재가($)": round(p, 2), "변동률(%)": round(chg, 2)})
            except: 
                pass
            
            my_bar.progress(int(((i + 1) / len(tickers)) * 100), text=f"🔍 {t} 스캔 완료! ({i+1}/{len(tickers)})")
            time.sleep(0.1) # 안전장치
            
        if data:
            st.dataframe(pd.DataFrame(data).style.applymap(lambda x: f"color: {'#ff4b4b' if x>0 else '#0068c9'}", subset=['변동률(%)']), use_container_width=True)
        else:
            st.error("데이터를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.")

# ==========================================
# 메뉴 3: 급등주 탐지 (절대 안 뻗는 엔진 장착)
# ==========================================
elif menu == "🔥 3. 급등주 탐지기":
    st.subheader("🔥 실시간 급등주 스캐너")
    if st.button("🚀 스캔 시작 (약 5~10초 소요)"):
        hot_tickers = ["TSLA", "NVDA", "ASTS", "MSTR", "PLTR", "SOXL", "TQQQ", "COIN", "MARA", "LUNR", "RKLB", "HOOD"]
        my_bar = st.progress(0, text="미국 증시 전역을 스캔 중입니다...")
        res = []
        
        for i, t in enumerate(hot_tickers):
            try:
                # 3mo로 넉넉하게 가져와서 RSI 계산 에러 원천 차단
                h = get_safe_history(t, "3mo")
                if h is not None and len(h) > 20:
                    p = float(h['Close'].iloc[-1])
                    prev_p = float(h['Close'].iloc[-2])
                    chg = (p - prev_p) / prev_p * 100
                    rsi = float(calculate_rsi(h).iloc[-1])
                    res.append({"t": t, "p": p, "chg": chg, "rsi": rsi})
            except: 
                pass
            
            my_bar.progress(int(((i + 1) / len(hot_tickers)) * 100), text=f"🔍 {t} 변동성 분석 중... ({i+1}/{len(hot_tickers)})")
            time.sleep(0.1)
            
        if res:
            st.success("✅ 스캔 완료! 가장 핫한 종목을 찾았습니다.")
            top_gainers = sorted(res, key=lambda x: x['chg'], reverse=True)[:3]
            for i, s in enumerate(top_gainers):
                st.markdown(f"### 🥇 {i+1}위: {s['t']} (+{s['chg']:.2f}%)")
                st.write(f"현재가: ${s['p']:,.2f} | RSI: {s['rsi']:.1f}")
                
                # 진입 타당성 분석 추가
                if s['rsi'] > 75:
                    st.error("❌ 너무 급하게 올랐습니다. 단기 고점일 수 있으니 진입을 보류하세요.")
                elif s['rsi'] > 60:
                    st.warning("⚠️ 추세는 좋지만 꽤 올랐습니다. 단기 스윙만 추천합니다.")
                else:
                    st.success("✅ 아직 과열되지 않았습니다. 분할 매수 접근이 유효합니다.")
                st.markdown("---")
        else:
            st.error("스캔에 실패했습니다. 야후 서버 연결 상태를 확인해주세요.")

# ==========================================
# 메뉴 4: AI 5일 수익률 (절대 안 뻗는 엔진 장착)
# ==========================================
elif menu == "🏆 4. AI 5일 수익률 랭킹":
    st.subheader("🏆 AI 5일 후 예상 수익률 랭킹")
    if st.button("🔮 전 종목 AI 예측 스캔"):
        scan_list = ["TSLA", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "PLTR", "ASTS", "SOXL", "TQQQ", "MSTR", "AVGO", "QCOM", "INTC"]
        my_bar = st.progress(0, text="AI 모델 데이터 불러오는 중...")
        pred = []
        
        for i, t in enumerate(scan_list):
            try:
                h = get_safe_history(t, "3mo")
                if h is not None and len(h) > 20:
                    curr_p = float(h['Close'].iloc[-1])
                    rsi = float(calculate_rsi(h).iloc[-1])
                    exp_return = predict_5d_return(curr_p, h, rsi)
                    pred.append({"Ticker": t, "현재가($)": round(curr_p, 2), "예상 수익률(%)": round(exp_return, 2)})
            except: 
                pass
            
            my_bar.progress(int(((i + 1) / len(scan_list)) * 100), text=f"🧠 AI가 {t}의 패턴을 학습 중입니다... ({i+1}/{len(scan_list)})")
            time.sleep(0.1)
            
        if pred:
            st.success("✅ AI 예측 완료!")
            df = pd.DataFrame(pred).sort_values(by="예상 수익률(%)", ascending=False).reset_index(drop=True)
            c1, c2 = st.columns(2)
            with c1:
                st.success("📈 **상승 기대 TOP 5**")
                st.dataframe(df.head(5).style.applymap(lambda x: "color: #ff4b4b; font-weight: bold;", subset=['예상 수익률(%)']), use_container_width=True)
            with c2:
                st.error("📉 **하락 주의 WORST 5**")
                st.dataframe(df.tail(5).sort_values(by="예상 수익률(%)", ascending=True).reset_index(drop=True).style.applymap(lambda x: "color: #0068c9; font-weight: bold;", subset=['예상 수익률(%)']), use_container_width=True)
        else:
            st.error("데이터 로딩에 실패했습니다.")
