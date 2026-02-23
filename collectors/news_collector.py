"""
뉴스 수집기 (모든 소스 포함)
Yahoo Finance, MarketWatch, Motley Fool, Seeking Alpha
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import re

class NewsCollector:
    """다중 소스 뉴스 수집기"""
    
    def __init__(self, days=3):
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
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
                    
                    news.append({
                        'ticker': ticker,
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'published_at': date_str,
                        'summary': entry.get('summary', '')[:200],
                        'source': 'Yahoo Finance'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_marketwatch(self, ticker: str) -> List[Dict]:
        """MarketWatch 검색"""
        try:
            search_url = f"https://www.marketwatch.com/search?q={ticker}&ts=0&tab=All%20News"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
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
                    url = title_elem.get('href', '')
                    
                    if not url.startswith('http'):
                        url = f"https://www.marketwatch.com{url}"
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': url,
                        'published_at': datetime.now().strftime('%Y-%m-%d'),
                        'summary': title[:200],
                        'source': 'MarketWatch'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_motley_fool(self, ticker: str) -> List[Dict]:
        """Motley Fool 검색"""
        try:
            search_url = f"https://www.fool.com/search/?q={ticker}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news = []
            articles = soup.find_all('article', limit=3)
            
            for article in articles[:3]:
                try:
                    title_elem = article.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    if url and not url.startswith('http'):
                        url = f"https://www.fool.com{url}"
                    
                    if title and url:
                        news.append({
                            'ticker': ticker,
                            'title': title,
                            'url': url,
                            'published_at': datetime.now().strftime('%Y-%m-%d'),
                            'summary': title[:200],
                            'source': 'Motley Fool'
                        })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_seeking_alpha(self, ticker: str) -> List[Dict]:
        """Seeking Alpha 뉴스"""
        try:
            # Seeking Alpha RSS (public)
            url = f"https://seekingalpha.com/api/sa/combined/{ticker}.xml"
            feed = feedparser.parse(url)
            
            news = []
            for entry in feed.entries[:3]:
                try:
                    pub_date = entry.get('published_parsed')
                    if pub_date:
                        pub_dt = datetime(*pub_date[:6])
                        if pub_dt < self.cutoff_date:
                            continue
                        date_str = pub_dt.strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    news.append({
                        'ticker': ticker,
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'published_at': date_str,
                        'summary': entry.get('summary', '')[:200],
                        'source': 'Seeking Alpha'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_benzinga_rss(self, ticker: str) -> List[Dict]:
        """Benzinga RSS"""
        try:
            url = f"https://www.benzinga.com/feed/stock/{ticker}"
            feed = feedparser.parse(url)
            
            news = []
            for entry in feed.entries[:2]:
                try:
                    pub_date = entry.get('published_parsed')
                    if pub_date:
                        pub_dt = datetime(*pub_date[:6])
                        date_str = pub_dt.strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    news.append({
                        'ticker': ticker,
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'published_at': date_str,
                        'summary': entry.get('summary', '')[:200],
                        'source': 'Benzinga'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_for_ticker(self, ticker: str, company: str) -> List[Dict]:
        """티커별 모든 소스 뉴스 수집"""
        all_news = []
        
        # Yahoo Finance (주요 소스)
        yahoo_news = self.collect_yahoo_rss(ticker)
        all_news.extend(yahoo_news)
        
        # MarketWatch
        mw_news = self.collect_marketwatch(ticker)
        all_news.extend(mw_news)
        
        # Motley Fool
        fool_news = self.collect_motley_fool(ticker)
        all_news.extend(fool_news)
        
        # Seeking Alpha
        sa_news = self.collect_seeking_alpha(ticker)
        all_news.extend(sa_news)
        
        # Benzinga
        bz_news = self.collect_benzinga_rss(ticker)
        all_news.extend(bz_news)
        
        # 회사명 추가
        for item in all_news:
            item['company_name'] = company
        
        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_news = []
        for item in all_news:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_news.append(item)
        
        return unique_news
    
    def collect_all(self, holdings: List[Dict], etf_ticker: str) -> List[Dict]:
        """전체 Holdings 뉴스 수집"""
        all_news = []
        
        total = len(holdings)
        for idx, holding in enumerate(holdings):
            ticker = holding['ticker']
            company = holding['name']
            
            print(f"  [{idx+1}/{total}] {ticker} ({company})...")
            
            news_items = self.collect_for_ticker(ticker, company)
            
            # 메타데이터 추가
            for news in news_items:
                news['etf'] = etf_ticker
                news['weight'] = holding['weight']
            
            all_news.extend(news_items)
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n✅ 총 {len(all_news)}개 뉴스 수집 완료")
        
        return all_news
