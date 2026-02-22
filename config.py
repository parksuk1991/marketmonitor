"""
설정 파일
"""
from pathlib import Path
import os

class Config:
    # 프로젝트 루트
    BASE_DIR = Path(__file__).parent.parent
    
    # 데이터 디렉토리
    DATA_DIR = BASE_DIR / "data"
    REPORT_DIR = DATA_DIR / "reports"
    
    # API 키 (환경 변수에서 로드)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # 섹터 ETF 목록
    SECTOR_ETFS = {
        'XLK': 'Technology',
        'XLF': 'Financials',
        'XLV': 'Health Care',
        'XLY': 'Consumer Discretionary',
        'XLE': 'Energy',
        'XLI': 'Industrials',
        'XLP': 'Consumer Staples',
        'XLC': 'Communication Services',
        'XLRE': 'Real Estate',
        'XLB': 'Materials',
        'XLU': 'Utilities'
    }
    
    # RSS 피드
    RSS_FEEDS = {
        'yahoo_finance': 'https://finance.yahoo.com/rss/',
        'motley_fool': 'https://www.fool.com/feeds/index.aspx',
        'marketwatch': 'https://www.marketwatch.com/rss/'
    }
    
    # 감성 분석 설정
    SENTIMENT_THRESHOLD_POSITIVE = 0.2
    SENTIMENT_THRESHOLD_NEGATIVE = -0.2
    
    # 뉴스 수집 설정
    NEWS_DAYS = 3  # 최근 3일
    MAX_NEWS_PER_TICKER = 10
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.REPORT_DIR.mkdir(exist_ok=True)
