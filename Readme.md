# 🚀 섹터 ETF 감성분석 대시보드

미국 주식 시장 11개 섹터 ETF의 실시간 뉴스 감성 분석 시스템

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP-NAME.streamlit.app)

## 📊 주요 기능

### 🎯 핵심 기능
- **11개 섹터 ETF** 실시간 모니터링
- **FinBERT + VADER** 하이브리드 감성 분석
- **Plotly** 인터랙티브 차트
- **엑셀/CSV** 다운로드 기능

### 📈 시각화
- 섹터별 평균 Sentiment (색상 코딩)
- 뉴스 개수 및 카테고리 분포
- Word Cloud (빈도 & 감성 기여도)
- 시계열 트렌드 분석

### 💾 데이터 관리
- 원본 엑셀 파일 다운로드
- CSV 내보내기
- 섹터별 다운로드

## 🎯 지원 섹터

| ETF | 섹터 | 주요 종목 |
|-----|------|----------|
| **XLK** | Technology | AAPL, MSFT, NVDA |
| **XLF** | Financials | JPM, BAC, WFC |
| **XLV** | Health Care | UNH, JNJ, LLY |
| **XLY** | Consumer Discretionary | AMZN, TSLA, HD |
| **XLE** | Energy | XOM, CVX, COP |
| **XLI** | Industrials | CAT, UNP, GE |
| **XLP** | Consumer Staples | PG, KO, PEP |
| **XLC** | Communication Services | META, GOOGL, NFLX |
| **XLRE** | Real Estate | AMT, PLD, EQIX |
| **XLB** | Materials | LIN, APD, SHW |
| **XLU** | Utilities | NEE, DUK, SO |

## 🚀 빠른 시작

### 온라인에서 바로 사용
👉 [대시보드 열기](https://YOUR-APP-NAME.streamlit.app)

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/YOUR_USERNAME/marketmonitor.git
cd marketmonitor

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 대시보드 실행
streamlit run app.py
```

**주의:** 데이터 파일(`data/reports/Market_Monitor_*.xlsx`)이 필요합니다.

## 📁 프로젝트 구조

```
marketmonitor/
├── app.py                      # Streamlit 대시보드
├── requirements.txt            # 패키지 목록
├── README.md                   # 프로젝트 설명
├── .streamlit/
│   └── config.toml            # Streamlit 설정
└── data/
    └── reports/
        └── Market_Monitor_*.xlsx  # 데이터 파일
```

## 📊 데이터 형식

엑셀 파일 구조:
- **Sheet 1: Daily News Monitor**
  - ETF, Sector, Ticker, Company, Weight (%)
  - Category, Title, URL, Pub Date
  - Highlights, Sentiment
  
- **Sheet 2: Sentiment Trend** (선택사항)
  - Ticker, Company
  - Date -2, Date -1, Today
  - Trend, Change

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib, WordCloud
- **Deployment**: Streamlit Cloud

## 📈 사용 예시

### 1. 섹터 모멘텀 파악
```python
# 긍정적 감성이 높은 섹터 식별
positive_sectors = df[df['Sentiment'] > 0.3]
```

### 2. 개별 종목 분석
```python
# 특정 기업의 최근 뉴스 감성
company_news = df[df['Company'] == 'Apple Inc']
```

### 3. 리스크 모니터링
```python
# 부정적 뉴스가 급증하는 섹터
negative_surge = df[df['Sentiment'] < -0.3].groupby('Sector').size()
```

## 🎨 스크린샷

### 개요 화면
![Overview](https://via.placeholder.com/800x400?text=Overview+Screenshot)

### 섹터 분석
![Sector Analysis](https://via.placeholder.com/800x400?text=Sector+Analysis+Screenshot)

### 시각화
![Visualization](https://via.placeholder.com/800x400?text=Visualization+Screenshot)

## 🤝 기여

Pull Request를 환영합니다!

1. Fork
2. Feature Branch 생성 (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📝 라이선스

MIT License

## 📧 문의

이슈를 등록해주세요: [GitHub Issues](https://github.com/YOUR_USERNAME/marketmonitor/issues)

## ⚠️ 면책 조항

이 도구는 정보 제공 목적으로만 사용됩니다. 투자 결정은 본인의 책임하에 이루어져야 합니다.

---

Made with ❤️ using Streamlit & Plotly
