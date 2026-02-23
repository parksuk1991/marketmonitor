"""
ETF Holdings 감성분석 (최종 버전)
복수 ETF 지원 + Highlights + 본문 감성 분석
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

st.set_page_config(page_title="ETF Holdings 감성분석", page_icon="🚀", layout="wide")

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

def run_pipeline_single(etf_ticker: str):
    try:
        from collectors.etf_collector import ETFCollector
        from collectors.news_collector import NewsCollector
        
        collector = ETFCollector()
        holdings = collector.get_etf_holdings(etf_ticker, top_n=10)
        
        if not holdings:
            return None, None, None, None, f"❌ {etf_ticker}: Holdings 정보 없음"
        
        etf_name = collector.get_etf_name(etf_ticker)
        sector_weights = collector.get_etf_sector_weightings(etf_ticker)
        
        news_collector = NewsCollector(days=3)
        all_news = news_collector.collect_all(holdings, etf_ticker)
        
        if not all_news:
            return holdings, etf_name, sector_weights, None, f"⚠️ {etf_ticker}: 뉴스 없음"
        
        analyzer = load_analyzer()
        analyzed = analyzer.batch_analyze(all_news)
        
        return holdings, etf_name, sector_weights, analyzed, None
        
    except Exception as e:
        import traceback
        return None, None, None, None, f"❌ {etf_ticker} 오류: {e}\n{traceback.format_exc()}"

def run_pipeline_multiple(etf_list: list):
    all_holdings = {}
    all_news = []
    all_sector_weights = {}
    etf_names = {}
    
    for etf in etf_list:
        print(f"\n{'='*60}\n🔄 {etf} 처리 중...\n{'='*60}")
        
        holdings, etf_name, sector_weights, news, error = run_pipeline_single(etf)
        
        if error:
            print(error)
            continue
        
        if holdings:
            all_holdings[etf] = holdings
            etf_names[etf] = etf_name
            
            if sector_weights is not None:
                all_sector_weights[etf] = sector_weights
            
            if news:
                all_news.extend(news)
    
    if not all_news:
        return None, None, None, None, "❌ 모든 ETF에서 뉴스를 찾을 수 없습니다"
    
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
    
    return all_holdings, etf_names, all_sector_weights, df, None

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">🚀 ETF Holdings 감성분석</h1>
        <p style="color: white; opacity: 0.9; margin-top: 10px;">
            복수 ETF 지원 + 본문 분석 + FinBERT + Highlights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.title("⚙️ 설정")
        
        etf_input = st.text_input(
            "ETF 티커 입력 (쉼표로 구분)",
            value="SPY",
            help="예: SPY 또는 SPY, QQQ, XLK"
        ).strip().upper()
        
        st.markdown("---")
        
        if st.button("🔄 분석 시작", use_container_width=True, type="primary"):
            if etf_input:
                etf_list = [e.strip() for e in etf_input.split(',') if e.strip()]
                st.session_state.etf_list = etf_list
                st.session_state.run_analysis = True
        
        st.markdown("---")
        
        st.info("""
        **📊 사용법**
        
        **단일:** `SPY`
        **복수:** `SPY, QQQ, XLK`
        
        **특징:**
        - Highlights: 본문 요약
        - Sentiment: 본문 기반
        - 5개 뉴스 소스
        """)
    
    if 'df_news' not in st.session_state:
        st.session_state.df_news = None
        st.session_state.all_holdings = None
        st.session_state.etf_names = None
        st.session_state.all_sector_weights = None
        st.session_state.etf_list = None
    
    if st.session_state.get('run_analysis', False):
        st.session_state.run_analysis = False
        
        etf_list = st.session_state.etf_list
        etf_str = ', '.join(etf_list)
        
        with st.spinner(f"{etf_str} 분석 중... (약 {len(etf_list) * 60}초 소요)"):
            all_holdings, etf_names, all_sector_weights, df, error = run_pipeline_multiple(etf_list)
            
            if error:
                st.error(error)
            elif df is not None:
                st.session_state.all_holdings = all_holdings
                st.session_state.etf_names = etf_names
                st.session_state.all_sector_weights = all_sector_weights
                st.session_state.df_news = df
                
                st.success(f"✅ {etf_str} 분석 완료! {len(df)}개 뉴스")
                st.balloons()
    
    if st.session_state.df_news is None:
        st.info("""
        ### 👋 시작하기
        
        1. ETF 티커 입력
           - 단일: `SPY`
           - 복수: `SPY, QQQ, XLK`
        
        2. "분석 시작" 클릭
        3. 대기 (ETF당 60초)
        """)
        return
    
    df = st.session_state.df_news
    all_holdings = st.session_state.all_holdings
    etf_names = st.session_state.etf_names
    all_sector_weights = st.session_state.all_sector_weights
    etf_list = st.session_state.etf_list
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "📈 Holdings", "📰 뉴스", "💾 다운로드"])
    
    with tab1:
        st.header(f"📊 분석된 ETF: {', '.join(etf_list)}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(etf_list)}</div><div style="opacity: 0.9;">ETF</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div style="opacity: 0.9;">뉴스</div></div>', unsafe_allow_html=True)
        
        with col3:
            avg = df['Sentiment'].mean()
            color = "#4CAF50" if avg > 0 else "#f44336"
            st.markdown(f'<div class="metric-card" style="background: {color};"><div class="metric-value">{avg:.3f}</div><div style="opacity: 0.9;">평균</div></div>', unsafe_allow_html=True)
        
        with col4:
            pos = (df['Sentiment'] > 0.2).sum() / len(df) * 100
            st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><div class="metric-value">{pos:.1f}%</div><div style="opacity: 0.9;">긍정</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        ticker_avg = df.groupby('Ticker')['Sentiment'].mean().sort_values().tail(15)
        colors = ['#f44336' if x < -0.2 else '#4CAF50' if x > 0.2 else '#FFC107' for x in ticker_avg]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(y=ticker_avg.index, x=ticker_avg.values, orientation='h',
                             marker=dict(color=colors), text=[f"{v:.3f}" for v in ticker_avg.values], textposition='outside'))
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        fig.update_layout(title="종목별 평균 Sentiment", height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("📈 Holdings")
        
        if len(etf_list) > 1:
            selected_etf = st.selectbox("ETF 선택", etf_list)
        else:
            selected_etf = etf_list[0]
        
        if selected_etf in all_holdings:
            holdings_df = pd.DataFrame(all_holdings[selected_etf])
            holdings_df.index = holdings_df.index + 1
            
            st.dataframe(holdings_df, use_container_width=True,
                        column_config={"ticker": "티커", "name": "기업명",
                                     "weight": st.column_config.NumberColumn("비중 (%)", format="%.2f")})
    
    with tab3:
        st.header("📰 뉴스 (Highlights 포함)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            etf_filter = st.selectbox("ETF", ["전체"] + etf_list)
        with col2:
            ticker_filter = st.selectbox("종목", ["전체"] + sorted(df['Ticker'].unique()))
        with col3:
            source_filter = st.selectbox("소스", ["전체"] + sorted(df['Source'].unique()))
        
        filtered = df
        if etf_filter != "전체":
            filtered = filtered[filtered['ETF'] == etf_filter]
        if ticker_filter != "전체":
            filtered = filtered[filtered['Ticker'] == ticker_filter]
        if source_filter != "전체":
            filtered = filtered[filtered['Source'] == source_filter]
        
        st.info(f"📌 {len(filtered)}개 뉴스")
        
        for _, row in filtered.head(50).iterrows():
            emoji = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            
            with st.expander(f"{emoji} [{row['ETF']}] {row['Ticker']} - {row['Pub Date']}"):
                st.markdown(f"### {row['Title']}")
                st.markdown(f"**Highlights:** {row['Highlights']}")
                st.markdown(f"**ETF:** {row['ETF']} | **카테고리:** {row['Category']} | **소스:** {row['Source']}")
                st.markdown(f"**Sentiment:** {row['Sentiment']:.4f}")
                st.markdown(f"[원문]({row['URL']})")
    
    with tab4:
        st.header("💾 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv, f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                             "text/csv", use_container_width=True)
        
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='News', index=False)
                for etf in etf_list:
                    if etf in all_holdings:
                        pd.DataFrame(all_holdings[etf]).to_excel(writer, sheet_name=f'{etf}_Holdings', index=False)
            
            st.download_button("📥 Excel", output.getvalue(),
                             f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             use_container_width=True)

if __name__ == "__main__":
    main()
