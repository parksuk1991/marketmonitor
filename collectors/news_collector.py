"""
뉴스 수집기 (본문 추출 + 요약 포함)
모든 뉴스 소스 + 본문 스크래핑
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import re

class NewsCollector:
    """다중 소스 뉴스 수집 + 본문 추출"""
    
    def __init__(self, days=3):
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_article_content(self, url: str) -> str:
        """기사 본문 추출"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 본문 추출 (다양한 태그 시도)
            content_tags = [
                soup.find('article'),
                soup.find('div', class_='article-body'),
                soup.find('div', class_='caas-body'),
                soup.find('div', class_='body'),
                soup.find('div', {'id': 'article-body'}),
                soup.find('div', class_='content')
            ]
            
            for tag in content_tags:
                if tag:
                    # 스크립트, 스타일 제거
                    for script in tag(['script', 'style', 'aside', 'nav']):
                        script.decompose()
                    
                    text = tag.get_text(separator=' ', strip=True)
                    
                    # 정리
                    text = re.sub(r'\s+', ' ', text)
                    
                    if len(text) > 100:
                        return text
            
            # 모든 p 태그 추출
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            text = re.sub(r'\s+', ' ', text)
            
            return text if len(text) > 50 else ""
            
        except:
            return ""
    
    def create_highlights(self, content: str, max_length: int = 200) -> str:
        """본문에서 하이라이트 생성"""
        if not content:
            return ""
        
        # 문장 단위로 분리
        sentences = re.split(r'[.!?]\s+', content)
        
        # 처음 2-3문장 추출
        highlights = []
        total_length = 0
        
        for sentence in sentences[:5]:
            sentence = sentence.strip()
            if len(sentence) > 20:  # 너무 짧은 문장 제외
                highlights.append(sentence)
                total_length += len(sentence)
                
                if total_length >= max_length:
                    break
        
        result = '. '.join(highlights)
        
        if len(result) > max_length:
            result = result[:max_length] + '...'
        
        return result
    
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
                    summary = entry.get('summary', '')
                    
                    # 본문 추출
                    content = self.extract_article_content(article_url)
                    
                    # Highlights 생성
                    highlights = self.create_highlights(content if content else summary)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary[:500],
                        'content': content[:2000],  # 본문 (최대 2000자)
                        'highlights': highlights,
                        'source': 'Yahoo Finance'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_marketwatch(self, ticker: str) -> List[Dict]:
        """MarketWatch"""
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
                    article_url = title_elem.get('href', '')
                    
                    if not article_url.startswith('http'):
                        article_url = f"https://www.marketwatch.com{article_url}"
                    
                    # 본문 추출
                    content = self.extract_article_content(article_url)
                    highlights = self.create_highlights(content if content else title)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': datetime.now().strftime('%Y-%m-%d'),
                        'summary': title[:500],
                        'content': content[:2000],
                        'highlights': highlights,
                        'source': 'MarketWatch'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_motley_fool(self, ticker: str) -> List[Dict]:
        """Motley Fool"""
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
                    article_url = title_elem.get('href', '')
                    
                    if article_url and not article_url.startswith('http'):
                        article_url = f"https://www.fool.com{article_url}"
                    
                    if title and article_url:
                        content = self.extract_article_content(article_url)
                        highlights = self.create_highlights(content if content else title)
                        
                        news.append({
                            'ticker': ticker,
                            'title': title,
                            'url': article_url,
                            'published_at': datetime.now().strftime('%Y-%m-%d'),
                            'summary': title[:500],
                            'content': content[:2000],
                            'highlights': highlights,
                            'source': 'Motley Fool'
                        })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_seeking_alpha(self, ticker: str) -> List[Dict]:
        """Seeking Alpha"""
        try:
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
                    
                    title = entry.get('title', '')
                    article_url = entry.get('link', '')
                    summary = entry.get('summary', '')
                    
                    content = self.extract_article_content(article_url)
                    highlights = self.create_highlights(content if content else summary)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary[:500],
                        'content': content[:2000],
                        'highlights': highlights,
                        'source': 'Seeking Alpha'
                    })
                except:
                    continue
            
            return news
        except:
            return []
    
    def collect_benzinga_rss(self, ticker: str) -> List[Dict]:
        """Benzinga"""
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
                    
                    title = entry.get('title', '')
                    article_url = entry.get('link', '')
                    summary = entry.get('summary', '')
                    
                    content = self.extract_article_content(article_url)
                    highlights = self.create_highlights(content if content else summary)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary[:500],
                        'content': content[:2000],
                        'highlights': highlights,
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
        
        # 모든 소스에서 수집
        yahoo_news = self.collect_yahoo_rss(ticker)
        all_news.extend(yahoo_news)
        
        mw_news = self.collect_marketwatch(ticker)
        all_news.extend(mw_news)
        
        fool_news = self.collect_motley_fool(ticker)
        all_news.extend(fool_news)
        
        sa_news = self.collect_seeking_alpha(ticker)
        all_news.extend(sa_news)
        
        bz_news = self.collect_benzinga_rss(ticker)
        all_news.extend(bz_news)
        
        # 회사명 추가
        for item in all_news:
            item['company_name'] = company
        
        # 중복 제거
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
            
            time.sleep(0.5)
        
        print(f"\n✅ {etf_ticker}: {len(all_news)}개 뉴스 수집")
        
        return all_news
