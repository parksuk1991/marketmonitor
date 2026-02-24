"""
ETF Collector (안정화 버전)
재시도 로직 추가
"""
import ssl
import urllib3
from yahooquery import Ticker
from typing import List, Dict
import time

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ETFCollector:
    """안정화된 ETF Collector"""
    
    def __init__(self):
        try:
            from curl_cffi import requests as cffi_requests
            self.session = cffi_requests.Session(impersonate="chrome")
            self.session.verify = False
            print("✓ ETF 수집기 초기화")
        except:
            self.session = None
            print("✓ ETF 수집기 초기화 (기본)")
    
    def get_etf_holdings(self, ticker: str, retry=3) -> List[Dict]:
        """
        Holdings 가져오기 (재시도 로직)
        """
        for attempt in range(retry):
            try:
                # 매번 새로운 Ticker 객체
                if self.session:
                    etf = Ticker(ticker, session=self.session)
                else:
                    etf = Ticker(ticker)
                
                holdings = etf.fund_holding_info
                
                if ticker in holdings and 'holdings' in holdings[ticker]:
                    top_holdings = holdings[ticker]['holdings'][:10]
                    
                    result = []
                    for holding in top_holdings:
                        symbol = holding.get('symbol', '')
                        weight = holding.get('holdingPercent', 0.0)
                        
                        if symbol:
                            result.append({
                                'ticker': symbol,
                                'name': holding.get('holdingName', symbol),
                                'weight': weight * 100
                            })
                    
                    if result:
                        print(f"  ✅ {ticker}: {len(result)}개 종목")
                        return result
                
                # Holdings 없으면 재시도
                if attempt < retry - 1:
                    print(f"  ⚠️ {ticker}: 재시도 {attempt + 1}/{retry}")
                    time.sleep(2)
                
            except Exception as e:
                if attempt < retry - 1:
                    print(f"  ⚠️ {ticker}: 재시도 {attempt + 1}/{retry}")
                    time.sleep(2)
                else:
                    print(f"  ❌ {ticker}: {str(e)[:50]}")
        
        return []
    
    def get_etf_name(self, ticker: str) -> str:
        """ETF 이름"""
        try:
            if self.session:
                etf = Ticker(ticker, session=self.session)
            else:
                etf = Ticker(ticker)
            
            quote_type = etf.quote_type
            
            if ticker in quote_type:
                return quote_type[ticker].get('longName', f'{ticker} ETF')
            
            return f'{ticker} ETF'
        except:
            return f'{ticker} ETF'
    
    def get_etf_sector_weightings(self, ticker: str):
        """섹터 비중"""
        try:
            import pandas as pd
            
            if self.session:
                etf = Ticker(ticker, session=self.session)
            else:
                etf = Ticker(ticker)
            
            sector_data = etf.fund_sector_weightings
            
            if ticker in sector_data:
                data = sector_data[ticker]
                
                if isinstance(data, pd.Series) and not data.empty:
                    df = pd.DataFrame({
                        'Sector': data.index,
                        'Weight (%)': data.values * 100
                    })
                    return df.reset_index(drop=True)
            
            return None
        except:
            return None
