"""
섹터 ETF 감성분석 Streamlit 대시보드
GitHub + Streamlit Cloud 배포용
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="섹터 ETF 감성분석",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main { padding: 0rem 1rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        padding-left: 20px;
        padding-right: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value { font-size: 2.5em; font-weight: bold; margin: 10px 0; }
    .metric-label { font-size: 1.1em; opacity: 0.9; }
    .sector-positive {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 15px; border-radius: 8px; color: white; margin: 10px 0;
    }
    .sector-negative {
        background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        padding: 15px; border-radius: 8px; color: white; margin: 10px 0;
    }
    .sector-neutral {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px; border-radius: 8px; color: white; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 (GitHub에서)
@st.cache_data(ttl=3600)
def load_data_from_github():
    """GitHub에서 데이터 로드"""
    try:
        # GitHub raw URL
        base_url = "https://raw.githubusercontent.com/YOUR_USERNAME/market-monitor/main/data/"
        
        # 최신 파일 URL (예: Market_Monitor_2026-02-19.xlsx)
        file_url = base_url + "Market_Monitor_latest.xlsx"
        
        df_main = pd.read_excel(file_url, sheet_name='Daily News Monitor')
        
        try:
            df_trend = pd.read_excel(file_url, sheet_name='Sentiment Trend')
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
        
        return df_main, df_trend, sector_scores
        
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None, None, {}

# 로컬 파일 로드 (개발용)
@st.cache_data(ttl=300)
def load_data_local():
    """로컬 파일에서 데이터 로드"""
    try:
        import glob
        files = glob.glob("data/reports/Market_Monitor_*.xlsx")
        
        if not files:
            return None, None, {}
        
        latest = sorted(files)[-1]
        
        df_main = pd.read_excel(latest, sheet_name='Daily News Monitor')
        
        try:
            df_trend = pd.read_excel(latest, sheet_name='Sentiment Trend')
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
        
        return df_main, df_trend, sector_scores
        
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None, None, {}

def main():
    st.title("🚀 섹터 ETF 감성분석 대시보드")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 데이터 소스 선택
        data_source = st.radio(
            "데이터 소스",
            ["GitHub", "로컬"],
            help="GitHub: 온라인 배포용 | 로컬: 개발용"
        )
        
        st.markdown("---")
        
        if st.button("🔄 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.info("💡 자동 새로고침: 1시간마다")
        
        st.markdown("---")
        st.markdown("""
        ### 📌 정보
        - **업데이트**: 매일 오전 9시
        - **데이터**: 3일치 뉴스
        - **분석**: FinBERT + VADER
        """)
    
    # 데이터 로드
    if data_source == "GitHub":
        df_main, df_trend, sector_scores = load_data_from_github()
    else:
        df_main, df_trend, sector_scores = load_data_local()
    
    if df_main is None:
        st.warning("⚠️ 데이터를 찾을 수 없습니다.")
        st.info("""
        **GitHub 배포 시:**
        1. `data/Market_Monitor_latest.xlsx` 파일을 업로드하세요
        2. `app.py`의 `YOUR_USERNAME`을 실제 GitHub 사용자명으로 변경하세요
        
        **로컬 개발 시:**
        1. `python src/main.py`를 실행하여 데이터를 생성하세요
        """)
        return
    
    # 실제 뉴스만
    df_news = df_main[df_main['Title'].notna()].copy()
    
    st.success(f"✅ 데이터 로드 완료: {len(df_news)}개 뉴스 | 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "🏢 섹터 분석", "📈 차트", "📋 상세 데이터"])
    
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
                        card_class = "sector-positive"
                    elif weighted < -0.3:
                        card_class = "sector-negative"
                    else:
                        card_class = "sector-neutral"
                    
                    with cols[j]:
                        st.markdown(f"""
                        <div class="{card_class}">
                            <div style="font-size: 1.2em; font-weight: bold;">{info['etf']} | {sector}</div>
                            <div style="font-size: 0.9em; margin: 5px 0;">Simple: {info['simple']:.4f}</div>
                            <div style="font-size: 1.8em; font-weight: bold;">Weighted: {weighted:.4f}</div>
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
                <div class="metric-value" style="font-size: 1.5em;">{top_sector[:12]}</div>
                <div class="metric-label">최고 섹터</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ========== 탭 2: 섹터 분석 ==========
    with tab2:
        st.header("🏢 섹터별 상세 분석")
        
        # 섹터 선택
        selected_sector = st.selectbox(
            "섹터 선택",
            sorted(df_news['Sector'].unique()),
            key="sector_select"
        )
        
        sector_df = df_news[df_news['Sector'] == selected_sector]
        
        # 섹터 지표
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("뉴스 개수", len(sector_df))
        
        with col2:
            st.metric("평균 Sentiment", f"{sector_df['Sentiment'].mean():.4f}")
        
        with col3:
            pos_count = (sector_df['Sentiment'] > 0.2).sum()
            st.metric("긍정 뉴스", f"{pos_count}개 ({pos_count/len(sector_df)*100:.1f}%)")
        
        # 카테고리 분포
        st.subheader("카테고리별 분포")
        
        fig = px.pie(
            sector_df,
            names='Category',
            title=f"{selected_sector} 섹터 카테고리 분포"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 상위 종목
        st.subheader("주요 종목")
        
        top_companies = sector_df.groupby('Company')['Sentiment'].agg(['mean', 'count']).sort_values('count', ascending=False).head(10)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_companies.index,
            y=top_companies['count'],
            name='뉴스 개수',
            marker_color='lightblue'
        ))
        fig.add_trace(go.Scatter(
            x=top_companies.index,
            y=top_companies['mean'],
            name='평균 Sentiment',
            yaxis='y2',
            marker_color='red',
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title=f"{selected_sector} 상위 10개 종목",
            yaxis=dict(title='뉴스 개수'),
            yaxis2=dict(title='평균 Sentiment', overlaying='y', side='right'),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 최근 뉴스
        st.subheader("최근 뉴스")
        recent = sector_df.sort_values('Pub Date', ascending=False).head(10)
        
        for _, row in recent.iterrows():
            sentiment_color = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            
            st.markdown(f"""
            **{sentiment_color} {row['Company']} ({row['Ticker']})** - {row['Pub Date']}
            
            {row['Title']}
            
            *Sentiment: {row['Sentiment']:.4f} | Category: {row['Category']}*
            
            ---
            """)
    
    # ========== 탭 3: 차트 ==========
    with tab3:
        st.header("📈 시각화")
        
        # 필터
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sector_filter = st.multiselect(
                "섹터 필터",
                sorted(df_news['Sector'].unique()),
                default=sorted(df_news['Sector'].unique())
            )
        
        with col2:
            category_filter = st.multiselect(
                "카테고리 필터",
                sorted(df_news['Category'].unique()),
                default=sorted(df_news['Category'].unique())
            )
        
        with col3:
            sentiment_range = st.slider(
                "Sentiment 범위",
                -1.0, 1.0, (-1.0, 1.0), 0.1
            )
        
        # 필터 적용
        chart_df = df_news[
            (df_news['Sector'].isin(sector_filter)) &
            (df_news['Category'].isin(category_filter)) &
            (df_news['Sentiment'] >= sentiment_range[0]) &
            (df_news['Sentiment'] <= sentiment_range[1])
        ]
        
        st.info(f"📌 필터 결과: {len(chart_df)}개 뉴스")
        
        # 차트들
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("섹터별 평균 Sentiment")
            sector_avg = chart_df.groupby('Sector')['Sentiment'].mean().sort_values()
            
            fig = px.bar(
                x=sector_avg.values,
                y=sector_avg.index,
                orientation='h',
                color=sector_avg.values,
                color_continuous_scale=['red', 'yellow', 'green'],
                labels={'x': '평균 Sentiment', 'y': '섹터'}
            )
            fig.update_layout(showlegend=False, height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("섹터별 뉴스 개수")
            sector_count = chart_df['Sector'].value_counts().sort_values()
            
            fig = px.bar(
                x=sector_count.values,
                y=sector_count.index,
                orientation='h',
                labels={'x': '뉴스 개수', 'y': '섹터'},
                color_discrete_sequence=['#2196F3']
            )
            fig.update_layout(showlegend=False, height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Word Cloud
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("빈도 기반 Word Cloud")
            try:
                text = ' '.join(chart_df['Title'].dropna().astype(str))
                wc = WordCloud(width=800, height=400, background_color='white', max_words=100).generate(text)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.warning(f"Word Cloud 생성 실패: {e}")
        
        with col2:
            st.subheader("감성 기여도 Word Cloud")
            try:
                word_sent = {}
                for _, row in chart_df.iterrows():
                    for word in str(row['Title']).lower().split():
                        if len(word) > 3 and word.isalpha():
                            if word not in word_sent:
                                word_sent[word] = []
                            word_sent[word].append(abs(row['Sentiment']))
                
                contrib = {w: np.mean(s) * len(s) for w, s in word_sent.items() if len(s) >= 2}
                
                if contrib:
                    wc = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(contrib)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.warning("데이터 부족")
            except Exception as e:
                st.warning(f"Word Cloud 생성 실패: {e}")
        
        # 시계열
        if df_trend is not None and len(df_trend) > 0:
            st.subheader("상위 종목 Sentiment 추이")
            
            top_tickers = df_trend.nlargest(10, 'Today')
            
            fig = go.Figure()
            
            for _, row in top_tickers.iterrows():
                ticker = row['Ticker']
                values = []
                dates = []
                
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
                        line=dict(width=2)
                    ))
            
            fig.update_layout(
                title="상위 10개 종목 Sentiment 추이",
                xaxis_title="날짜",
                yaxis_title="Sentiment",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== 탭 4: 상세 데이터 ==========
    with tab4:
        st.header("📋 상세 뉴스 데이터")
        
        # 필터
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            table_sector = st.selectbox("섹터", ["전체"] + sorted(df_news['Sector'].unique()), key="table_sector")
        
        with col2:
            table_category = st.selectbox("카테고리", ["전체"] + sorted(df_news['Category'].unique()), key="table_cat")
        
        with col3:
            table_sentiment = st.selectbox("감성", ["전체", "긍정 (>0.2)", "중립", "부정 (<-0.2)"], key="table_sent")
        
        with col4:
            sort_by = st.selectbox("정렬", ["Pub Date", "Sentiment", "Weight (%)"], key="sort")
        
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
        
        st.info(f"📌 {len(table_df)}개 뉴스")
        
        # 테이블
        display_df = table_df[['ETF', 'Sector', 'Ticker', 'Company', 'Weight (%)', 
                                'Category', 'Title', 'URL', 'Pub Date', 'Sentiment']].copy()
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            column_config={
                "URL": st.column_config.LinkColumn("URL"),
                "Sentiment": st.column_config.NumberColumn("Sentiment", format="%.4f"),
                "Weight (%)": st.column_config.NumberColumn("Weight (%)", format="%.2f"),
            }
        )
        
        # 다운로드
        csv = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 CSV 다운로드",
            csv,
            f"market_monitor_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

if __name__ == "__main__":
    main()
