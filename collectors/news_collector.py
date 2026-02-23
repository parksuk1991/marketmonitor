"""
뉴스 수집기 (검증된 버전)
본문 추출 + Highlights 생성
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import re

class NewsCollector:
    """뉴스 수집 + 본문 추출"""
    
    def __init__(self, days=3):
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def extract_content(self, url: str) -> str:
        """본문 추출 (간단 버전)"""
        try:
            response = requests.get(url, headers=self.headers, timeout=8)
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 본문 찾기
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # p 태그들 수집
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
            
            if text:
                return text[:2000]  # 최대 2000자
            
            return ""
        except:
            return ""
    
    def create_highlights(self, text: str) -> str:
        """Highlights 생성 (200자)"""
        if not text or len(text) < 20:
            return ""
        
        # 문장 단위 분리
        sentences = re.split(r'[.!?]\s+', text)
        
        result = []
        total_len = 0
        
        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                result.append(sentence)
                total_len += len(sentence)
                if total_len >= 200:
                    break
        
        highlights = '. '.join(result)
        
        if len(highlights) > 200:
            highlights = highlights[:200] + '...'
        
        return highlights if highlights else text[:200] + '...'
    
    def collect_yahoo_rss(self, ticker: str) -> List[Dict]:
        """Yahoo Finance RSS"""
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            feed = feedparser.parse(url)
            
            news = []
            for entry in feed.entries[:5]:
                try:
                    # 날짜 파싱
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
                    
                    # Highlights
                    if content:
                        highlights = self.create_highlights(content)
                    elif summary:
                        highlights = self.create_highlights(summary)
                    else:
                        highlights = title[:200] if len(title) > 200 else title
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary[:500] if summary else "",
                        'content': content,
                        'highlights': highlights,
                        'source': 'Yahoo Finance'
                    })
                    
                except Exception as e:
                    print(f"  ⚠️ Entry 처리 오류: {e}")
                    continue
            
            return news
            
        except Exception as e:
            print(f"  ⚠️ Yahoo RSS 오류: {e}")
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
                    
                    content = self.extract_content(article_url)
                    highlights = self.create_highlights(content if content else title)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': datetime.now().strftime('%Y-%m-%d'),
                        'summary': title,
                        'content': content,
                        'highlights': highlights,
                        'source': 'MarketWatch'
                    })
                    
                except:
                    continue
            
            return news
            
        except:
            return []
    
    def collect_for_ticker(self, ticker: str, company: str) -> List[Dict]:
        """티커별 뉴스 수집"""
        all_news = []
        
        # Yahoo Finance (주요 소스)
        yahoo_news = self.collect_yahoo_rss(ticker)
        all_news.extend(yahoo_news)
        
        # MarketWatch
        if len(all_news) < 3:
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
