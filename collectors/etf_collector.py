"""
ETF Holdings 수집기 (세션 문제 해결)
"""
import ssl
import urllib3
from yahooquery import Ticker
from typing import List, Dict

# SSL 설정
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ETFCollector:
    """ETF Holdings 수집"""
    
    def __init__(self):
        # 매번 새로운 세션 생성하지 않음
        try:
            from curl_cffi import requests as cffi_requests
            self.session = cffi_requests.Session(impersonate="chrome")
            self.session.verify = False
            print("✓ ETF 수집기 초기화 (curl_cffi)")
        except:
            self.session = None
            print("✓ ETF 수집기 초기화 (기본)")
    
    def get_etf_holdings(self, ticker: str) -> List[Dict]:
        """
        Holdings 가져오기 (매번 새로 호출)
        """
        try:
            # 매번 새로운 Ticker 객체 생성
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
                
                print(f"  ✅ {ticker}: {len(result)}개 종목")
                return result
            else:
                print(f"  ❌ {ticker}: Holdings 정보 없음")
                return []
                
        except Exception as e:
            print(f"  ❌ {ticker}: {str(e)[:100]}")
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
