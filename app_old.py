"""
섹터 ETF 감성분석 Streamlit 대시보드
실제 코드 통합 버전
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

# 프로젝트 경로 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 페이지 설정
st.set_page_config(
    page_title="섹터 ETF 감성분석",
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
    .sector-card-positive {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 20px; border-radius: 10px; color: white; margin: 10px 0;
    }
    .sector-card-negative {
        background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        padding: 20px; border-radius: 10px; color: white; margin: 10px 0;
    }
    .sector-card-neutral {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px; border-radius: 10px; color: white; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# 메인 파이프라인 실행
# ========================================

def run_analysis_pipeline():
    """전체 분석 파이프라인 실행"""
    try:
        from config.config import Config
        from collectors.sector_collector import SectorETFCollector
        from collectors.news_collector import NewsCollector
        from analyzers.sentiment_analyzer import SentimentAnalyzer
        from reporters.excel_generator_sector import SectorETFExcelGenerator
        
        # 1. Holdings 수집
        sector_collector = SectorETFCollector()
        sector_holdings = sector_collector.collect_all_sector_holdings(top_n=5)
        portfolio = sector_collector.get_portfolio_for_news(sector_holdings)
        
        # 2. 뉴스 수집
        news_collector = NewsCollector(days=3)
        all_news = news_collector.collect_all_news(portfolio)
        
        # 3. 감성 분석
        analyzer = SentimentAnalyzer(use_finbert=False)
        analyzed_news = analyzer.batch_analyze(all_news)
        
        # 4. DataFrame 생성
        df_list = []
        sector_scores = {}
        
        # 섹터별 정리
        news_by_sector = {}
        for news in analyzed_news:
            sector = news.get('sector', 'Unknown')
            if sector not in news_by_sector:
                news_by_sector[sector] = []
            news_by_sector[sector].append(news)
        
        # 섹터별 점수 계산
        for sector, news_list in news_by_sector.items():
            sentiments = [n.get('sentiment_score', 0.0) for n in news_list]
            weights = [n.get('weight', 1.0) for n in news_list]
            
            if sentiments:
                simple_avg = np.mean(sentiments)
                weighted_avg = np.average(sentiments, weights=weights) if sum(weights) > 0 else simple_avg
                
                sector_info = sector_holdings.get(sector, {})
                
                sector_scores[sector] = {
                    'etf': sector_info.get('etf', ''),
                    'simple': round(simple_avg, 4),
                    'weighted': round(weighted_avg, 4)
                }
            
            # DataFrame 구성
            for news in news_list:
                df_list.append({
                    'ETF': sector_info.get('etf', ''),
                    'Sector': sector,
                    'Ticker': news.get('ticker', ''),
                    'Company': news.get('company_name', ''),
                    'Weight (%)': news.get('weight', 0.0),
                    'Category': news.get('category', 'General'),
                    'Title': news.get('title', ''),
                    'URL': news.get('url', ''),
                    'Pub Date': news.get('published_at', '')[:10],
                    'Highlights': news.get('summary', '')[:100] + '...' if news.get('summary') else '',
                    'Sentiment': news.get('sentiment_score', 0.0)
                })
        
        df = pd.DataFrame(df_list)
        
        return df, sector_scores, analyzed_news, sector_holdings
        
    except Exception as e:
        st.error(f"파이프라인 실행 오류: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None, None, None, None

# ========================================
# 차트 함수들
# ========================================

def create_sector_chart(df):
    sector_avg = df.groupby('Sector')['Sentiment'].mean().sort_values()
    colors = ['#f44336' if x < -0.2 else '#4CAF50' if x > 0.2 else '#FFC107' for x in sector_avg]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=sector_avg.index, x=sector_avg.values, orientation='h',
        marker=dict(color=colors), text=[f"{v:.4f}" for v in sector_avg.values], textposition='outside'
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(title="섹터별 평균 Sentiment", height=500)
    return fig

def create_category_pie(df):
    category_dist = df['Category'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=category_dist.index, values=category_dist.values, hole=0.4)])
    fig.update_layout(title="카테고리 분포", height=400)
    return fig

# ========================================
# 메인 앱
# ========================================

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">🚀 섹터 ETF 감성분석 대시보드</h1>
        <p style="color: white; margin-top: 10px; opacity: 0.9;">
            완전 통합 버전 - Yahoo Finance + VADER 감성 분석
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.title("⚙️ 설정")
        st.markdown("---")
        
        if st.button("🔄 데이터 수집 및 분석 실행", use_container_width=True, type="primary"):
            st.session_state.run_analysis = True
        
        st.markdown("---")
        st.info("""
        **📌 시스템 정보**
        
        - 섹터: 11개
        - 종목: 55개
        - 뉴스 소스: Yahoo Finance, MarketWatch
        - 분석: VADER 감성 분석
        - 카테고리: 자동 분류
        """)
    
    # 세션 상태
    if 'df_news' not in st.session_state:
        st.session_state.df_news = None
        st.session_state.sector_scores = None
        st.session_state.analyzed_news = None
        st.session_state.sector_holdings = None
    
    # 분석 실행
    if st.session_state.get('run_analysis', False):
        st.session_state.run_analysis = False
        
        with st.spinner("데이터 수집 및 분석 중... (약 30초 소요)"):
            df, scores, analyzed, holdings = run_analysis_pipeline()
            
            if df is not None:
                st.session_state.df_news = df
                st.session_state.sector_scores = scores
                st.session_state.analyzed_news = analyzed
                st.session_state.sector_holdings = holdings
                
                st.success(f"✅ 분석 완료! 총 {len(df)}개 뉴스")
                st.balloons()
    
    # 데이터 없을 때
    if st.session_state.df_news is None:
        st.info("""
        ### 👋 시작하기
        
        좌측 사이드바에서 **"🔄 데이터 수집 및 분석 실행"** 버튼을 클릭하세요.
        
        **실행 과정:**
        1. 11개 섹터 ETF Holdings 수집
        2. Yahoo Finance & MarketWatch 뉴스 수집
        3. VADER 감성 분석
        4. 카테고리 자동 분류
        5. 섹터별 점수 계산
        
        **소요 시간:** 약 30-60초
        """)
        return
    
    df = st.session_state.df_news
    scores = st.session_state.sector_scores
    
    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "🏢 섹터 분석", "📈 시각화", "💾 다운로드"])
    
    with tab1:
        st.header("📊 섹터별 감성 점수")
        
        cols = st.columns(4)
        for idx, (sector, info) in enumerate(sorted(scores.items())):
            with cols[idx % 4]:
                weighted = info['weighted']
                card_class = "sector-card-positive" if weighted > 0.3 else "sector-card-negative" if weighted < -0.3 else "sector-card-neutral"
                emoji = "🟢" if weighted > 0.3 else "🔴" if weighted < -0.3 else "🟡"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="font-size: 1.3em;">{emoji}</div>
                    <div style="font-size: 1.1em; font-weight: bold;">{info['etf']} | {sector}</div>
                    <div style="font-size: 0.85em; margin: 5px 0;">Simple: {info['simple']:.4f}</div>
                    <div style="font-size: 1.6em; font-weight: bold;">{weighted:.4f}</div>
                    <div style="font-size: 0.8em;">Weighted</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
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
                <div class="metric-value">{avg:.4f}</div>
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
            top = df.groupby('Sector')['Sentiment'].mean().idxmax()
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-value" style="font-size: 1.5em;">{top[:15]}</div>
                <div style="opacity: 0.9;">최고 섹터</div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.header("🏢 섹터별 상세 분석")
        
        sector = st.selectbox("섹터 선택", sorted(df['Sector'].unique()))
        sector_df = df[df['Sector'] == sector]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("뉴스 개수", f"{len(sector_df)}개")
        col2.metric("평균 Sentiment", f"{sector_df['Sentiment'].mean():.4f}")
        col3.metric("긍정 뉴스", f"{(sector_df['Sentiment']>0.2).sum()}개")
        
        st.markdown("---")
        st.subheader("📰 최근 뉴스")
        
        for _, row in sector_df.head(10).iterrows():
            emoji = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            with st.expander(f"{emoji} {row['Company']} - {row['Pub Date']}"):
                st.markdown(f"**{row['Title']}**")
                st.markdown(f"카테고리: {row['Category']} | Sentiment: {row['Sentiment']:.4f}")
                st.markdown(f"[링크]({row['URL']})")
    
    with tab3:
        st.header("📈 시각화")
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_sector_chart(df), use_container_width=True)
        with col2:
            st.plotly_chart(create_category_pie(df), use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 상세 데이터")
        st.dataframe(df[['Sector', 'Ticker', 'Company', 'Category', 'Title', 'Sentiment']], 
                    use_container_width=True, height=400)
    
    with tab4:
        st.header("💾 데이터 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 CSV 다운로드",
                csv,
                f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='News', index=False)
                pd.DataFrame([
                    {'Sector': s, 'ETF': i['etf'], 'Simple': i['simple'], 'Weighted': i['weighted']}
                    for s, i in scores.items()
                ]).to_excel(writer, sheet_name='Scores', index=False)
            
            st.download_button(
                "📥 Excel 다운로드",
                output.getvalue(),
                f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
