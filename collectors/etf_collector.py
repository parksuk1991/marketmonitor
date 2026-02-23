"""
ETF Holdings 수집기 (yahooquery)
"""
import ssl
import urllib3
from yahooquery import Ticker
from typing import List, Dict, Optional
from curl_cffi import requests as cffi_requests

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ETFCollector:
    """ETF Holdings 수집"""
    
    def __init__(self):
        self.session = cffi_requests.Session(impersonate="chrome")
        self.session.verify = False
    
    def get_etf_holdings(self, etf_ticker: str, top_n: int = 10) -> Optional[List[Dict]]:
        """Top N Holdings 가져오기"""
        try:
            etf = Ticker(etf_ticker, session=self.session)
            holdings_info = etf.fund_holding_info
            
            if isinstance(holdings_info, dict) and etf_ticker in holdings_info:
                data = holdings_info[etf_ticker]
                
                if isinstance(data, dict) and 'holdings' in data:
                    holdings_list = data['holdings']
                    
                    result = []
                    for holding in holdings_list[:top_n]:
                        result.append({
                            'ticker': holding.get('symbol', ''),
                            'name': holding.get('holdingName', ''),
                            'weight': holding.get('holdingPercent', 0.0) * 100
                        })
                    
                    if result:
                        print(f"✅ {etf_ticker}: {len(result)}개 Holdings")
                        return result
            
            print(f"❌ {etf_ticker}: Holdings 없음")
            return None
            
        except Exception as e:
            print(f"❌ {etf_ticker} 오류: {e}")
            return None
    
    def get_etf_name(self, ticker: str) -> str:
        """ETF 이름"""
        try:
            etf = Ticker(ticker, session=self.session)
            info = etf.quote_type
            
            if isinstance(info, dict) and ticker in info:
                return info[ticker].get('longName', f'{ticker} ETF')
            
            return f'{ticker} ETF'
        except:
            return f'{ticker} ETF'
    
    def get_etf_sector_weightings(self, ticker: str) -> Optional:
        """섹터 비중"""
        try:
            etf = Ticker(ticker, session=self.session)
            data = etf.fund_sector_weightings
            
            if isinstance(data, dict) and ticker in data:
                import pandas as pd
                sector_data = data[ticker]
                
                if isinstance(sector_data, pd.Series) and not sector_data.empty:
                    df = pd.DataFrame({
                        'Sector': sector_data.index,
                        'Weight (%)': sector_data.values * 100
                    })
                    return df.reset_index(drop=True)
            
            return None
        except:
            return None
