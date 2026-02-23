"""
ETF Holdings 감성분석 대시보드
실시간 Holdings + 다중 뉴스 소스 + FinBERT
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import io
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

st.set_page_config(
    page_title="ETF Holdings 감성분석",
    page_icon="🚀",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px; border-radius: 12px; color: white; text-align: center;
    }
    .metric-value { font-size: 2.8em; font-weight: bold; }
    .source-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        margin-right: 5px;
    }
    .yahoo { background: #720e9e; color: white; }
    .marketwatch { background: #006a4d; color: white; }
    .fool { background: #e87722; color: white; }
    .seeking { background: #f47920; color: white; }
    .benzinga { background: #00a3e0; color: white; }
</style>
""", unsafe_allow_html=True)

# ========================================
# 파이프라인
# ========================================

@st.cache_resource
def load_analyzer():
    """FinBERT 모델 로드"""
    from analyzers.finbert_analyzer import FinBERTAnalyzer
    return FinBERTAnalyzer()

def run_pipeline(etf_ticker: str):
    """전체 파이프라인"""
    try:
        from collectors.etf_collector import ETFCollector
        from collectors.news_collector import NewsCollector
        
        # 1. Holdings 수집 (실시간)
        collector = ETFCollector()
        holdings = collector.get_etf_holdings(etf_ticker, top_n=10)
        
        if not holdings:
            return None, None, None, None, "❌ Holdings 정보를 찾을 수 없습니다. ETF 티커를 확인하세요."
        
        etf_name = collector.get_etf_name(etf_ticker)
        
        # 섹터 비중도 가져오기
        sector_weights = collector.get_etf_sector_weightings(etf_ticker)
        
        # 2. 뉴스 수집 (다중 소스)
        news_collector = NewsCollector(days=3)
        all_news = news_collector.collect_all(holdings, etf_ticker)
        
        if not all_news:
            return holdings, etf_name, sector_weights, None, "⚠️ 뉴스를 찾을 수 없습니다."
        
        # 3. 감성 분석 (FinBERT)
        analyzer = load_analyzer()
        analyzed = analyzer.batch_analyze(all_news)
        
        # 4. DataFrame
        df_list = []
        for news in analyzed:
            df_list.append({
                'ETF': etf_ticker.upper(),
                'Ticker': news.get('ticker', ''),
                'Company': news.get('company_name', ''),
                'Weight (%)': news.get('weight', 0.0),
                'Category': news.get('category', 'General'),
                'Title': news.get('title', ''),
                'URL': news.get('url', ''),
                'Pub Date': news.get('published_at', '')[:10],
                'Sentiment': news.get('sentiment_score', 0.0),
                'Source': news.get('source', 'Unknown')
            })
        
        df = pd.DataFrame(df_list)
        
        return holdings, etf_name, sector_weights, df, None
        
    except Exception as e:
        import traceback
        error_msg = f"❌ 오류: {e}\n\n{traceback.format_exc()}"
        return None, None, None, None, error_msg

# ========================================
# 차트
# ========================================

def create_sentiment_by_ticker(df):
    ticker_avg = df.groupby('Ticker')['Sentiment'].mean().sort_values()
    colors = ['#f44336' if x < -0.2 else '#4CAF50' if x > 0.2 else '#FFC107' for x in ticker_avg]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=ticker_avg.index, x=ticker_avg.values, orientation='h',
        marker=dict(color=colors),
        text=[f"{v:.3f}" for v in ticker_avg.values], textposition='outside'
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(title="종목별 평균 Sentiment", height=500)
    return fig

def create_source_distribution(df):
    source_dist = df['Source'].value_counts()
    fig = go.Figure(data=[go.Pie(
        labels=source_dist.index, 
        values=source_dist.values,
        marker=dict(colors=['#720e9e', '#006a4d', '#e87722', '#f47920', '#00a3e0'])
    )])
    fig.update_layout(title="뉴스 소스 분포", height=400)
    return fig

def create_category_pie(df):
    cat_dist = df['Category'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=cat_dist.index, values=cat_dist.values, hole=0.4)])
    fig.update_layout(title="카테고리 분포", height=400)
    return fig

# ========================================
# 메인
# ========================================

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">🚀 ETF Holdings 감성분석</h1>
        <p style="color: white; opacity: 0.9; margin-top: 10px;">
            실시간 Holdings + 5개 뉴스 소스 + FinBERT 감성 분석
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.title("⚙️ 설정")
        
        etf_input = st.text_input(
            "ETF 티커 입력",
            value="SPY",
            help="예: SPY, QQQ, XLK, VTI"
        ).strip().upper()
        
        st.markdown("---")
        
        if st.button("🔄 분석 시작", use_container_width=True, type="primary"):
            if etf_input:
                st.session_state.etf_ticker = etf_input
                st.session_state.run_analysis = True
        
        st.markdown("---")
        
        st.info("""
        **📊 데이터 소스**
        
        **Holdings:**
        - yahooquery (실시간)
        
        **뉴스:**
        - Yahoo Finance
        - MarketWatch
        - Motley Fool
        - Seeking Alpha
        - Benzinga
        
        **분석:**
        - FinBERT (금융 특화 AI)
        """)
    
    # 세션 상태
    if 'df_news' not in st.session_state:
        st.session_state.df_news = None
        st.session_state.holdings = None
        st.session_state.etf_name = None
        st.session_state.sector_weights = None
    
    # 분석 실행
    if st.session_state.get('run_analysis', False):
        st.session_state.run_analysis = False
        
        etf = st.session_state.etf_ticker
        
        with st.spinner(f"{etf} 분석 중... (약 60초 소요)"):
            holdings, etf_name, sector_weights, df, error = run_pipeline(etf)
            
            if error:
                st.error(error)
            elif df is not None:
                st.session_state.holdings = holdings
                st.session_state.etf_name = etf_name
                st.session_state.sector_weights = sector_weights
                st.session_state.df_news = df
                
                st.success(f"✅ {etf} 분석 완료! {len(df)}개 뉴스")
                st.balloons()
    
    # 데이터 없을 때
    if st.session_state.df_news is None:
        st.info("""
        ### 👋 시작하기
        
        1. 좌측 사이드바에서 **ETF 티커 입력**
        2. **"🔄 분석 시작"** 버튼 클릭
        3. 약 60초 대기 (실시간 데이터 수집)
        
        **예시:** SPY, QQQ, XLK, XLF, VTI, IWM
        """)
        return
    
    # 데이터 표시
    df = st.session_state.df_news
    holdings = st.session_state.holdings
    etf_name = st.session_state.etf_name
    sector_weights = st.session_state.sector_weights
    etf_ticker = st.session_state.etf_ticker
    
    # 탭
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 개요", 
        "📈 Holdings", 
        "🔍 분석", 
        "📰 뉴스",
        "💾 다운로드"
    ])
    
    with tab1:
        st.header(f"📊 {etf_ticker} - {etf_name}")
        
        # 주요 지표
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(df)}</div>
                <div style="opacity: 0.9;">총 뉴스</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg = df['Sentiment'].mean()
            color = "#4CAF50" if avg > 0 else "#f44336"
            st.markdown(f"""
            <div class="metric-card" style="background: {color};">
                <div class="metric-value">{avg:.3f}</div>
                <div style="opacity: 0.9;">평균 Sentiment</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pos = (df['Sentiment'] > 0.2).sum() / len(df) * 100
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="metric-value">{pos:.1f}%</div>
                <div style="opacity: 0.9;">긍정 비율</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            sources = df['Source'].nunique()
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-value">{sources}</div>
                <div style="opacity: 0.9;">뉴스 소스</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 종목별 Sentiment
        st.subheader("종목별 평균 Sentiment")
        fig = create_sentiment_by_ticker(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("📈 Top 10 Holdings (실시간)")
        
        holdings_df = pd.DataFrame(holdings)
        holdings_df.index = holdings_df.index + 1
        
        st.dataframe(
            holdings_df,
            use_container_width=True,
            column_config={
                "ticker": "티커",
                "name": "기업명",
                "weight": st.column_config.NumberColumn("비중 (%)", format="%.2f")
            }
        )
        
        # Holdings 차트
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=holdings_df['weight'],
            y=holdings_df['ticker'],
            orientation='h',
            marker_color='lightblue',
            text=[f"{v:.2f}%" for v in holdings_df['weight']],
            textposition='outside'
        ))
        fig.update_layout(title="Holdings 비중", xaxis_title="비중 (%)", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # 섹터 비중 (있으면)
        if sector_weights is not None and not sector_weights.empty:
            st.markdown("---")
            st.subheader("섹터 비중")
            
            fig = go.Figure(data=[go.Pie(
                labels=sector_weights['Sector'],
                values=sector_weights['Weight (%)'],
                hole=0.4
            )])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("🔍 상세 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_category_pie(df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_source_distribution(df), use_container_width=True)
    
    with tab4:
        st.header("📰 최근 뉴스")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ticker_filter = st.selectbox("종목 필터", ["전체"] + sorted(df['Ticker'].unique()))
        
        with col2:
            source_filter = st.selectbox("소스 필터", ["전체"] + sorted(df['Source'].unique()))
        
        filtered = df
        if ticker_filter != "전체":
            filtered = filtered[filtered['Ticker'] == ticker_filter]
        if source_filter != "전체":
            filtered = filtered[filtered['Source'] == source_filter]
        
        st.info(f"📌 {len(filtered)}개 뉴스")
        
        for _, row in filtered.head(30).iterrows():
            emoji = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            
            source_class = row['Source'].lower().replace(' ', '')
            
            with st.expander(f"{emoji} {row['Ticker']} - {row['Pub Date']}"):
                st.markdown(f"**{row['Title']}**")
                st.markdown(f"""
                <span class="source-badge {source_class}">{row['Source']}</span>
                카테고리: {row['Category']} | Sentiment: {row['Sentiment']:.4f}
                """, unsafe_allow_html=True)
                st.markdown(f"[링크]({row['URL']})")
    
    with tab5:
        st.header("💾 데이터 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 CSV 다운로드",
                csv,
                f"{etf_ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='News', index=False)
                holdings_df.to_excel(writer, sheet_name='Holdings', index=False)
                if sector_weights is not None:
                    sector_weights.to_excel(writer, sheet_name='Sectors', index=False)
            
            st.download_button(
                "📥 Excel 다운로드",
                output.getvalue(),
                f"{etf_ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
