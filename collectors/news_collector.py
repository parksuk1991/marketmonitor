"""
뉴스 수집기 (경량 버전)
LLM 없이 추출식 요약
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import re

class NewsCollector:
    """경량 뉴스 수집기"""
    
    def __init__(self, days=3):
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_content(self, url: str) -> str:
        """본문 추출 (간단 버전)"""
        try:
            response = requests.get(url, headers=self.headers, timeout=8)
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # p 태그 수집
            paragraphs = soup.find_all('p')
            texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
            
            full_text = ' '.join(texts)
            
            # 최대 5000자 (메모리 절약)
            return full_text[:5000] if full_text else ""
        except:
            return ""
    
    def is_valid_content(self, content: str) -> bool:
        """본문 유효성 체크"""
        if not content or len(content) < 200:
            return False
        
        # Paywall 키워드
        paywall_words = ['sign in', 'log in', 'subscribe', 'register']
        content_lower = content.lower()
        
        for word in paywall_words:
            if word in content_lower[:500]:  # 앞부분만 체크
                return False
        
        return True
    
    def create_extractive_summary(self, text: str) -> str:
        """추출식 요약 (LLM 없이)"""
        if not text or len(text) < 20:
            return ""
        
        # 문장 분리
        sentences = re.split(r'[.!?]\s+', text)
        
        # 처음 3-4문장 (약 300자)
        summary_sentences = []
        total_len = 0
        
        for sentence in sentences[:5]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                summary_sentences.append(sentence)
                total_len += len(sentence)
                
                if total_len >= 300:
                    break
        
        summary = '. '.join(summary_sentences)
        
        # 300자 제한
        if len(summary) > 300:
            summary = summary[:300] + '...'
        
        return summary if summary else text[:300] + '...'
    
    def collect_yahoo_rss(self, ticker: str) -> List[Dict]:
        """Yahoo Finance RSS"""
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            feed = feedparser.parse(url)
            
            news = []
            for entry in feed.entries[:3]:  # 3개로 제한
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
                    summary = entry.get('summary', '')
                    
                    # 본문 추출
                    content = self.extract_content(article_url)
                    
                    # 유효성 체크
                    if not self.is_valid_content(content):
                        continue
                    
                    # 추출식 요약
                    highlights = self.create_extractive_summary(content)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary[:300],
                        'content': content,
                        'highlights': highlights,
                        'source': 'Yahoo Finance'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_for_ticker(self, ticker: str, company: str) -> List[Dict]:
        """티커별 뉴스 (Yahoo만)"""
        all_news = []
        
        # Yahoo Finance만 사용 (가장 안정적)
        yahoo_news = self.collect_yahoo_rss(ticker)
        all_news.extend(yahoo_news)
        
        # 회사명 추가
        for item in all_news:
            item['company_name'] = company
        
        return all_news
    
    def collect_all(self, holdings: List[Dict], etf_ticker: str) -> List[Dict]:
        """전체 수집"""
        all_news = []
        
        for idx, holding in enumerate(holdings):
            ticker = holding['ticker']
            company = holding['name']
            
            print(f"  [{idx+1}/{len(holdings)}] {ticker}...")
            
            news = self.collect_for_ticker(ticker, company)
            
            for item in news:
                item['etf'] = etf_ticker
                item['weight'] = holding['weight']
            
            all_news.extend(news)
            time.sleep(0.3)
        
        print(f"✅ {etf_ticker}: {len(all_news)}개 뉴스")
        return all_news
