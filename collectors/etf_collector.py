"""
ETF Holdings 수집기 (yahooquery 사용)
하드코딩 제거, 실시간 데이터만 사용
"""
import ssl
import urllib3
import pandas as pd
from yahooquery import Ticker
from typing import List, Dict, Optional
from curl_cffi import requests as cffi_requests

# SSL 경고 무시
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ETFCollector:
    """ETF Holdings 실시간 수집"""
    
    def __init__(self):
        self.session = cffi_requests.Session(impersonate="chrome")
        self.session.verify = False
    
    def get_etf_holdings(self, etf_ticker: str, top_n: int = 10) -> Optional[List[Dict]]:
        """ETF의 Top N Holdings 가져오기 (실시간)"""
        try:
            # yahooquery로 Holdings 가져오기
            etf = Ticker(etf_ticker, session=self.session)
            
            # fund_holding_info 시도
            holdings_info = etf.fund_holding_info
            
            if isinstance(holdings_info, dict) and etf_ticker in holdings_info:
                holdings_data = holdings_info[etf_ticker]
                
                if isinstance(holdings_data, dict) and 'holdings' in holdings_data:
                    holdings_list = holdings_data['holdings']
                    
                    result = []
                    for holding in holdings_list[:top_n]:
                        result.append({
                            'ticker': holding.get('symbol', ''),
                            'name': holding.get('holdingName', ''),
                            'weight': holding.get('holdingPercent', 0.0) * 100
                        })
                    
                    if result:
                        print(f"✅ {etf_ticker}: {len(result)}개 Holdings 수집")
                        return result
            
            # 실패 시 에러
            print(f"❌ {etf_ticker}: Holdings 정보 없음")
            return None
            
        except Exception as e:
            print(f"❌ {etf_ticker} 오류: {e}")
            return None
    
    def get_etf_name(self, ticker: str) -> str:
        """ETF 이름 가져오기"""
        try:
            etf = Ticker(ticker, session=self.session)
            info = etf.quote_type
            
            if isinstance(info, dict) and ticker in info:
                return info[ticker].get('longName', f'{ticker} ETF')
            
            return f'{ticker} ETF'
            
        except:
            return f'{ticker} ETF'
    
    def get_etf_sector_weightings(self, ticker: str) -> Optional[pd.DataFrame]:
        """ETF 섹터 비중 가져오기"""
        try:
            etf = Ticker(ticker, session=self.session)
            sector_data = etf.fund_sector_weightings
            
            if isinstance(sector_data, dict) and ticker in sector_data:
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
