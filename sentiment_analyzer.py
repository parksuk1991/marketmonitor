"""
감성 분석기 - FinBERT + VADER 하이브리드
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict
import re

class SentimentAnalyzer:
    """FinBERT + VADER 하이브리드 감성 분석"""
    
    def __init__(self, use_finbert=True):
        self.use_finbert = use_finbert
        
        # VADER 초기화 (항상)
        self.vader = SentimentIntensityAnalyzer()
        
        # FinBERT 초기화 (옵션)
        if use_finbert:
            try:
                print("📊 FinBERT 모델 로드 중...")
                self.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
                self.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
                self.finbert_model.eval()
                print("✅ FinBERT 로드 완료")
            except Exception as e:
                print(f"⚠️ FinBERT 로드 실패, VADER만 사용: {e}")
                self.use_finbert = False
    
    def analyze_with_finbert(self, text: str) -> float:
        """FinBERT로 감성 분석"""
        try:
            # 텍스트 전처리
            text = self._preprocess_text(text)
            
            # 토큰화
            inputs = self.finbert_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # 예측
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT: [positive, negative, neutral]
            positive = predictions[0][0].item()
            negative = predictions[0][1].item()
            neutral = predictions[0][2].item()
            
            # 점수 계산 (-1 ~ 1)
            score = positive - negative
            
            return score
            
        except Exception as e:
            print(f"  ⚠️ FinBERT 분석 실패: {e}")
            return 0.0
    
    def analyze_with_vader(self, text: str) -> float:
        """VADER로 감성 분석"""
        try:
            # 텍스트 전처리
            text = self._preprocess_text(text)
            
            # VADER 분석
            scores = self.vader.polarity_scores(text)
            
            # compound 점수 사용 (-1 ~ 1)
            return scores['compound']
            
        except Exception as e:
            print(f"  ⚠️ VADER 분석 실패: {e}")
            return 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # URL 제거
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # 특수문자 정리
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def analyze_hybrid(self, text: str, finbert_weight=0.7) -> float:
        """하이브리드 감성 분석"""
        # VADER 점수
        vader_score = self.analyze_with_vader(text)
        
        # FinBERT 사용 가능하면 조합
        if self.use_finbert:
            finbert_score = self.analyze_with_finbert(text)
            
            # 가중 평균
            final_score = (finbert_score * finbert_weight + 
                          vader_score * (1 - finbert_weight))
        else:
            final_score = vader_score
        
        # -1 ~ 1 범위로 클리핑
        final_score = max(-1.0, min(1.0, final_score))
        
        return round(final_score, 4)
    
    def categorize_news(self, title: str) -> str:
        """뉴스 카테고리 분류"""
        title_lower = title.lower()
        
        # 키워드 기반 분류
        if any(word in title_lower for word in ['earnings', 'revenue', 'profit', 'quarterly', 'q1', 'q2', 'q3', 'q4']):
            return 'Earnings'
        elif any(word in title_lower for word in ['merger', 'acquisition', 'buyout', 'deal', 'acquire']):
            return 'M&A'
        elif any(word in title_lower for word in ['product', 'launch', 'release', 'innovation', 'unveil']):
            return 'Product'
        elif any(word in title_lower for word in ['regulation', 'fda', 'sec', 'lawsuit', 'legal', 'court']):
            return 'Regulatory'
        elif any(word in title_lower for word in ['analyst', 'upgrade', 'downgrade', 'rating', 'target']):
            return 'Analyst'
        else:
            return 'General'
    
    def analyze_news(self, news: Dict) -> Dict:
        """뉴스 분석 (감성 + 카테고리)"""
        # 제목 + 요약 결합
        text = news.get('title', '') + " " + news.get('summary', '')
        
        # 감성 분석
        sentiment = self.analyze_hybrid(text)
        
        # 카테고리 분류
        category = self.categorize_news(news.get('title', ''))
        
        # 결과 추가
        news['sentiment_score'] = sentiment
        news['category'] = category
        
        return news
    
    def batch_analyze(self, news_list: List[Dict]) -> List[Dict]:
        """뉴스 리스트 일괄 분석"""
        analyzed = []
        
        total = len(news_list)
        
        for idx, news in enumerate(news_list):
            if (idx + 1) % 10 == 0:
                print(f"  분석 중... {idx + 1}/{total}")
            
            analyzed_news = self.analyze_news(news)
            analyzed.append(analyzed_news)
        
        print(f"✅ {total}개 뉴스 분석 완료")
        
        return analyzed
