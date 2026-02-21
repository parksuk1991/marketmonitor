"""
섹터 ETF 감성분석 Streamlit 대시보드
최종 완성 버전 - 모든 기능 통합
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import io
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="섹터 ETF 감성분석",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# CSS 스타일
st.markdown("""
<style>
    .main { padding: 0rem 1rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    .metric-card:hover { transform: translateY(-5px); }
    .metric-value { 
        font-size: 2.8em; 
        font-weight: bold; 
        margin: 15px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .metric-label { 
        font-size: 1.2em; 
        opacity: 0.95;
        font-weight: 500;
    }
    .sector-card-positive {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        transition: all 0.3s;
    }
    .sector-card-positive:hover {
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.6);
        transform: translateY(-3px);
    }
    .sector-card-negative {
        background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
        transition: all 0.3s;
    }
    .sector-card-negative:hover {
        box-shadow: 0 6px 20px rgba(244, 67, 54, 0.6);
        transform: translateY(-3px);
    }
    .sector-card-neutral {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        transition: all 0.3s;
    }
    .sector-card-neutral:hover {
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        transform: translateY(-3px);
    }
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin: 15px 0;
    }
    .download-section {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        border: 2px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    """데이터 로드 - data/reports 폴더에서 최신 파일"""
    try:
        import glob
        
        # 최신 파일 찾기
        files = glob.glob("data/reports/Market_Monitor_*.xlsx")
        
        if not files:
            st.error("📁 data/reports/ 폴더에 엑셀 파일이 없습니다.")
            st.info("💡 python src/main.py를 실행하여 데이터를 생성하세요.")
            return None, None, {}, None
        
        latest_file = sorted(files)[-1]
        filename = Path(latest_file).name
        
        # 메인 데이터
        df_main = pd.read_excel(latest_file, sheet_name='Daily News Monitor')
        
        # 트렌드 데이터
        try:
            df_trend = pd.read_excel(latest_file, sheet_name='Sentiment Trend')
        except:
            df_trend = None
        
        # 섹터 점수 추출
        sector_scores = {}
        for idx, row in df_main.iterrows():
            if pd.notna(row['ETF']) and pd.isna(row['Title']):
                etf = row['ETF']
                sector = row['Sector']
                
                if pd.notna(row['Ticker']) and 'Simple:' in str(row['Ticker']):
                    simple = float(str(row['Ticker']).replace('Simple:', '').strip())
                    weighted = float(str(row['Company']).replace('Weighted:', '').strip())
                    
                    sector_scores[sector] = {
                        'etf': etf,
                        'simple': simple,
                        'weighted': weighted
                    }
        
        return df_main, df_trend, sector_scores, latest_file
        
    except Exception as e:
        st.error(f"❌ 데이터 로드 오류: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None, None, {}, None

def create_sector_sentiment_chart(df):
    """섹터별 평균 Sentiment 차트 (Plotly)"""
    sector_avg = df.groupby('Sector')['Sentiment'].agg(['mean', 'count']).sort_values('mean')
    
    colors = ['#f44336' if x < -0.2 else '#4CAF50' if x > 0.2 else '#FFC107' 
              for x in sector_avg['mean']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=sector_avg.index,
        x=sector_avg['mean'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=[f"{v:.4f}" for v in sector_avg['mean']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>평균: %{x:.4f}<br>뉴스: %{customdata}개<extra></extra>',
        customdata=sector_avg['count']
    ))
    
    fig.add_vline(x=0, line_dash="dash", line_color="gray", line_width=2)
    
    fig.update_layout(
        title=dict(text="섹터별 평균 Sentiment", font=dict(size=20, color='#333')),
        xaxis_title="평균 Sentiment",
        yaxis_title="",
        height=500,
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(size=12),
        margin=dict(l=150, r=50, t=80, b=50)
    )
    
    return fig

def create_sector_count_chart(df):
    """섹터별 뉴스 개수 차트 (Plotly)"""
    sector_count = df['Sector'].value_counts().sort_values()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=sector_count.index,
        x=sector_count.values,
        orientation='h',
        marker=dict(
            color='#2196F3',
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=sector_count.values,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>뉴스: %{x}개<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text="섹터별 뉴스 개수", font=dict(size=20, color='#333')),
        xaxis_title="뉴스 개수",
        yaxis_title="",
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(size=12),
        margin=dict(l=150, r=50, t=80, b=50)
    )
    
    return fig

def create_category_distribution_chart(df):
    """카테고리 분포 차트 (Plotly)"""
    category_dist = df['Category'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=category_dist.index,
        values=category_dist.values,
        hole=0.4,
        marker=dict(
            colors=px.colors.qualitative.Set3,
            line=dict(color='white', width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=14),
        hovertemplate='<b>%{label}</b><br>개수: %{value}<br>비율: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text="카테고리 분포", font=dict(size=20, color='#333')),
        height=500,
        showlegend=True,
        legend=dict(orientation="v", x=1.05, y=0.5),
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

def create_sentiment_distribution_chart(df):
    """Sentiment 분포 히스토그램 (Plotly)"""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=df['Sentiment'],
        nbinsx=50,
        marker=dict(
            color=df['Sentiment'],
            colorscale='RdYlGn',
            line=dict(color='white', width=1)
        ),
        hovertemplate='Sentiment: %{x:.2f}<br>개수: %{y}<extra></extra>'
    ))
    
    # 평균선
    mean_val = df['Sentiment'].mean()
    fig.add_vline(
        x=mean_val, 
        line_dash="dash", 
        line_color="red", 
        line_width=2,
        annotation_text=f"평균: {mean_val:.4f}",
        annotation_position="top"
    )
    
    fig.update_layout(
        title=dict(text="Sentiment 분포", font=dict(size=20, color='#333')),
        xaxis_title="Sentiment",
        yaxis_title="뉴스 개수",
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

def create_trend_chart(df_trend):
    """시계열 트렌드 차트 (Plotly)"""
    if df_trend is None or len(df_trend) == 0:
        return None
    
    top_tickers = df_trend.nlargest(10, 'Today')
    
    fig = go.Figure()
    
    for _, row in top_tickers.iterrows():
        ticker = row['Ticker']
        dates = []
        values = []
        
        if pd.notna(row['Date -2']):
            dates.append('D-2')
            values.append(row['Date -2'])
        
        if pd.notna(row['Date -1']):
            dates.append('D-1')
            values.append(row['Date -1'])
        
        if pd.notna(row['Today']):
            dates.append('Today')
            values.append(row['Today'])
        
        if len(values) >= 2:
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name=ticker,
                line=dict(width=3),
                marker=dict(size=10),
                hovertemplate=f'<b>{ticker}</b><br>날짜: %{{x}}<br>Sentiment: %{{y:.4f}}<extra></extra>'
            ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    
    fig.update_layout(
        title=dict(text="상위 10개 종목 Sentiment 추이", font=dict(size=20, color='#333')),
        xaxis_title="날짜",
        yaxis_title="Sentiment",
        height=500,
        hovermode='x unified',
        legend=dict(orientation="v", x=1.05, y=1),
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

def create_top_companies_chart(df, sector):
    """섹터별 상위 종목 차트 (Plotly)"""
    sector_df = df[df['Sector'] == sector]
    
    top_companies = sector_df.groupby('Company').agg({
        'Sentiment': 'mean',
        'Title': 'count'
    }).rename(columns={'Title': 'count'}).sort_values('count', ascending=False).head(10)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=top_companies.index,
            y=top_companies['count'],
            name='뉴스 개수',
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>뉴스: %{y}개<extra></extra>'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=top_companies.index,
            y=top_companies['Sentiment'],
            name='평균 Sentiment',
            mode='lines+markers',
            marker=dict(size=10, color='red'),
            line=dict(width=3, color='red'),
            hovertemplate='<b>%{x}</b><br>평균: %{y:.4f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="기업", tickangle=-45)
    fig.update_yaxes(title_text="뉴스 개수", secondary_y=False)
    fig.update_yaxes(title_text="평균 Sentiment", secondary_y=True)
    
    fig.update_layout(
        title=dict(text=f"{sector} 섹터 상위 10개 종목", font=dict(size=18, color='#333')),
        height=500,
        hovermode='x unified',
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(size=11)
    )
    
    return fig

def main():
    # 헤더
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <h1 style="color: white; margin: 0; font-size: 2.5em;">🚀 섹터 ETF 감성분석 대시보드</h1>
        <p style="color: rgba(255,255,255,0.9); margin-top: 10px; font-size: 1.2em;">
            11개 섹터 ETF 실시간 뉴스 감성 분석 시스템
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/stock-market.png", width=80)
        st.title("⚙️ 설정")
        
        st.markdown("---")
        
        if st.button("🔄 데이터 새로고침", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top: 0;">📌 시스템 정보</h4>
            <p><strong>분석 모델:</strong> FinBERT + VADER</p>
            <p><strong>데이터 소스:</strong> Yahoo Finance, Motley Fool</p>
            <p><strong>업데이트:</strong> 매일 자동</p>
            <p><strong>캐시:</strong> 5분</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("""
        ### 📊 지원 섹터 (11개)
        - **XLK** Technology
        - **XLF** Financials
        - **XLV** Health Care
        - **XLY** Consumer Discretionary
        - **XLE** Energy
        - **XLI** Industrials
        - **XLP** Consumer Staples
        - **XLC** Communication Services
        - **XLRE** Real Estate
        - **XLB** Materials
        - **XLU** Utilities
        """)
    
    # 데이터 로드
    with st.spinner("📊 데이터 로드 중..."):
        df_main, df_trend, sector_scores, latest_file = load_data()
    
    if df_main is None:
        st.stop()
    
    # 실제 뉴스만
    df_news = df_main[df_main['Title'].notna()].copy()
    
    # 성공 메시지
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.success(f"✅ 데이터 로드 완료: **{len(df_news)}개** 뉴스")
    with col2:
        if latest_file:
            st.info(f"📅 {Path(latest_file).name[16:26]}")
    with col3:
        st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 개요", 
        "🏢 섹터 분석", 
        "📈 시각화", 
        "📋 상세 데이터",
        "💾 다운로드"
    ])
    
    # ========== 탭 1: 개요 ==========
    with tab1:
        # 섹터별 점수
        st.header("📊 섹터별 감성 점수")
        
        cols_per_row = 4
        sector_list = sorted(sector_scores.keys())
        
        for i in range(0, len(sector_list), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, sector in enumerate(sector_list[i:i+cols_per_row]):
                if j < len(cols):
                    info = sector_scores[sector]
                    weighted = info['weighted']
                    
                    if weighted > 0.3:
                        card_class = "sector-card-positive"
                        emoji = "🟢"
                    elif weighted < -0.3:
                        card_class = "sector-card-negative"
                        emoji = "🔴"
                    else:
                        card_class = "sector-card-neutral"
                        emoji = "🟡"
                    
                    with cols[j]:
                        st.markdown(f"""
                        <div class="{card_class}">
                            <div style="font-size: 1.5em; margin-bottom: 5px;">{emoji}</div>
                            <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 5px;">
                                {info['etf']} | {sector}
                            </div>
                            <div style="font-size: 0.95em; opacity: 0.9; margin: 8px 0;">
                                Simple: {info['simple']:.4f}
                            </div>
                            <div style="font-size: 2em; font-weight: bold; margin-top: 10px;">
                                {weighted:.4f}
                            </div>
                            <div style="font-size: 0.9em; opacity: 0.8;">Weighted Score</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 주요 지표
        st.header("📈 주요 지표")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(df_news)}</div>
                <div class="metric-label">총 뉴스</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_sent = df_news['Sentiment'].mean()
            color = "#4CAF50" if avg_sent > 0 else "#f44336"
            st.markdown(f"""
            <div class="metric-card" style="background: {color};">
                <div class="metric-value">{avg_sent:.4f}</div>
                <div class="metric-label">평균 Sentiment</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pos_ratio = (df_news['Sentiment'] > 0.2).sum() / len(df_news) * 100
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="metric-value">{pos_ratio:.1f}%</div>
                <div class="metric-label">긍정 비율</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            top_sector = df_news.groupby('Sector')['Sentiment'].mean().idxmax()
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-value" style="font-size: 1.8em;">{top_sector[:15]}</div>
                <div class="metric-label">최고 섹터</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Sentiment 분포
        st.subheader("📊 Sentiment 분포")
        fig_dist = create_sentiment_distribution_chart(df_news)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # ========== 탭 2: 섹터 분석 ==========
    with tab2:
        st.header("🏢 섹터별 상세 분석")
        
        selected_sector = st.selectbox(
            "분석할 섹터 선택",
            sorted(df_news['Sector'].unique()),
            key="sector_analysis"
        )
        
        sector_df = df_news[df_news['Sector'] == selected_sector]
        
        # 섹터 지표
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("뉴스 개수", f"{len(sector_df)}개")
        
        with col2:
            sector_avg = sector_df['Sentiment'].mean()
            st.metric("평균 Sentiment", f"{sector_avg:.4f}")
        
        with col3:
            pos_count = (sector_df['Sentiment'] > 0.2).sum()
            st.metric("긍정 뉴스", f"{pos_count}개 ({pos_count/len(sector_df)*100:.1f}%)")
        
        with col4:
            neg_count = (sector_df['Sentiment'] < -0.2).sum()
            st.metric("부정 뉴스", f"{neg_count}개 ({neg_count/len(sector_df)*100:.1f}%)")
        
        st.markdown("---")
        
        # 상위 종목
        st.subheader("📌 주요 종목 분석")
        fig_companies = create_top_companies_chart(df_news, selected_sector)
        st.plotly_chart(fig_companies, use_container_width=True)
        
        st.markdown("---")
        
        # 카테고리 분포
        st.subheader("📑 카테고리 분포")
        col1, col2 = st.columns(2)
        
        with col1:
            category_dist = sector_df['Category'].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=category_dist.index,
                values=category_dist.values,
                hole=0.4
            )])
            fig.update_layout(height=400, title="카테고리별 뉴스 개수")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            category_sent = sector_df.groupby('Category')['Sentiment'].mean().sort_values()
            fig = go.Figure(data=[go.Bar(
                x=category_sent.values,
                y=category_sent.index,
                orientation='h',
                marker_color='lightcoral'
            )])
            fig.update_layout(height=400, title="카테고리별 평균 Sentiment")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # 최근 뉴스
        st.subheader("📰 최근 뉴스 (Top 10)")
        recent = sector_df.sort_values('Pub Date', ascending=False).head(10)
        
        for idx, row in recent.iterrows():
            sent_color = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            
            with st.expander(f"{sent_color} **{row['Company']}** ({row['Ticker']}) - {row['Pub Date']}"):
                st.markdown(f"""
                **제목:** {row['Title']}
                
                **카테고리:** {row['Category']} | **Sentiment:** {row['Sentiment']:.4f}
                
                **요약:** {row['Highlights'][:200]}...
                
                **링크:** [{row['URL']}]({row['URL']})
                """)
    
    # ========== 탭 3: 시각화 ==========
    with tab3:
        st.header("📈 종합 시각화")
        
        # 필터
        st.subheader("🔍 필터")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sector_filter = st.multiselect(
                "섹터",
                sorted(df_news['Sector'].unique()),
                default=sorted(df_news['Sector'].unique()),
                key="viz_sector"
            )
        
        with col2:
            category_filter = st.multiselect(
                "카테고리",
                sorted(df_news['Category'].unique()),
                default=sorted(df_news['Category'].unique()),
                key="viz_category"
            )
        
        with col3:
            sentiment_range = st.slider(
                "Sentiment 범위",
                -1.0, 1.0, (-1.0, 1.0), 0.1,
                key="viz_sentiment"
            )
        
        # 필터 적용
        viz_df = df_news[
            (df_news['Sector'].isin(sector_filter)) &
            (df_news['Category'].isin(category_filter)) &
            (df_news['Sentiment'] >= sentiment_range[0]) &
            (df_news['Sentiment'] <= sentiment_range[1])
        ]
        
        st.info(f"📌 필터 결과: **{len(viz_df)}개** 뉴스")
        
        st.markdown("---")
        
        # 차트
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("섹터별 평균 Sentiment")
            fig1 = create_sector_sentiment_chart(viz_df)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("섹터별 뉴스 개수")
            fig2 = create_sector_count_chart(viz_df)
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("---")
        
        # 카테고리 분포
        st.subheader("카테고리 분포")
        fig3 = create_category_distribution_chart(viz_df)
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown("---")
        
        # Word Cloud
        st.subheader("☁️ Word Cloud")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**빈도 기반**")
            try:
                text = ' '.join(viz_df['Title'].dropna().astype(str))
                wc = WordCloud(
                    width=800, 
                    height=400, 
                    background_color='white',
                    colormap='viridis',
                    max_words=100
                ).generate(text)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
            except:
                st.warning("Word Cloud 생성 실패")
        
        with col2:
            st.markdown("**감성 기여도 기반**")
            try:
                word_sent = {}
                for _, row in viz_df.iterrows():
                    for word in str(row['Title']).lower().split():
                        if len(word) > 3 and word.isalpha():
                            if word not in word_sent:
                                word_sent[word] = []
                            word_sent[word].append(abs(row['Sentiment']))
                
                contrib = {w: np.mean(s)*len(s) for w,s in word_sent.items() if len(s)>=2}
                
                if contrib:
                    wc = WordCloud(
                        width=800, 
                        height=400, 
                        background_color='white',
                        colormap='RdYlGn'
                    ).generate_from_frequencies(contrib)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.warning("데이터 부족")
            except:
                st.warning("Word Cloud 생성 실패")
        
        st.markdown("---")
        
        # 시계열 트렌드
        if df_trend is not None:
            st.subheader("📊 시계열 트렌드")
            fig_trend = create_trend_chart(df_trend)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
    
    # ========== 탭 4: 상세 데이터 ==========
    with tab4:
        st.header("📋 상세 뉴스 데이터")
        
        # 필터
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            table_sector = st.selectbox(
                "섹터",
                ["전체"] + sorted(df_news['Sector'].unique()),
                key="table_sector"
            )
        
        with col2:
            table_category = st.selectbox(
                "카테고리",
                ["전체"] + sorted(df_news['Category'].unique()),
                key="table_category"
            )
        
        with col3:
            table_sentiment = st.selectbox(
                "감성",
                ["전체", "긍정 (>0.2)", "중립", "부정 (<-0.2)"],
                key="table_sentiment"
            )
        
        with col4:
            sort_by = st.selectbox(
                "정렬",
                ["Pub Date", "Sentiment", "Weight (%)"],
                key="sort"
            )
        
        # 필터 적용
        table_df = df_news.copy()
        
        if table_sector != "전체":
            table_df = table_df[table_df['Sector'] == table_sector]
        
        if table_category != "전체":
            table_df = table_df[table_df['Category'] == table_category]
        
        if table_sentiment == "긍정 (>0.2)":
            table_df = table_df[table_df['Sentiment'] > 0.2]
        elif table_sentiment == "중립":
            table_df = table_df[(table_df['Sentiment'] >= -0.2) & (table_df['Sentiment'] <= 0.2)]
        elif table_sentiment == "부정 (<-0.2)":
            table_df = table_df[table_df['Sentiment'] < -0.2]
        
        table_df = table_df.sort_values(sort_by, ascending=False)
        
        st.info(f"📌 **{len(table_df)}개** 뉴스")
        
        # 테이블 표시
        display_df = table_df[[
            'ETF', 'Sector', 'Ticker', 'Company', 'Weight (%)',
            'Category', 'Title', 'URL', 'Pub Date', 'Sentiment'
        ]].copy()
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            column_config={
                "URL": st.column_config.LinkColumn("URL", display_text="🔗 링크"),
                "Sentiment": st.column_config.NumberColumn(
                    "Sentiment",
                    format="%.4f",
                    help="감성 점수 (-1: 부정, +1: 긍정)"
                ),
                "Weight (%)": st.column_config.NumberColumn(
                    "Weight (%)",
                    format="%.2f%%"
                ),
                "Pub Date": st.column_config.DateColumn(
                    "Pub Date",
                    format="YYYY-MM-DD"
                )
            }
        )
    
    # ========== 탭 5: 다운로드 ==========
    with tab5:
        st.header("💾 데이터 다운로드")
        
        st.markdown("""
        <div class="download-section">
            <h3 style="margin-top: 0;">📥 다운로드 옵션</h3>
            <p>필요한 형식으로 데이터를 다운로드하세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 원본 엑셀 파일")
            
            if latest_file and Path(latest_file).exists():
                with open(latest_file, 'rb') as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="📥 전체 엑셀 다운로드",
                    data=excel_data,
                    file_name=Path(latest_file).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
                
                st.info(f"파일: {Path(latest_file).name}")
                st.info(f"크기: {len(excel_data) / 1024:.1f} KB")
        
        with col2:
            st.subheader("📄 CSV 파일")
            
            csv_data = df_news[[
                'ETF', 'Sector', 'Ticker', 'Company', 'Weight (%)',
                'Category', 'Title', 'URL', 'Pub Date', 'Highlights', 'Sentiment'
            ]].to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_data,
                file_name=f"market_monitor_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.info(f"행 개수: {len(df_news)}개")
            st.info(f"크기: {len(csv_data) / 1024:.1f} KB")
        
        st.markdown("---")
        
        # 섹터별 다운로드
        st.subheader("🏢 섹터별 다운로드")
        
        download_sector = st.selectbox(
            "다운로드할 섹터 선택",
            sorted(df_news['Sector'].unique()),
            key="download_sector"
        )
        
        sector_download_df = df_news[df_news['Sector'] == download_sector]
        sector_csv = sector_download_df.to_csv(index=False).encode('utf-8-sig')
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.download_button(
                label=f"📥 {download_sector} 다운로드",
                data=sector_csv,
                file_name=f"{download_sector}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.info(f"📌 {download_sector}: {len(sector_download_df)}개 뉴스")

if __name__ == "__main__":
    main()
