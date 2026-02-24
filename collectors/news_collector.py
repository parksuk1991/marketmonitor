"""
뉴스 수집기 (확장 버전)
5개 소스 + 전체 본문 추출
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
    
    def extract_full_content(self, url: str) -> str:
        """본문 전체 추출 (제한 없음)"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return ""
            
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
            
            # 모든 p 태그 수집 (제한 없음)
            texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30:  # 너무 짧은 문장 제외
                    texts.append(text)
            
            full_text = ' '.join(texts)
            
            # 최대 10,000자까지 (너무 길면 잘림)
            return full_text[:10000] if full_text else ""
            
        except Exception as e:
            print(f"    본문 추출 실패: {e}")
            return ""
    
    def create_full_summary(self, text: str) -> str:
        """본문 전체 요약 (200자 제한 제거)"""
        if not text or len(text) < 20:
            return ""
        
        # 문장 단위로 분리
        sentences = re.split(r'[.!?]\s+', text)
        
        # 처음 5-7 문장 (약 500-800자)
        result = []
        total_len = 0
        
        for sentence in sentences[:7]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                result.append(sentence)
                total_len += len(sentence)
                
                # 약 800자까지
                if total_len >= 800:
                    break
        
        summary = '. '.join(result)
        
        # 800자 제한 (200자보다 훨씬 김)
        if len(summary) > 800:
            summary = summary[:800] + '...'
        
        return summary if summary else text[:800] + '...'
    
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
                    
                    # 전체 본문 추출
                    content = self.extract_full_content(article_url)
                    
                    # 전체 요약
                    if content:
                        highlights = self.create_full_summary(content)
                    elif summary:
                        highlights = self.create_full_summary(summary)
                    else:
                        highlights = title
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary,
                        'content': content,  # 전체 본문
                        'highlights': highlights,  # 전체 요약
                        'source': 'Yahoo Finance'
                    })
                except Exception as e:
                    print(f"    Yahoo entry 오류: {e}")
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
                    
                    content = self.extract_full_content(article_url)
                    highlights = self.create_full_summary(content if content else title)
                    
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
                except Exception as e:
                    print(f"    MarketWatch entry 오류: {e}")
                    continue
            
            return news
        except Exception as e:
            print(f"    MarketWatch 오류: {e}")
            return []
    
    def collect_seeking_alpha(self, ticker: str) -> List[Dict]:
        """Seeking Alpha RSS"""
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
                    
                    content = self.extract_full_content(article_url)
                    highlights = self.create_full_summary(content if content else summary)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary,
                        'content': content,
                        'highlights': highlights,
                        'source': 'Seeking Alpha'
                    })
                except Exception as e:
                    print(f"    Seeking Alpha entry 오류: {e}")
                    continue
            
            return news
        except Exception as e:
            print(f"    Seeking Alpha 오류: {e}")
            return []
    
    def collect_benzinga(self, ticker: str) -> List[Dict]:
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
                    
                    title = entry.get('title', '')
                    article_url = entry.get('link', '')
                    summary = entry.get('summary', '')
                    
                    content = self.extract_full_content(article_url)
                    highlights = self.create_full_summary(content if content else summary)
                    
                    news.append({
                        'ticker': ticker,
                        'title': title,
                        'url': article_url,
                        'published_at': date_str,
                        'summary': summary,
                        'content': content,
                        'highlights': highlights,
                        'source': 'Benzinga'
                    })
                except Exception as e:
                    print(f"    Benzinga entry 오류: {e}")
                    continue
            
            return news
        except Exception as e:
            print(f"    Benzinga 오류: {e}")
            return []
    
    def collect_reuters(self, ticker: str) -> List[Dict]:
        """Reuters (검색)"""
        try:
            url = f"https://www.reuters.com/site-search/?query={ticker}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news = []
            # Reuters 검색 결과 파싱 (구조에 따라 조정 필요)
            articles = soup.find_all('article', limit=2)
            
            for article in articles:
                try:
                    title_elem = article.find('h3')
                    link_elem = article.find('a')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    article_url = link_elem.get('href', '')
                    
                    if article_url and not article_url.startswith('http'):
                        article_url = f"https://www.reuters.com{article_url}"
                    
                    if title and article_url:
                        content = self.extract_full_content(article_url)
                        highlights = self.create_full_summary(content if content else title)
                        
                        news.append({
                            'ticker': ticker,
                            'title': title,
                            'url': article_url,
                            'published_at': datetime.now().strftime('%Y-%m-%d'),
                            'summary': title,
                            'content': content,
                            'highlights': highlights,
                            'source': 'Reuters'
                        })
                except Exception as e:
                    print(f"    Reuters entry 오류: {e}")
                    continue
            
            return news
        except Exception as e:
            print(f"    Reuters 오류: {e}")
            return []
    
    def collect_for_ticker(self, ticker: str, company: str) -> List[Dict]:
        """티커별 모든 소스에서 수집"""
        all_news = []
        
        print(f"    소스별 수집 중...")
        
        # Yahoo Finance (주요)
        yahoo_news = self.collect_yahoo_rss(ticker)
        all_news.extend(yahoo_news)
        print(f"      Yahoo: {len(yahoo_news)}개")
        
        # MarketWatch
        mw_news = self.collect_marketwatch(ticker)
        all_news.extend(mw_news)
        print(f"      MarketWatch: {len(mw_news)}개")
        
        # Seeking Alpha
        sa_news = self.collect_seeking_alpha(ticker)
        all_news.extend(sa_news)
        print(f"      Seeking Alpha: {len(sa_news)}개")
        
        # Benzinga
        bz_news = self.collect_benzinga(ticker)
        all_news.extend(bz_news)
        print(f"      Benzinga: {len(bz_news)}개")
        
        # Reuters
        reuters_news = self.collect_reuters(ticker)
        all_news.extend(reuters_news)
        print(f"      Reuters: {len(reuters_news)}개")
        
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
            
            print(f"  [{idx+1}/{len(holdings)}] {ticker} ({company})")
            
            news = self.collect_for_ticker(ticker, company)
            
            for item in news:
                item['etf'] = etf_ticker
                item['weight'] = holding['weight']
            
            all_news.extend(news)
            time.sleep(0.5)  # Rate limiting
        
        print(f"✅ {etf_ticker}: {len(all_news)}개 뉴스 (5개 소스)")
        return all_news
