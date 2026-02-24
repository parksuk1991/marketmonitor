"""
FinBERT 분석기 (경량 버전)
메모리 최적화
"""
from transformers import pipeline
import re

class FinBERTAnalyzer:
    """경량 FinBERT"""
    
    def __init__(self):
        self.pipe = None
        self._initialize()
    
    def _initialize(self):
        """모델 로드 (한 번만)"""
        try:
            print("📊 FinBERT 로드 중...")
            self.pipe = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                device=-1,
                max_length=512,
                truncation=True
            )
            print("✅ FinBERT 로드 완료")
        except Exception as e:
            print(f"⚠️ FinBERT 로드 실패: {e}")
            self.pipe = None
    
    def analyze_chunk(self, text: str) -> float:
        """단일 청크 분석"""
        if not self.pipe or not text or len(text) < 10:
            return 0.0
        
        try:
            # 전처리
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 분석 (512자로 제한)
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
    
    def analyze_text(self, text: str) -> float:
        """
        텍스트 분석 (최대 3개 청크)
        """
        if not text or len(text) < 100:
            return 0.0
        
        # 청크 크기 (1000자)
        chunk_size = 1000
        
        # 최대 3개 청크만
        chunks = []
        for i in range(0, min(len(text), 3000), chunk_size):
            chunk = text[i:i+chunk_size]
            if len(chunk) > 100:
                chunks.append(chunk)
        
        # 각 청크 분석
        scores = []
        for chunk in chunks[:3]:  # 최대 3개
            score = self.analyze_chunk(chunk)
            if score != 0.0:
                scores.append(score)
        
        if scores:
            return sum(scores) / len(scores)
        
        return 0.0
    
    def categorize(self, title: str) -> str:
        """카테고리"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ['earnings', 'revenue', 'profit']):
            return 'Earnings'
        elif any(w in title_lower for w in ['merger', 'acquisition', 'deal']):
            return 'M&A'
        elif any(w in title_lower for w in ['product', 'launch']):
            return 'Product'
        elif any(w in title_lower for w in ['regulation', 'lawsuit']):
            return 'Regulatory'
        elif any(w in title_lower for w in ['analyst', 'upgrade', 'downgrade']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: dict) -> dict:
        """뉴스 분석"""
        content = news.get('content', '')
        
        # 본문 있는지 체크
        if not content or len(content) < 100:
            return None
        
        # 본문 분석
        sentiment = self.analyze_text(content)
        
        news['sentiment_score'] = round(sentiment, 4)
        news['category'] = self.categorize(news.get('title', ''))
        
        return news
    
    def batch_analyze(self, news_list: list) -> list:
        """일괄 분석"""
        analyzed = []
        
        for idx, news in enumerate(news_list):
            if (idx + 1) % 5 == 0:
                print(f"  분석: {idx + 1}/{len(news_list)}")
            
            result = self.analyze_news(news)
            if result:
                analyzed.append(result)
        
        print(f"✅ {len(analyzed)}개 분석 완료")
        return analyzed
