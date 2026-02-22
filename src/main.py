"""
메인 실행 파일 - 전체 파이프라인
"""
from datetime import datetime
from pathlib import Path
import sys

# 프로젝트 루트 추가
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.config import Config
from collectors.sector_collector import SectorETFCollector
from collectors.news_collector import NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from reporters.excel_generator_sector import SectorETFExcelGenerator

def run_pipeline():
    """전체 파이프라인 실행"""
    
    print("\n" + "="*70)
    print("섹터 ETF 감성분석 시스템")
    print("="*70)
    
    # 디렉토리 생성
    Config.ensure_directories()
    
    # 1. Holdings 수집
    print("\n[1/4] 섹터 ETF Holdings 수집...")
    sector_collector = SectorETFCollector()
    sector_holdings = sector_collector.collect_all_sector_holdings(top_n=5)
    portfolio = sector_collector.get_portfolio_for_news(sector_holdings)
    print(f"✅ {len(portfolio)}개 종목")
    
    # 2. 뉴스 수집
    print("\n[2/4] 뉴스 수집...")
    news_collector = NewsCollector(days=Config.NEWS_DAYS)
    all_news = news_collector.collect_all_news(portfolio)
    print(f"✅ {len(all_news)}개 뉴스")
    
    # 3. 감성 분석
    print("\n[3/4] 감성 분석...")
    analyzer = SentimentAnalyzer(use_finbert=False)  # Streamlit에서는 VADER만
    analyzed_news = analyzer.batch_analyze(all_news)
    print(f"✅ {len(analyzed_news)}개 분석 완료")
    
    # 4. 엑셀 생성
    print("\n[4/4] 엑셀 리포트 생성...")
    generator = SectorETFExcelGenerator(Config.REPORT_DIR)
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = generator.generate_sector_report(
        analyzed_news,
        sector_holdings,
        today
    )
    
    print("\n" + "="*70)
    print("✅ 완료!")
    print(f"✅ 리포트: {report_path}")
    print("="*70 + "\n")
    
    return report_path, analyzed_news, sector_holdings

if __name__ == "__main__":
    run_pipeline()
