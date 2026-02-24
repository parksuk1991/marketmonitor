"""
뉴스 수집기 (본문 검증 버전)
본문 없는 기사 제외 + Paywall 감지
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import re

class NewsCollector:
    """뉴스 수집기 (본문 필수)"""
    
    def __init__(self, days=3):
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Paywall 감지 키워드
        self.paywall_keywords = [
            'sign in', 'log in', 'subscribe', 'subscription',
            'register', 'premium', 'member only', 'subscribers only',
            'create account', 'google sign', 'login required'
        ]
    
    def is_paywall(self, content: str, url: str) -> bool:
        """Paywall 또는 로그인 필요 감지"""
        if not content or len(content) < 100:
            return True
        
        content_lower = content.lower()
        
        # Paywall 키워드 확인
        for keyword in self.paywall_keywords:
            if keyword in content_lower:
                print(f"      ⚠️ Paywall 감지: {keyword}")
                return True
        
        return False
    
    def extract_full_content(self, url: str) -> tuple:
        """
        본문 전체 추출 + 검증
        
        Returns:
            (content, is_valid)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return "", False
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                tag.decompose()
            
            # article 태그 우선
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
            else:
                paragraphs = soup.find_all('p')
            
            # 모든 p 태그 수집
            texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30:
                    texts.append(text)
            
            full_text = ' '.join(texts)
            
            # Paywall 체크
            if self.is_paywall(full_text, url):
                return "", False
            
            # 본문 길이 체크 (최소 200자)
            if len(full_text) < 200:
                print(f"      ⚠️ 본문 너무 짧음: {len(full_text)}자")
                return "", False
            
            # 최대 10,000자
            return full_text[:10000], True
            
        except Exception as e:
            print(f"      본문 추출 실패: {e}")
            return "", False
    
    def summarize_with_llm(self, text: str) -> str:
        """
        무료 LLM으로 본문 요약
        Hugging Face Inference API 사용
        """
        try:
            from transformers import pipeline
            
            # 요약 모델 로드 (캐시됨)
            if not hasattr(self, 'summarizer'):
                print("      📝 요약 모델 로드 중...")
                self.summarizer = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    device=-1
                )
            
            # 텍스트가 너무 길면 앞부분만
            if len(text) > 2000:
                text = text[:2000]
            
            # 요약 생성
            summary = self.summarizer(
                text,
                max_length=150,
                min_length=50,
                do_sample=False
            )
            
            return summary[0]['summary_text']
            
        except Exception as e:
            print(f"      ⚠️ LLM 요약 실패: {e}")
            # Fallback: 처음 3-4문장
            return self.create_manual_summary(text)
    
    def create_manual_summary(self, text: str) -> str:
        """Fallback 수동 요약 (LLM 실패 시)"""
        if not text or len(text) < 20:
            return ""
        
        sentences = re.split(r'[.!?]\s+', text)
        result = []
        
        for sentence in sentences[:4]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                result.append(sentence)
        
        summary = '. '.join(result)
        
        if len(summary) > 500:
            summary = summary[:500] + '...'
        
        return summary if summary else text[:500] + '...'
    
    def collect_yahoo_rss(self, ticker: str) -> List[Dict]:
        """Yahoo Finance RSS"""
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            feed = feedparser.parse(url)
            
            news = []
            for entry in feed.entries[:5]:
                try:
                    pub_date = entry.get('published_parsed')
                    if pub_date:
                        pub_dt = datetime(*pub_date[:6])
                        if pub_dt < self.cutoff_date:
                            continue
                        date_str = pub_dt.strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    title = entry.get('title', '')
                    article_url = entry.get('link', '')
                    
                    # 본문 추출 + 검증
                    content, is_valid = self.extract_full_content(article_url)
                    
                    # 본문 없으면 건너뛰기
                    if not is_valid or not content:
                        print(f"      ❌ 본문 없음, 제외")
                        continue
                    
                    # LLM 요약
                    highlights = self.summarize_with_llm(content)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': entry.get('summary', ''),
                        'content': content,
                        'highlights': highlights,
                        'source': 'Yahoo Finance',
                        'has_content': True
                    })
                    
                    print(f"      ✅ 본문 {len(content)}자, 요약 {len(highlights)}자")
                    
                except Exception as e:
                    print(f"      오류: {e}")
                    continue
            
            return news
        except Exception as e:
            print(f"    Yahoo RSS 오류: {e}")
            return []
    
    def collect_marketwatch(self, ticker: str) -> List[Dict]:
        """MarketWatch"""
        try:
            url = f"https://www.marketwatch.com/search?q={ticker}&ts=0&tab=All%20News"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news = []
            articles = soup.find_all('div', class_='article__content', limit=3)
            
            for article in articles:
                try:
                    title_elem = article.find('a', class_='link')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    article_url = title_elem.get('href', '')
                    
                    if not article_url.startswith('http'):
                        article_url = f"https://www.marketwatch.com{article_url}"
                    
                    # 본문 추출 + 검증
                    content, is_valid = self.extract_full_content(article_url)
                    
                    if not is_valid or not content:
                        print(f"      ❌ 본문 없음, 제외")
                        continue
                    
                    # LLM 요약
                    highlights = self.summarize_with_llm(content)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': datetime.now().strftime('%Y-%m-%d'),
                        'summary': title,
                        'content': content,
                        'highlights': highlights,
                        'source': 'MarketWatch',
                        'has_content': True
                    })
                    
                    print(f"      ✅ 본문 {len(content)}자, 요약 {len(highlights)}자")
                    
                except Exception as e:
                    print(f"      오류: {e}")
                    continue
            
            return news
        except Exception as e:
            print(f"    MarketWatch 오류: {e}")
            return []
    
    def collect_for_ticker(self, ticker: str, company: str) -> List[Dict]:
        """티커별 뉴스 수집 (본문 있는 것만)"""
        all_news = []
        
        print(f"    Yahoo Finance...")
        yahoo_news = self.collect_yahoo_rss(ticker)
        all_news.extend(yahoo_news)
        
        print(f"    MarketWatch...")
        mw_news = self.collect_marketwatch(ticker)
        all_news.extend(mw_news)
        
        # 회사명 추가
        for item in all_news:
            item['company_name'] = company
        
        # 중복 제거
        seen = set()
        unique = []
        for item in all_news:
            url = item.get('url', '')
            if url and url not in seen:
                seen.add(url)
                unique.append(item)
        
        return unique
    
    def collect_all(self, holdings: List[Dict], etf_ticker: str) -> List[Dict]:
        """전체 수집 (본문 있는 것만)"""
        all_news = []
        
        for idx, holding in enumerate(holdings):
            ticker = holding['ticker']
            company = holding['name']
            
            print(f"  [{idx+1}/{len(holdings)}] {ticker} ({company})")
            
            news = self.collect_for_ticker(ticker, company)
            
            for item in news:
                item['etf'] = etf_ticker
                item['weight'] = holding['weight']
            
            all_news.extend(news)
            time.sleep(0.5)
        
        # 본문 있는 뉴스만 필터링
        valid_news = [n for n in all_news if n.get('has_content', False)]
        
        print(f"✅ {etf_ticker}: {len(valid_news)}개 뉴스 (본문 있음)")
        
        return valid_news
