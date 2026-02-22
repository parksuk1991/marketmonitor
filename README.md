# 🚀 섹터 ETF 감성분석 대시보드

미국 주식 11개 섹터 ETF의 실시간 뉴스 감성 분석 시스템

## 📊 기능

- **11개 섹터 ETF** 모니터링 (XLK, XLF, XLV, XLY, XLE, XLI, XLP, XLC, XLRE, XLB, XLU)
- **실시간 뉴스 수집** (Yahoo Finance, MarketWatch)
- **VADER 감성 분석**
- **카테고리 자동 분류** (Earnings, M&A, Product, Regulatory, Analyst, General)
- **Plotly 인터랙티브 차트**
- **Excel/CSV 다운로드**

## 🚀 Streamlit Cloud 배포

현재 배포된 앱: [marketmonitor.streamlit.app](https://marketmonitor.streamlit.app)

## 📁 프로젝트 구조

```
marketmonitor/
├── app.py                          # Streamlit 대시보드
├── requirements.txt                # 패키지 목록
├── config/
│   └── config.py                   # 설정
├── collectors/
│   ├── sector_collector.py         # ETF Holdings 수집
│   └── news_collector.py           # 뉴스 수집
├── analyzers/
│   └── sentiment_analyzer.py       # 감성 분석
├── reporters/
│   └── excel_generator_sector.py   # 엑셀 생성
└── src/
    └── main.py                     # 파이프라인
```

## 🛠️ 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/parksuk1991/marketmonitor.git
cd marketmonitor

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Streamlit 실행
streamlit run app.py
```

## 📝 라이선스

MIT License
