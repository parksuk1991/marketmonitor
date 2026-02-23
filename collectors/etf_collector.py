"""
ETF Holdings 수집기 (검증된 버전)
이전에 작동했던 코드 그대로 사용
"""
import ssl
import urllib3
from yahooquery import Ticker
from curl_cffi import requests as cffi_requests
from typing import Dict, List

# SSL 검증 비활성화
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ETFCollector:
    """ETF Holdings 수집"""
    
    def __init__(self):
        self.session = cffi_requests.Session(impersonate="chrome")
        self.session.verify = False
        print("✓ ETF Holdings 수집기 초기화")
    
    def get_etf_holdings(self, ticker: str) -> List[Dict]:
        """
        ETF Top 10 Holdings 가져오기
        
        Returns:
            [{'symbol': 'AAPL', 'weight': 0.25, 'name': 'Apple Inc'}, ...]
        """
        try:
            etf = Ticker(ticker, session=self.session)
            
            # Holdings 정보
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
                            'weight': weight * 100,  # 퍼센트로 변환
                            'name': holding.get('holdingName', symbol)
                        })
                
                print(f"  {ticker}: {len(result)}개 종목")
                return result
            else:
                print(f"  {ticker}: Holdings 정보 없음")
                return []
                
        except Exception as e:
            print(f"  {ticker}: 오류 - {str(e)[:50]}")
            return []
    
    def get_etf_name(self, ticker: str) -> str:
        """ETF 이름 가져오기"""
        try:
            etf = Ticker(ticker, session=self.session)
            quote_type = etf.quote_type
            
            if ticker in quote_type:
                return quote_type[ticker].get('longName', f'{ticker} ETF')
            
            return f'{ticker} ETF'
        except:
            return f'{ticker} ETF'
    
    def get_etf_sector_weightings(self, ticker: str):
        """섹터 비중 가져오기"""
        try:
            import pandas as pd
            
            etf = Ticker(ticker, session=self.session)
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
