"""
섹터 ETF Holdings 수집기
"""
import yfinance as yf
import pandas as pd
from typing import Dict, List
import time

class SectorETFCollector:
    """섹터 ETF의 Holdings 정보 수집"""
    
    def __init__(self):
        self.sector_etfs = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLV': 'Health Care',
            'XLY': 'Consumer Discretionary',
            'XLE': 'Energy',
            'XLI': 'Industrials',
            'XLP': 'Consumer Staples',
            'XLC': 'Communication Services',
            'XLRE': 'Real Estate',
            'XLB': 'Materials',
            'XLU': 'Utilities'
        }
    
    def get_etf_holdings(self, etf_ticker: str, top_n: int = 5) -> List[Dict]:
        """ETF의 상위 Holdings 가져오기"""
        try:
            etf = yf.Ticker(etf_ticker)
            
            # Holdings 정보
            holdings = etf.get_holdings()
            
            if holdings is None or holdings.empty:
                # 대체: 주요 종목 하드코딩
                return self._get_fallback_holdings(etf_ticker, top_n)
            
            # 상위 N개 종목
            top_holdings = holdings.head(top_n)
            
            result = []
            for _, row in top_holdings.iterrows():
                result.append({
                    'ticker': row.get('Symbol', ''),
                    'name': row.get('Holding', ''),
                    'weight': row.get('% Assets', 0.0)
                })
            
            return result
            
        except Exception as e:
            print(f"⚠️ {etf_ticker} Holdings 수집 실패: {e}")
            return self._get_fallback_holdings(etf_ticker, top_n)
    
    def _get_fallback_holdings(self, etf_ticker: str, top_n: int = 5) -> List[Dict]:
        """대체 Holdings 정보 (하드코딩)"""
        fallback_data = {
            'XLK': [
                {'ticker': 'AAPL', 'name': 'Apple Inc', 'weight': 21.5},
                {'ticker': 'MSFT', 'name': 'Microsoft Corp', 'weight': 20.8},
                {'ticker': 'NVDA', 'name': 'NVIDIA Corp', 'weight': 8.2},
                {'ticker': 'AVGO', 'name': 'Broadcom Inc', 'weight': 4.1},
                {'ticker': 'CRM', 'name': 'Salesforce Inc', 'weight': 2.3}
            ],
            'XLF': [
                {'ticker': 'BRK.B', 'name': 'Berkshire Hathaway', 'weight': 12.4},
                {'ticker': 'JPM', 'name': 'JPMorgan Chase', 'weight': 9.8},
                {'ticker': 'V', 'name': 'Visa Inc', 'weight': 7.2},
                {'ticker': 'MA', 'name': 'Mastercard Inc', 'weight': 6.5},
                {'ticker': 'BAC', 'name': 'Bank of America', 'weight': 5.8}
            ],
            'XLV': [
                {'ticker': 'UNH', 'name': 'UnitedHealth Group', 'weight': 10.2},
                {'ticker': 'LLY', 'name': 'Eli Lilly', 'weight': 8.9},
                {'ticker': 'JNJ', 'name': 'Johnson & Johnson', 'weight': 7.6},
                {'ticker': 'ABBV', 'name': 'AbbVie Inc', 'weight': 5.4},
                {'ticker': 'MRK', 'name': 'Merck & Co', 'weight': 4.8}
            ],
            'XLY': [
                {'ticker': 'AMZN', 'name': 'Amazon.com Inc', 'weight': 22.1},
                {'ticker': 'TSLA', 'name': 'Tesla Inc', 'weight': 15.3},
                {'ticker': 'HD', 'name': 'Home Depot', 'weight': 8.9},
                {'ticker': 'MCD', 'name': 'McDonald\'s Corp', 'weight': 4.2},
                {'ticker': 'NKE', 'name': 'Nike Inc', 'weight': 3.7}
            ],
            'XLE': [
                {'ticker': 'XOM', 'name': 'Exxon Mobil', 'weight': 22.3},
                {'ticker': 'CVX', 'name': 'Chevron Corp', 'weight': 16.8},
                {'ticker': 'COP', 'name': 'ConocoPhillips', 'weight': 7.9},
                {'ticker': 'SLB', 'name': 'Schlumberger', 'weight': 4.5},
                {'ticker': 'EOG', 'name': 'EOG Resources', 'weight': 3.8}
            ],
            'XLI': [
                {'ticker': 'CAT', 'name': 'Caterpillar Inc', 'weight': 8.9},
                {'ticker': 'UNP', 'name': 'Union Pacific', 'weight': 7.2},
                {'ticker': 'GE', 'name': 'General Electric', 'weight': 6.5},
                {'ticker': 'BA', 'name': 'Boeing Co', 'weight': 5.8},
                {'ticker': 'HON', 'name': 'Honeywell Intl', 'weight': 5.2}
            ],
            'XLP': [
                {'ticker': 'PG', 'name': 'Procter & Gamble', 'weight': 14.2},
                {'ticker': 'KO', 'name': 'Coca-Cola Co', 'weight': 11.8},
                {'ticker': 'PEP', 'name': 'PepsiCo Inc', 'weight': 10.5},
                {'ticker': 'COST', 'name': 'Costco Wholesale', 'weight': 9.8},
                {'ticker': 'WMT', 'name': 'Walmart Inc', 'weight': 8.9}
            ],
            'XLC': [
                {'ticker': 'META', 'name': 'Meta Platforms', 'weight': 24.3},
                {'ticker': 'GOOGL', 'name': 'Alphabet Inc', 'weight': 22.1},
                {'ticker': 'NFLX', 'name': 'Netflix Inc', 'weight': 8.9},
                {'ticker': 'DIS', 'name': 'Walt Disney', 'weight': 6.2},
                {'ticker': 'CMCSA', 'name': 'Comcast Corp', 'weight': 4.8}
            ],
            'XLRE': [
                {'ticker': 'AMT', 'name': 'American Tower', 'weight': 12.3},
                {'ticker': 'PLD', 'name': 'Prologis Inc', 'weight': 10.8},
                {'ticker': 'EQIX', 'name': 'Equinix Inc', 'weight': 7.9},
                {'ticker': 'PSA', 'name': 'Public Storage', 'weight': 6.5},
                {'ticker': 'SPG', 'name': 'Simon Property', 'weight': 5.2}
            ],
            'XLB': [
                {'ticker': 'LIN', 'name': 'Linde PLC', 'weight': 18.9},
                {'ticker': 'APD', 'name': 'Air Products', 'weight': 9.2},
                {'ticker': 'SHW', 'name': 'Sherwin-Williams', 'weight': 8.5},
                {'ticker': 'FCX', 'name': 'Freeport-McMoRan', 'weight': 6.8},
                {'ticker': 'NEM', 'name': 'Newmont Corp', 'weight': 5.4}
            ],
            'XLU': [
                {'ticker': 'NEE', 'name': 'NextEra Energy', 'weight': 15.2},
                {'ticker': 'DUK', 'name': 'Duke Energy', 'weight': 8.9},
                {'ticker': 'SO', 'name': 'Southern Co', 'weight': 7.6},
                {'ticker': 'D', 'name': 'Dominion Energy', 'weight': 6.8},
                {'ticker': 'AEP', 'name': 'American Electric', 'weight': 5.9}
            ]
        }
        
        return fallback_data.get(etf_ticker, [])[:top_n]
    
    def collect_all_sector_holdings(self, top_n: int = 5) -> Dict:
        """모든 섹터 ETF의 Holdings 수집"""
        all_holdings = {}
        
        for etf, sector in self.sector_etfs.items():
            print(f"📊 {sector} ({etf}) Holdings 수집 중...")
            holdings = self.get_etf_holdings(etf, top_n)
            
            all_holdings[sector] = {
                'etf': etf,
                'holdings': holdings
            }
            
            time.sleep(0.5)  # Rate limiting
        
        return all_holdings
    
    def get_portfolio_for_news(self, holdings_data: Dict) -> List[Dict]:
        """뉴스 수집을 위한 포트폴리오 생성"""
        portfolio = []
        
        for sector, data in holdings_data.items():
            for holding in data['holdings']:
                portfolio.append({
                    'sector': sector,
                    'etf': data['etf'],
                    'ticker': holding['ticker'],
                    'company': holding['name'],
                    'weight': holding['weight']
                })
        
        return portfolio
