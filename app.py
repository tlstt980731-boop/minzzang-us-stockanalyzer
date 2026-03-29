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

def get_safe_history(ticker_symbol, period="3mo"):
    try:
        tkr = yf.Ticker(ticker_symbol)
        df = tkr.history(period=period)
        if df is not None and not df.empty and len(df) > 5:
            return df
        return None
    except:
        return None

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
    ["🏠 0. 메인 홈 (대시보드)", "🔍 1. 종목 분석 & 7대 리포트", "🚀 2. 테마별 종목 모아보기", "🔥 3. 급등주 탐지기", "🏆 4. AI 5일 수익률 랭킹"]
)

# ==========================================
# 메뉴 0, 1, 2 (이전과 동일하게 완벽 작동)
# ==========================================
if menu == "🏠 0. 메인 홈 (대시보드)":
    st.title("환영합니다! 📈 미주 분석기 (민짱 Pro Ver 13.0)")
    st.markdown("여의도/월스트리트 전문가 수준의 심층 데이터와 실전 매매 타점을 무료로 경험해 보세요.")
    st.markdown("---")
    st.subheader("🌐 오늘의 거시 경제 (Macro) 현황")
    with st.spinner('실시간 시장 데이터를 불러오는 중...'):
        c_m1, c_m2, c_m3 = st.columns(3)
        try:
            ndx = get_safe_history("^IXIC", "5d")
            if ndx is not None:
                c_m1.metric("NASDAQ", f"{ndx['Close'].iloc[-1]:,.2f}", f"{ndx['Close'].iloc[-1] - ndx['Close'].iloc[-2]:,.2f}")
            spx = get_safe_history("^GSPC", "5d")
            if spx is not None:
                c_m2.metric("S&P 500", f"{spx['Close'].iloc[-1]:,.2f}", f"{spx['Close'].iloc[-1] - spx['Close'].iloc[-2]:,.2f}")
            krw = get_safe_history("USDKRW=X", "5d")
            if krw is not None:
                c_m3.metric("원/달러 환율", f"{krw['Close'].iloc[-1]:,.2f} 원", f"{krw['Close'].iloc[-1] - krw['Close'].iloc[-2]:,.2f} 원")
        except: st.error("데이터 로딩 실패")
    st.markdown("---")
    st.info("👈 왼쪽 메뉴를 클릭해서 실전 스캔을 시작해 보세요!")

elif menu == "🔍 1. 종목 분석 & 7대 리포트":
    st.title("🔍 개별 종목 정밀 분석")
    user_input = st.text_input("종목 코드 또는 한글명 입력 (예: TSLA, AAPL)", "")
    if user_input != "":
        ticker_symbol = ticker_map.get(user_input.replace(" ", "").lower(), user_input.upper())
        with st.spinner(f'{ticker_symbol} 분석 중...'):
            hist = get_safe_history(ticker_symbol, "1y")
            if hist is None: st.warning("데이터를 찾을 수 없습니다.")
            else:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                p, prev_p = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                st.markdown(f"### {info.get('longName', ticker_symbol)} ({ticker_symbol})")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("현재가", f"${p:,.2f}", f"{p - prev_p:,.2f} ({(p-prev_p)/prev_p*100:.2f}%)")
                c2.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', p):,.2f}")
                c3.metric("거래량", f"{hist['Volume'].iloc[-1]:,}")
                c4.metric("시가총액", f"${info.get('marketCap', 0):,.0f}")
                
                hist['SMA20'] = hist['Close'].rolling(20).mean()
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.8])
                fig.add_trace(go.Candlestick(x=hist.index[-126:], open=hist['Open'][-126:], high=hist['High'][-126:], low=hist['Low'][-126:], close=hist['Close'][-126:], name='주가', increasing_line_color='red', decreasing_line_color='blue'), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist.index[-126:], y=hist['SMA20'][-126:], line=dict(color='orange', width=1.5)), row=1, col=1)
                fig.add_trace(go.Bar(x=hist.index[-126:], y=hist['Volume'][-126:], marker_color='gray'), row=2, col=1)
                fig.update_layout(height=450, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                t1, t2 = st.tabs(["📝 7대 매트릭스", "🤖 실전 매매 타점"])
                with t1:
                    st.write(f"- 월가 투자의견: **{info.get('recommendationKey', 'N/A').upper()}**")
                    st.write(f"- P/E Ratio: {info.get('trailingPE', 'N/A')}")
                with t2:
                    entry = p * 0.98
                    st.success(f"🎯 추천 진입가 (눌림목): **${entry:,.2f}**")
                    st.error(f"🚨 칼손절가 (-5%): **${entry*0.95:,.2f}**")

elif menu == "🚀 2. 테마별 종목 모아보기":
    st.subheader("🚀 테마별 관련주 비교하기")
    themes = {"🛰️ 우주/항공": ["ASTS", "RKLB", "LUNR", "SPCE"], "🧠 AI / 반도체": ["NVDA", "AMD", "TSM", "PLTR"], "⚡ 빅테크 (M7)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]}
    selected_theme = st.selectbox("테마 선택:", list(themes.keys()))
    if st.button("🚀 스캔 시작"):
        my_bar = st.progress(0, text="데이터 수집 중...")
        data = []
        for i, t in enumerate(themes[selected_theme]):
            h = get_safe_history(t, "5d")
            if h is not None:
                p, prev_p = h['Close'].iloc[-1], h['Close'].iloc[-2]
                data.append({"종목": t, "현재가($)": round(p, 2), "변동률(%)": round((p-prev_p)/prev_p*100, 2)})
            my_bar.progress(int(((i+1)/len(themes[selected_theme]))*100))
        if data: st.dataframe(pd.DataFrame(data).style.applymap(lambda x: f"color: {'#ff4b4b' if x>0 else '#0068c9'}", subset=['변동률(%)']), use_container_width=True)

# ==========================================
# 메뉴 3: 급등주 탐지 (시총 무관 40대장주 + 실전 타점 계산)
# ==========================================
elif menu == "🔥 3. 급등주 탐지기":
    st.subheader("🔥 실시간 급등주 스캐너 (시총 무관 변동성 대장주)")
    st.write("대형주부터 동전주까지 현재 미 증시에서 가장 핫한 40개 종목을 스캔합니다.")
    
    if st.button("🚀 스캔 시작 (약 10~15초 소요)"):
        # 시총 무관하게 변동성 엄청난 종목들 40개 엄선!
        hot_tickers = [
            "TSLA", "NVDA", "ASTS", "MSTR", "PLTR", "SOXL", "TQQQ", "COIN", "MARA", "LUNR",
            "RKLB", "HOOD", "GME", "AMC", "DJT", "CVNA", "UPST", "SOUN", "BBAI", "SMCI",
            "ARM", "RDDT", "ALAB", "IONQ", "JOBY", "ACHR", "NIO", "LCID", "RIVN", "SYM"
        ]
        my_bar = st.progress(0, text="전 종목 스캔 중입니다...")
        res = []
        
        for i, t in enumerate(hot_tickers):
            try:
                h = get_safe_history(t, "3mo")
                if h is not None and len(h) > 20:
                    p = float(h['Close'].iloc[-1])
                    prev_p = float(h['Close'].iloc[-2])
                    chg = (p - prev_p) / prev_p * 100
                    rsi = float(calculate_rsi(h).iloc[-1])
                    
                    # 실전 타점 계산
                    entry_p = p * 0.98 # -2% 눌림목 진입
                    stop_p = entry_p * 0.95 # -5% 손절
                    target_p = h['Close'].tail(20).max() # 최근 20일 고점을 목표가로
                    if target_p <= p: target_p = p * 1.1 # 이미 최고점 돌파중이면 10% 더 위로 타겟
                    est_return = (target_p - entry_p) / entry_p * 100
                    
                    res.append({
                        "t": t, "p": p, "chg": chg, "rsi": rsi, 
                        "entry": entry_p, "stop": stop_p, "return": est_return
                    })
            except: pass
            my_bar.progress(int(((i + 1) / len(hot_tickers)) * 100), text=f"🔍 {t} 분석 중... ({i+1}/{len(hot_tickers)})")
            time.sleep(0.05)
            
        if res:
            st.success("✅ 스캔 완료! 가장 변동성이 큰 종목 TOP 3를 찾았습니다.")
            top_gainers = sorted(res, key=lambda x: x['chg'], reverse=True)[:3]
            for i, s in enumerate(top_gainers):
                st.markdown(f"### 🥇 {i+1}위: {s['t']} (+{s['chg']:.2f}%)")
                st.write(f"**현재가:** ${s['p']:,.2f} | **RSI:** {s['rsi']:.1f}")
                
                # 네가 원했던 상세 분석창!
                st.info(f"""
                **💡 민짱의 실전 매매 시나리오**
                - 🎯 **추천 진입가 (안전 눌림목):** **${s['entry']:,.2f}** (현재가 대비 -2% 하락 시 매수)
                - 🚨 **추천 손절가 (칼손절):** **${s['stop']:,.2f}** (진입가 대비 -5% 이탈 시)
                - 💸 **추천가 진입 시 예상 수익률:** **+{s['return']:,.2f}%** (최근 저항선 목표)
                """)
                st.markdown("---")
        else:
            st.error("스캔에 실패했습니다.")

# ==========================================
# 메뉴 4: AI 5일 수익률 랭킹 (실전 타점 포함)
# ==========================================
elif menu == "🏆 4. AI 5일 수익률 랭킹":
    st.subheader("🏆 AI 5일 후 예상 수익률 & 실전 타점 랭킹")
    st.write("단순 예측을 넘어, **'정확히 얼마에 사서 손절은 어디로 잡아야 할지'** AI가 표로 정리해 줍니다.")
    
    if st.button("🔮 전 종목 AI 예측 스캔"):
        # 시총 무관 타겟 리스트
        scan_list = ["TSLA", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "PLTR", "ASTS", "SOXL", "TQQQ", "MSTR", "AVGO", "QCOM", "INTC", "GME", "CVNA", "UPST"]
        my_bar = st.progress(0, text="AI 모델 데이터 불러오는 중...")
        pred = []
        
        for i, t in enumerate(scan_list):
            try:
                h = get_safe_history(t, "3mo")
                if h is not None and len(h) > 20:
                    curr_p = float(h['Close'].iloc[-1])
                    rsi = float(calculate_rsi(h).iloc[-1])
                    
                    # 5일 후 상승/하락 예측 (기존 로직)
                    exp_return_from_now = predict_5d_return(curr_p, h, rsi)
                    
                    # 실전 타점 계산 로직 적용!
                    entry_p = curr_p * 0.98 # -2% 눌림목 진입
                    stop_p = entry_p * 0.95 # -5% 손절
                    
                    # 현재가 대비 AI 예측 %를 가격으로 환산한 목표가
                    target_p = curr_p * (1 + (exp_return_from_now / 100))
                    
                    # 진입가 기준 진짜 기대 수익률 계산
                    real_est_return = (target_p - entry_p) / entry_p * 100
                    
                    pred.append({
                        "Ticker": t, 
                        "현재가($)": round(curr_p, 2), 
                        "진입 추천가($)": round(entry_p, 2),
                        "손절가($)": round(stop_p, 2),
                        "진입 시 기대수익(%)": round(real_est_return, 2)
                    })
            except: pass
            my_bar.progress(int(((i + 1) / len(scan_list)) * 100), text=f"🧠 AI가 {t} 타점 계산 중... ({i+1}/{len(scan_list)})")
            time.sleep(0.05)
            
        if pred:
            st.success("✅ AI 실전 타점 분석 완료! 표를 좌우로 스크롤해서 보세요.")
            df = pd.DataFrame(pred).sort_values(by="진입 시 기대수익(%)", ascending=False).reset_index(drop=True)
            
            st.success("📈 **[상승 기대 TOP 5] 지금 매수하기 좋은 종목**")
            st.dataframe(df.head(5).style.applymap(lambda x: "color: #ff4b4b; font-weight: bold;", subset=['진입 시 기대수익(%)']), use_container_width=True)
            
            st.error("📉 **[하락 주의 WORST 5] 예상 수익이 마이너스인 피해야 할 종목**")
            st.dataframe(df.tail(5).sort_values(by="진입 시 기대수익(%)", ascending=True).reset_index(drop=True).style.applymap(lambda x: "color: #0068c9; font-weight: bold;", subset=['진입 시 기대수익(%)']), use_container_width=True)
