# 🚀 ETF Holdings 감성분석 (실시간 버전)

실시간 Holdings + 5개 뉴스 소스 + FinBERT 감성 분석

## ✨ 주요 기능

### 실시간 데이터
- **yahooquery**: 실시간 ETF Holdings 수집
- **하드코딩 없음**: 모든 데이터 실시간 수집

### 5개 뉴스 소스
- **Yahoo Finance**: RSS 피드
- **MarketWatch**: 웹 스크래핑
- **Motley Fool**: 검색 API
- **Seeking Alpha**: RSS 피드
- **Benzinga**: RSS 피드

### FinBERT 감성 분석
- 금융 뉴스 특화 AI 모델
- -1 ~ +1 감성 점수
- 자동 카테고리 분류

## 📊 지원 ETF

모든 ETF 지원:
- SPY, QQQ, DIA, IWM
- XLK, XLF, XLV, XLY 등 섹터 ETF
- VTI, VOO, VT 등 Vanguard ETF

## 🚀 사용 방법

1. ETF 티커 입력
2. "분석 시작" 클릭
3. 약 60초 대기 (실시간 수집)
4. 결과 확인

## 🛠️ 기술 스택

- **yahooquery**: Holdings 실시간 수집
- **FinBERT**: 감성 분석
- **feedparser**: RSS 뉴스
- **BeautifulSoup**: 웹 스크래핑
- **Streamlit**: 대시보드
- **Plotly**: 차트

## 📝 라이선스

MIT License
