"""
FinBERT 감성 분석기
Streamlit 환경 최적화
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from typing import Dict
import re

class FinBERTAnalyzer:
    """FinBERT 감성 분석"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipe = None
        self._initialize()
    
    def _initialize(self):
        """모델 초기화"""
        try:
            print("📊 FinBERT 모델 로드 중...")
            
            # FinBERT 모델
            model_name = "ProsusAI/finbert"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Pipeline 생성
            self.pipe = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1  # CPU 사용
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
            # 텍스트 전처리
            text = self._preprocess(text)
            
            if len(text) < 10:
                return 0.0
            
            # FinBERT 분석
            result = self.pipe(text[:512])[0]  # 최대 512 토큰
            
            label = result['label']
            score = result['score']
            
            # 점수 변환 (-1 ~ 1)
            if label == 'positive':
                return score
            elif label == 'negative':
                return -score
            else:  # neutral
                return 0.0
                
        except Exception as e:
            print(f"  ⚠️ 분석 오류: {e}")
            return 0.0
    
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
        
        # 키워드 기반
        if any(w in title_lower for w in ['earnings', 'revenue', 'profit', 'quarterly', 'eps']):
            return 'Earnings'
        elif any(w in title_lower for w in ['merger', 'acquisition', 'buyout', 'deal']):
            return 'M&A'
        elif any(w in title_lower for w in ['product', 'launch', 'release', 'unveil']):
            return 'Product'
        elif any(w in title_lower for w in ['regulation', 'fda', 'sec', 'lawsuit']):
            return 'Regulatory'
        elif any(w in title_lower for w in ['analyst', 'upgrade', 'downgrade', 'rating']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: Dict) -> Dict:
        """뉴스 분석"""
        # 제목 + 요약
        text = news.get('title', '') + " " + news.get('summary', '')
        
        # 감성 분석
        sentiment = self.analyze(text)
        
        # 카테고리
        category = self.categorize(news.get('title', ''))
        
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
