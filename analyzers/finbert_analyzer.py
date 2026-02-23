"""
FinBERT 감성 분석기 (본문 기반)
제목 + 본문 종합 분석
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from typing import Dict
import re

class FinBERTAnalyzer:
    """FinBERT 감성 분석 (본문 우선)"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipe = None
        self._initialize()
    
    def _initialize(self):
        """모델 초기화"""
        try:
            print("📊 FinBERT 모델 로드 중...")
            
            model_name = "ProsusAI/finbert"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.pipe = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1
            )
            
            print("✅ FinBERT 로드 완료")
            
        except Exception as e:
            print(f"⚠️ FinBERT 로드 실패: {e}")
            self.pipe = None
    
    def analyze(self, text: str) -> float:
        """텍스트 감성 분석"""
        if self.pipe is None:
            return 0.0
        
        try:
            # 전처리
            text = self._preprocess(text)
            
            if len(text) < 10:
                return 0.0
            
            # FinBERT는 최대 512 토큰
            # 본문이 길면 앞부분 우선 + 뒷부분 일부
            if len(text) > 1500:
                text = text[:1000] + " " + text[-500:]
            
            # 분석
            result = self.pipe(text[:512])[0]
            
            label = result['label']
            score = result['score']
            
            # 점수 변환
            if label == 'positive':
                return score
            elif label == 'negative':
                return -score
            else:
                return 0.0
                
        except Exception as e:
            print(f"  ⚠️ 분석 오류: {e}")
            return 0.0
    
    def analyze_comprehensive(self, title: str, content: str, summary: str = "") -> float:
        """종합 감성 분석 (본문 우선)"""
        
        # 우선순위: 본문 > 요약 > 제목
        if content and len(content) > 100:
            # 본문이 충분하면 본문 사용 (제목도 포함)
            text = f"{title}. {content}"
            return self.analyze(text)
        
        elif summary and len(summary) > 50:
            # 본문 없으면 요약 + 제목
            text = f"{title}. {summary}"
            return self.analyze(text)
        
        else:
            # 제목만
            return self.analyze(title)
    
    def _preprocess(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # URL 제거
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # 특수문자 정리
        text = re.sub(r'[^\w\s.,!?$%-]', '', text)
        
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def categorize(self, title: str) -> str:
        """뉴스 카테고리 분류"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ['earnings', 'revenue', 'profit', 'quarterly', 'eps', 'beat', 'miss']):
            return 'Earnings'
        elif any(w in title_lower for w in ['merger', 'acquisition', 'buyout', 'deal', 'acquire', 'purchase']):
            return 'M&A'
        elif any(w in title_lower for w in ['product', 'launch', 'release', 'unveil', 'announce']):
            return 'Product'
        elif any(w in title_lower for w in ['regulation', 'fda', 'sec', 'lawsuit', 'legal', 'court']):
            return 'Regulatory'
        elif any(w in title_lower for w in ['analyst', 'upgrade', 'downgrade', 'rating', 'target', 'recommendation']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: Dict) -> Dict:
        """뉴스 분석 (본문 기반)"""
        
        title = news.get('title', '')
        content = news.get('content', '')
        summary = news.get('summary', '')
        
        # 종합 감성 분석 (본문 우선)
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
            if (idx + 1) % 10 == 0 or idx == 0:
                print(f"  분석 중... {idx + 1}/{total}")
            
            analyzed_news = self.analyze_news(news)
            analyzed.append(analyzed_news)
        
        print(f"✅ {total}개 뉴스 분석 완료")
        
        return analyzed
