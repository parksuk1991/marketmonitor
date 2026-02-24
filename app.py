"""
ETF Holdings 감성분석 (독립 표시 버전)
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
    .etf-section {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
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
        print(f"\n🤖 감성 분석 (본문만)...")
        analyzer = load_analyzer()
        analyzed = analyzer.batch_analyze(all_news)
        
        return holdings, etf_name, sectors, analyzed, None
        
    except Exception as e:
        import traceback
        error = f"❌ {etf_ticker}: {e}\n{traceback.format_exc()}"
        print(error)
        return None, None, None, None, error

def run_multiple_etf(etf_list: list):
    """복수 ETF (독립 보관)"""
    results = {}
    
    for etf in etf_list:
        holdings, name, sectors, news, error = run_single_etf(etf)
        
        if error:
            st.warning(error)
            continue
        
        if holdings and news:
            # 각 ETF 데이터 독립 보관
            df_list = []
            for item in news:
                df_list.append({
                    'ETF': etf,
                    'Ticker': item.get('ticker', ''),
                    'Company': item.get('company_name', ''),
                    'Weight (%)': item.get('weight', 0.0),
                    'Category': item.get('category', 'General'),
                    'Title': item.get('title', ''),
                    'URL': item.get('url', ''),
                    'Pub Date': item.get('published_at', '')[:10],
                    'Highlights': item.get('highlights', ''),
                    'Sentiment': item.get('sentiment_score', 0.0),
                    'Source': item.get('source', 'Unknown')
                })
            
            results[etf] = {
                'name': name,
                'holdings': holdings,
                'sectors': sectors,
                'df': pd.DataFrame(df_list),
                'news_count': len(news)
            }
    
    return results

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">🚀 ETF Holdings 감성분석</h1>
        <p style="color: white; opacity: 0.9; margin-top: 10px;">
            복수 ETF 독립 분석 + 본문 감성 분석
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
        **주의:**
        - 각 ETF 독립 분석
        - 본문만 감성 분석
        - Yahoo + MarketWatch
        """)
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    if st.session_state.get('run_analysis', False):
        st.session_state.run_analysis = False
        
        etf_list = st.session_state.etf_list
        
        with st.spinner(f"{', '.join(etf_list)} 분석 중..."):
            results = run_multiple_etf(etf_list)
            
            if not results:
                st.error("❌ 모든 ETF 실패")
            else:
                st.session_state.results = results
                st.session_state.etf_list = etf_list
                
                total_news = sum(r['news_count'] for r in results.values())
                st.success(f"✅ {len(results)}개 ETF 완료! 총 {total_news}개 뉴스")
                st.balloons()
    
    if st.session_state.results is None:
        st.info("""
        ### 👋 시작하기
        
        1. ETF 입력: SPY 또는 SPY, QQQ
        2. "분석 시작" 클릭
        3. 각 ETF 독립 표시
        """)
        return
    
    results = st.session_state.results
    etf_list = st.session_state.etf_list
    
    # 각 ETF별 독립 표시
    for etf in etf_list:
        if etf not in results:
            continue
        
        data = results[etf]
        df = data['df']
        holdings = data['holdings']
        
        st.markdown(f"""
        <div class="etf-section">
            <h2>📊 {etf} - {data['name']}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 지표 (ETF별 독립)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div>뉴스</div></div>', unsafe_allow_html=True)
        
        with col2:
            avg = df['Sentiment'].mean()
            color = "#4CAF50" if avg > 0 else "#f44336"
            st.markdown(f'<div class="metric-card" style="background: {color};"><div class="metric-value">{avg:.3f}</div><div>평균</div></div>', unsafe_allow_html=True)
        
        with col3:
            pos = (df['Sentiment'] > 0.2).sum() / len(df) * 100
            st.markdown(f'<div class="metric-card" style="background: #f093fb;"><div class="metric-value">{pos:.1f}%</div><div>긍정</div></div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'<div class="metric-card" style="background: #4facfe;"><div class="metric-value">{len(holdings)}</div><div>종목</div></div>', unsafe_allow_html=True)
        
        # 탭 (ETF별)
        tab1, tab2, tab3 = st.tabs([f"{etf} 종목", f"{etf} Holdings", f"{etf} 뉴스"])
        
        with tab1:
            ticker_avg = df.groupby('Ticker')['Sentiment'].mean().sort_values().tail(10)
            colors = ['#f44336' if x < -0.2 else '#4CAF50' if x > 0.2 else '#FFC107' for x in ticker_avg]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(y=ticker_avg.index, x=ticker_avg.values, orientation='h',
                                 marker=dict(color=colors), text=[f"{v:.3f}" for v in ticker_avg.values], textposition='outside'))
            fig.update_layout(title=f"{etf} 종목별 Sentiment", height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Holdings: ticker, name, weight 순서
            holdings_df = pd.DataFrame(holdings)[['ticker', 'name', 'weight']]
            holdings_df.columns = ['Ticker', 'Name', 'Weight (%)']
            holdings_df.index = holdings_df.index + 1
            
            st.dataframe(holdings_df, use_container_width=True,
                        column_config={
                            "Weight (%)": st.column_config.NumberColumn(format="%.2f")
                        })
        
        with tab3:
            for _, row in df.head(20).iterrows():
                emoji = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
                
                with st.expander(f"{emoji} {row['Ticker']} - {row['Pub Date']}"):
                    st.markdown(f"### {row['Title']}")
                    st.markdown(f"**Highlights:** {row['Highlights']}")
                    st.markdown(f"**Sentiment:** {row['Sentiment']:.4f} | **Category:** {row['Category']}")
                    st.markdown(f"[원문]({row['URL']})")
        
        st.markdown("---")
    
    # 전체 다운로드
    if len(results) > 0:
        st.header("💾 전체 다운로드")
        
        # 전체 DataFrame 생성
        all_dfs = []
        for etf, data in results.items():
            all_dfs.append(data['df'])
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = combined_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv,
                             f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                             "text/csv", use_container_width=True)
        
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                combined_df.to_excel(writer, sheet_name='News', index=False)
                
                for etf, data in results.items():
                    holdings_df = pd.DataFrame(data['holdings'])[['ticker', 'name', 'weight']]
                    holdings_df.columns = ['Ticker', 'Name', 'Weight (%)']
                    holdings_df.to_excel(writer, sheet_name=f'{etf}_Holdings', index=False)
            
            st.download_button("📥 Excel", output.getvalue(),
                             f"market_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             use_container_width=True)

if __name__ == "__main__":
    main()
