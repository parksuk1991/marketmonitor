"""
뉴스 수집기 - Yahoo Finance RSS 기반
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
from bs4 import BeautifulSoup

class NewsCollector:
    """뉴스 수집기"""
    
    def __init__(self, days=3):
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)
    
    def collect_yahoo_finance_news(self, ticker: str) -> List[Dict]:
        """Yahoo Finance RSS에서 뉴스 수집"""
        try:
            # Yahoo Finance RSS URL
            rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            
            feed = feedparser.parse(rss_url)
            
            news_items = []
            
            for entry in feed.entries[:10]:  # 최대 10개
                try:
                    # 발행일 파싱
                    pub_date = entry.get('published_parsed')
                    if pub_date:
                        pub_datetime = datetime(*pub_date[:6])
                        
                        # 최근 N일 이내만
                        if pub_datetime < self.cutoff_date:
                            continue
                        
                        pub_date_str = pub_datetime.strftime('%Y-%m-%d')
                    else:
                        pub_date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    news_items.append({
                        'ticker': ticker,
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'published_at': pub_date_str,
                        'summary': entry.get('summary', ''),
                        'source': 'Yahoo Finance'
                    })
                    
                except Exception as e:
                    print(f"  ⚠️ Entry 파싱 실패: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            print(f"  ⚠️ {ticker} Yahoo Finance RSS 실패: {e}")
            return []
    
    def collect_marketwatch_news(self, ticker: str) -> List[Dict]:
        """MarketWatch에서 뉴스 검색"""
        try:
            # MarketWatch 검색 URL
            search_url = f"https://www.marketwatch.com/search?q={ticker}&ts=0&tab=All%20News"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            articles = soup.find_all('div', class_='article__content', limit=5)
            
            for article in articles:
                try:
                    title_elem = article.find('a', class_='link')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    if not url.startswith('http'):
                        url = f"https://www.marketwatch.com{url}"
                    
                    news_items.append({
                        'ticker': ticker,
                        'title': title,
                        'url': url,
                        'published_at': datetime.now().strftime('%Y-%m-%d'),
                        'summary': title[:200],
                        'source': 'MarketWatch'
                    })
                    
                except Exception as e:
                    continue
            
            return news_items[:3]  # 최대 3개
            
        except Exception as e:
            print(f"  ⚠️ {ticker} MarketWatch 실패: {e}")
            return []
    
    def collect_news_for_ticker(self, ticker: str, company: str) -> List[Dict]:
        """티커에 대한 뉴스 수집 (모든 소스)"""
        all_news = []
        
        # Yahoo Finance
        yahoo_news = self.collect_yahoo_finance_news(ticker)
        all_news.extend(yahoo_news)
        
        # MarketWatch (Yahoo가 적으면)
        if len(yahoo_news) < 3:
            mw_news = self.collect_marketwatch_news(ticker)
            all_news.extend(mw_news)
        
        # 회사명 추가
        for news in all_news:
            news['company_name'] = company
        
        return all_news
    
    def collect_all_news(self, portfolio: List[Dict]) -> List[Dict]:
        """포트폴리오 전체 뉴스 수집"""
        all_news = []
        
        for idx, item in enumerate(portfolio):
            ticker = item['ticker']
            company = item['company']
            
            print(f"  [{idx+1}/{len(portfolio)}] {ticker} ({company})...")
            
            news_items = self.collect_news_for_ticker(ticker, company)
            
            # 메타데이터 추가
            for news in news_items:
                news['sector'] = item['sector']
                news['etf'] = item['etf']
                news['weight'] = item['weight']
            
            all_news.extend(news_items)
            
            # Rate limiting
            time.sleep(0.3)
        
        print(f"\n✅ 총 {len(all_news)}개 뉴스 수집 완료")
        
        return all_news
