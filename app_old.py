"""
ETF Holdings 감성분석 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

st.set_page_config(page_title="ETF 감성분석", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px; border-radius: 12px; color: white; text-align: center;
    }
    .metric-value { font-size: 2.8em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_analyzer():
    from analyzers.finbert_analyzer import FinBERTAnalyzer
    return FinBERTAnalyzer()

def run_single_etf(etf_ticker: str):
    """단일 ETF 처리"""
    try:
        from collectors.etf_collector import ETFCollector
        from collectors.news_collector import NewsCollector
        
        print(f"\n{'='*60}")
        print(f"🔄 {etf_ticker} 처리")
        print(f"{'='*60}")
        
        # Holdings
        collector = ETFCollector()
        holdings = collector.get_etf_holdings(etf_ticker)
        
        if not holdings:
            return None, None, None, None, f"❌ {etf_ticker}: Holdings 없음"
        
        etf_name = collector.get_etf_name(etf_ticker)
        sectors = collector.get_etf_sector_weightings(etf_ticker)
        
        # 뉴스
        print(f"\n📰 뉴스 수집...")
        news_collector = NewsCollector(days=3)
        all_news = news_collector.collect_all(holdings, etf_ticker)
        
        if not all_news:
            return holdings, etf_name, sectors, None, f"⚠️ {etf_ticker}: 뉴스 없음"
        
        # 감성 분석
        print(f"\n🤖 감성 분석...")
        analyzer = load_analyzer()
        analyzed = analyzer.batch_analyze(all_news)
        
        return holdings, etf_name, sectors, analyzed, None
        
    except Exception as e:
        import traceback
        error = f"❌ {etf_ticker}: {e}\n{traceback.format_exc()}"
        print(error)
        return None, None, None, None, error

def run_multiple_etf(etf_list: list):
    """복수 ETF"""
    all_holdings = {}
    all_news = []
    all_sectors = {}
    etf_names = {}
    
    for etf in etf_list:
        holdings, name, sectors, news, error = run_single_etf(etf)
        
        if error:
            st.warning(error)
            continue
        
        if holdings:
            all_holdings[etf] = holdings
            etf_names[etf] = name
            
            if sectors is not None:
                all_sectors[etf] = sectors
            
            if news:
                all_news.extend(news)
    
    if not all_news:
        return None, None, None, None, "❌ 모든 ETF에서 뉴스 없음"
    
    df_list = []
    for news in all_news:
        df_list.append({
            'ETF': news.get('etf', ''),
            'Ticker': news.get('ticker', ''),
            'Company': news.get('company_name', ''),
            'Weight (%)': news.get('weight', 0.0),
            'Category': news.get('category', 'General'),
            'Title': news.get('title', ''),
            'URL': news.get('url', ''),
            'Pub Date': news.get('published_at', '')[:10],
            'Highlights': news.get('highlights', ''),
            'Sentiment': news.get('sentiment_score', 0.0),
            'Source': news.get('source', 'Unknown')
        })
    
    df = pd.DataFrame(df_list)
    
    return all_holdings, etf_names, all_sectors, df, None

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">🚀 ETF Holdings 감성분석</h1>
        <p style="color: white; opacity: 0.9; margin-top: 10px;">
            복수 ETF + 본문 분석 + Highlights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.title("⚙️ 설정")
        
        etf_input = st.text_input(
            "ETF 티커 (쉼표 구분)",
            value="SPY",
            help="예: SPY 또는 SPY, QQQ"
        ).strip().upper()
        
        st.markdown("---")
        
        if st.button("🔄 분석 시작", use_container_width=True, type="primary"):
            if etf_input:
                etf_list = [e.strip() for e in etf_input.split(',') if e.strip()]
                st.session_state.etf_list = etf_list
                st.session_state.run_analysis = True
        
        st.markdown("---")
        
        st.info("""
        **사용법:**
        - 단일: `SPY`
        - 복수: `SPY, QQQ`
        
        **특징:**
        - Highlights: 본문 요약
        - Sentiment: 본문 기반
        - Yahoo + MarketWatch
        """)
    
    if 'df_news' not in st.session_state:
        st.session_state.df_news = None
        st.session_state.all_holdings = None
        st.session_state.etf_names = None
    
    if st.session_state.get('run_analysis', False):
        st.session_state.run_analysis = False
        
        etf_list = st.session_state.etf_list
        etf_str = ', '.join(etf_list)
        
        with st.spinner(f"{etf_str} 분석 중..."):
            holdings, names, sectors, df, error = run_multiple_etf(etf_list)
            
            if error:
                st.error(error)
            elif df is not None:
                st.session_state.all_holdings = holdings
                st.session_state.etf_names = names
                st.session_state.all_sectors = sectors
                st.session_state.df_news = df
                st.session_state.etf_list = etf_list
                
                st.success(f"✅ {etf_str} 완료! {len(df)}개 뉴스")
                st.balloons()
    
    if st.session_state.df_news is None:
        st.info("""
        ### 👋 시작하기
        
        1. ETF 입력: `SPY` 또는 `SPY, QQQ`
        2. "분석 시작" 클릭
        3. 대기 (ETF당 60초)
        """)
        return
    
    df = st.session_state.df_news
    holdings = st.session_state.all_holdings
    names = st.session_state.etf_names
    etf_list = st.session_state.etf_list
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "📈 Holdings", "📰 뉴스", "💾 다운로드"])
    
    with tab1:
        st.header(f"분석: {', '.join(etf_list)}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(etf_list)}</div><div>ETF</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div>뉴스</div></div>', unsafe_allow_html=True)
        
        with col3:
            avg = df['Sentiment'].mean()
            color = "#4CAF50" if avg > 0 else "#f44336"
            st.markdown(f'<div class="metric-card" style="background: {color};"><div class="metric-value">{avg:.3f}</div><div>평균</div></div>', unsafe_allow_html=True)
        
        with col4:
            pos = (df['Sentiment'] > 0.2).sum() / len(df) * 100
            st.markdown(f'<div class="metric-card" style="background: #f093fb;"><div class="metric-value">{pos:.1f}%</div><div>긍정</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        ticker_avg = df.groupby('Ticker')['Sentiment'].mean().sort_values().tail(15)
        colors = ['#f44336' if x < -0.2 else '#4CAF50' if x > 0.2 else '#FFC107' for x in ticker_avg]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(y=ticker_avg.index, x=ticker_avg.values, orientation='h',
                             marker=dict(color=colors), text=[f"{v:.3f}" for v in ticker_avg.values], textposition='outside'))
        fig.update_layout(title="종목별 Sentiment", height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("📈 Holdings")
        
        if len(etf_list) > 1:
            etf = st.selectbox("ETF", etf_list)
        else:
            etf = etf_list[0]
        
        if etf in holdings:
            df_h = pd.DataFrame(holdings[etf])
            st.dataframe(df_h, use_container_width=True)
    
    with tab3:
        st.header("📰 뉴스")
        
        col1, col2 = st.columns(2)
        
        with col1:
            etf_filter = st.selectbox("ETF", ["전체"] + etf_list)
        
        with col2:
            ticker_filter = st.selectbox("종목", ["전체"] + sorted(df['Ticker'].unique()))
        
        filtered = df
        if etf_filter != "전체":
            filtered = filtered[filtered['ETF'] == etf_filter]
        if ticker_filter != "전체":
            filtered = filtered[filtered['Ticker'] == ticker_filter]
        
        st.info(f"📌 {len(filtered)}개")
        
        for _, row in filtered.head(50).iterrows():
            emoji = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            
            with st.expander(f"{emoji} [{row['ETF']}] {row['Ticker']} - {row['Pub Date']}"):
                st.markdown(f"### {row['Title']}")
                st.markdown(f"**Highlights:** {row['Highlights']}")
                st.markdown(f"**Sentiment:** {row['Sentiment']:.4f} | **Category:** {row['Category']}")
                st.markdown(f"[원문]({row['URL']})")
    
    with tab4:
        st.header("💾 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv,
                             f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                             "text/csv", use_container_width=True)
        
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='News', index=False)
                
                for etf in etf_list:
                    if etf in holdings:
                        pd.DataFrame(holdings[etf]).to_excel(writer, sheet_name=f'{etf}_Holdings', index=False)
            
            st.download_button("📥 Excel", output.getvalue(),
                             f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             use_container_width=True)

if __name__ == "__main__":
    main()
