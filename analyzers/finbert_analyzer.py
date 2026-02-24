"""
FinBERT 분석기 (본문 전체 필수)
본문 없으면 분석 안 함
"""
from transformers import pipeline
import re

class FinBERTAnalyzer:
    """FinBERT 감성 분석 (본문 필수)"""
    
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
    
    def analyze_chunk(self, text: str) -> float:
        """단일 청크 분석"""
        if not self.pipe or not text or len(text) < 10:
            return 0.0
        
        try:
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
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
    
    def analyze_full_text(self, text: str) -> float:
        """본문 전체 분석 (청크 방식)"""
        if not text or len(text) < 100:
            return None  # 본문 없으면 None 반환
        
        # 청크로 분리
        chunk_size = 1500
        sentences = re.split(r'[.!?]\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_length + len(sentence) < chunk_size:
                current_chunk.append(sentence)
                current_length += len(sentence)
            else:
                if current_chunk:
                    chunks.append('. '.join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
        
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        # 각 청크 분석
        scores = []
        for chunk in chunks[:5]:
            score = self.analyze_chunk(chunk)
            if score != 0.0:  # 0이 아닌 점수만
                scores.append(score)
        
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"      감성: {len(chunks)}개 청크, 평균 {avg_score:.4f}")
            return avg_score
        
        return 0.0
    
    def analyze_article(self, content: str) -> float:
        """
        기사 감성 분석 (본문 필수)
        
        본문이 없으면 None 반환 → 분석 제외
        """
        if not content or len(content) < 100:
            return None  # 본문 없으면 분석 안 함
        
        return self.analyze_full_text(content)
    
    def categorize(self, title: str) -> str:
        """카테고리 분류"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ['earnings', 'revenue', 'profit', 'eps', 'quarterly']):
            return 'Earnings'
        elif any(w in title_lower for w in ['merger', 'acquisition', 'deal', 'buyout']):
            return 'M&A'
        elif any(w in title_lower for w in ['product', 'launch', 'release', 'unveil']):
            return 'Product'
        elif any(w in title_lower for w in ['regulation', 'lawsuit', 'legal', 'fda', 'sec']):
            return 'Regulatory'
        elif any(w in title_lower for w in ['analyst', 'upgrade', 'downgrade', 'rating']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: dict) -> dict:
        """뉴스 분석 (본문 필수)"""
        title = news.get('title', '')
        content = news.get('content', '')
        
        # 본문 검증
        if not content or len(content) < 100:
            print(f"      ❌ 본문 없음, 분석 제외")
            news['sentiment_score'] = None
            news['category'] = 'Invalid'
            news['analyzed'] = False
            return news
        
        print(f"      분석 중... (본문 {len(content)}자)")
        
        # 본문 전체 감성 분석
        sentiment = self.analyze_article(content)
        
        if sentiment is None:
            print(f"      ❌ 분석 실패")
            news['sentiment_score'] = None
            news['category'] = 'Invalid'
            news['analyzed'] = False
        else:
            news['sentiment_score'] = round(sentiment, 4)
            news['category'] = self.categorize(title)
            news['analyzed'] = True
        
        return news
    
    def batch_analyze(self, news_list: list) -> list:
        """일괄 분석 (본문 있는 것만)"""
        analyzed = []
        total = len(news_list)
        
        print(f"\n🤖 감성 분석 시작 (본문 필수)")
        
        for idx, news in enumerate(news_list):
            print(f"  [{idx + 1}/{total}] {news.get('ticker', '')}...")
            
            analyzed_news = self.analyze_news(news)
            
            # 분석된 것만 추가
            if analyzed_news.get('analyzed', False):
                analyzed.append(analyzed_news)
        
        print(f"✅ {len(analyzed)}/{total}개 분석 완료 (본문 기반)")
        
        return analyzed
