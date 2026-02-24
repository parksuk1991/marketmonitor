"""
FinBERT 감성 분석기 (본문 전체 분석)
512자 제한 제거, 청크 방식 처리
"""
from transformers import pipeline
import re

class FinBERTAnalyzer:
    """FinBERT 감성 분석 (본문 전체)"""
    
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
        """단일 청크 분석 (최대 512 토큰)"""
        if not self.pipe or not text or len(text) < 10:
            return 0.0
        
        try:
            # 전처리
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 분석 (512 토큰 제한)
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
        """
        본문 전체 분석 (청크로 나눠서 평균)
        
        현재 상황:
        - FinBERT는 최대 512 토큰만 처리 가능
        - 본문이 길면 여러 청크로 나눠서 분석 후 평균
        """
        if not text or len(text) < 10:
            return 0.0
        
        # 청크 크기 (약 400자 = 약 100 토큰)
        chunk_size = 1500  # 약 400 토큰 (여유있게)
        
        # 문장 단위로 분리
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
        
        # 마지막 청크
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        # 각 청크 분석
        scores = []
        for chunk in chunks[:5]:  # 최대 5개 청크 (너무 많으면 시간 오래 걸림)
            score = self.analyze_chunk(chunk)
            scores.append(score)
        
        # 평균 점수
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"      본문 분석: {len(chunks)}개 청크, 평균 {avg_score:.4f}")
            return avg_score
        
        return 0.0
    
    def analyze_article(self, title: str, content: str, summary: str = "") -> float:
        """
        기사 감성 분석 (본문 전체 사용)
        
        우선순위: 본문 전체 > 요약 전체 > 제목
        """
        # 1. 본문 전체 분석
        if content and len(content) > 100:
            return self.analyze_full_text(content)
        
        # 2. 요약 분석
        elif summary and len(summary) > 50:
            return self.analyze_full_text(summary)
        
        # 3. 제목만
        else:
            return self.analyze_chunk(title)
    
    def categorize(self, title: str) -> str:
        """카테고리 분류"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ['earnings', 'revenue', 'profit', 'eps', 'quarterly', 'q1', 'q2', 'q3', 'q4']):
            return 'Earnings'
        elif any(w in title_lower for w in ['merger', 'acquisition', 'deal', 'buyout', 'acquire']):
            return 'M&A'
        elif any(w in title_lower for w in ['product', 'launch', 'release', 'unveil', 'announce']):
            return 'Product'
        elif any(w in title_lower for w in ['regulation', 'lawsuit', 'legal', 'fda', 'sec', 'court']):
            return 'Regulatory'
        elif any(w in title_lower for w in ['analyst', 'upgrade', 'downgrade', 'rating', 'target']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: dict) -> dict:
        """뉴스 분석"""
        title = news.get('title', '')
        content = news.get('content', '')
        summary = news.get('summary', '')
        
        print(f"    감성 분석 중... (본문 {len(content)}자)")
        
        # 본문 전체 감성 분석
        sentiment = self.analyze_article(title, content, summary)
        category = self.categorize(title)
        
        news['sentiment_score'] = round(sentiment, 4)
        news['category'] = category
        
        return news
    
    def batch_analyze(self, news_list: list) -> list:
        """일괄 분석"""
        analyzed = []
        total = len(news_list)
        
        print(f"\n🤖 감성 분석 시작 (본문 전체)")
        
        for idx, news in enumerate(news_list):
            print(f"  [{idx + 1}/{total}] {news.get('ticker', '')}...")
            
            analyzed_news = self.analyze_news(news)
            analyzed.append(analyzed_news)
        
        print(f"✅ {total}개 뉴스 분석 완료 (본문 전체)")
        return analyzed
