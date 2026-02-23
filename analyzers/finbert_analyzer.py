"""
FinBERT 감성 분석기 (본문 우선)
"""
from transformers import pipeline
import re

class FinBERTAnalyzer:
    """FinBERT 감성 분석"""
    
    def __init__(self):
        self.pipe = None
        self._initialize()
    
    def _initialize(self):
        """모델 로드"""
        try:
            print("📊 FinBERT 로드 중...")
            self.pipe = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                device=-1
            )
            print("✅ FinBERT 로드 완료")
        except Exception as e:
            print(f"⚠️ FinBERT 로드 실패: {e}")
            self.pipe = None
    
    def analyze(self, text: str) -> float:
        """감성 분석"""
        if not self.pipe or not text or len(text) < 10:
            return 0.0
        
        try:
            # 전처리
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 분석 (최대 512 토큰)
            result = self.pipe(text[:512])[0]
            
            label = result['label']
            score = result['score']
            
            if label == 'positive':
                return score
            elif label == 'negative':
                return -score
            else:
                return 0.0
        except:
            return 0.0
    
    def analyze_comprehensive(self, title: str, content: str, summary: str = "") -> float:
        """종합 분석 (본문 우선)"""
        # 본문 > 요약 > 제목
        if content and len(content) > 100:
            text = f"{title}. {content}"
            return self.analyze(text)
        elif summary and len(summary) > 50:
            text = f"{title}. {summary}"
            return self.analyze(text)
        else:
            return self.analyze(title)
    
    def categorize(self, title: str) -> str:
        """카테고리 분류"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ['earnings', 'revenue', 'profit', 'eps']):
            return 'Earnings'
        elif any(w in title_lower for w in ['merger', 'acquisition', 'deal']):
            return 'M&A'
        elif any(w in title_lower for w in ['product', 'launch', 'release']):
            return 'Product'
        elif any(w in title_lower for w in ['regulation', 'lawsuit', 'legal']):
            return 'Regulatory'
        elif any(w in title_lower for w in ['analyst', 'upgrade', 'downgrade']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: dict) -> dict:
        """뉴스 분석"""
        title = news.get('title', '')
        content = news.get('content', '')
        summary = news.get('summary', '')
        
        # 본문 기반 감성 분석
        sentiment = self.analyze_comprehensive(title, content, summary)
        
        # 카테고리
        category = self.categorize(title)
        
        news['sentiment_score'] = round(sentiment, 4)
        news['category'] = category
        
        return news
    
    def batch_analyze(self, news_list: list) -> list:
        """일괄 분석"""
        analyzed = []
        total = len(news_list)
        
        for idx, news in enumerate(news_list):
            if (idx + 1) % 10 == 0:
                print(f"  분석: {idx + 1}/{total}")
            
            analyzed.append(self.analyze_news(news))
        
        print(f"✅ {total}개 분석 완료")
        return analyzed
