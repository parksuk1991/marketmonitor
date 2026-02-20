# 🚀 섹터 ETF 감성분석 대시보드

미국 주식 시장의 11개 섹터 ETF에 대한 실시간 뉴스 감성 분석 시스템

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP-NAME.streamlit.app)

## 📊 주요 기능

### 1. 섹터별 감성 점수
- **11개 섹터 ETF** 실시간 모니터링
- Simple Average & Weighted Average 점수
- 색상 코딩으로 한눈에 파악

### 2. 뉴스 감성 분석
- **FinBERT** + **VADER** 하이브리드 분석
- 카테고리 자동 분류 (Earnings, M&A, Product 등)
- 본문 요약 제공

### 3. 인터랙티브 시각화
- Plotly 기반 동적 차트
- Word Cloud (빈도 & 감성 기여도)
- 시계열 트렌드 분석

### 4. 상세 데이터 테이블
- 11개 컬럼 완전 표시
- 필터링 & 정렬 기능
- CSV 다운로드

## 🎯 지원 섹터

| ETF | 섹터 | 주요 종목 |
|-----|------|----------|
| XLK | Technology | AAPL, MSFT, NVDA |
| XLF | Financials | JPM, BAC, WFC |
| XLV | Health Care | UNH, JNJ, LLY |
| XLY | Consumer Discretionary | AMZN, TSLA, HD |
| XLE | Energy | XOM, CVX, COP |
| XLI | Industrials | CAT, UNP, GE |
| XLP | Consumer Staples | PG, KO, PEP |
| XLC | Communication Services | META, GOOGL, NFLX |
| XLRE | Real Estate | AMT, PLD, EQIX |
| XLB | Materials | LIN, APD, SHW |
| XLU | Utilities | NEE, DUK, SO |

## 🚀 빠른 시작

### 온라인에서 바로 사용
👉 [대시보드 열기](https://YOUR-APP-NAME.streamlit.app)

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/YOUR_USERNAME/market-monitor.git
cd market-monitor

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 데이터 수집 (처음 1회)
python src/main.py

# 5. 대시보드 실행
streamlit run app.py
```

## 📁 프로젝트 구조

```
market-monitor/
├── app.py                      # Streamlit 대시보드
├── requirements.txt            # 패키지 목록
├── .streamlit/
│   └── config.toml            # Streamlit 설정
├── data/
│   ├── Market_Monitor_latest.xlsx  # 최신 데이터
│   └── reports/               # 과거 리포트
├── src/
│   ├── main.py               # 메인 실행 파일
│   ├── collectors/           # 뉴스 수집
│   ├── analyzers/            # 감성 분석
│   └── reporters/            # 엑셀 생성
└── README.md
```

## 🔄 데이터 업데이트

### 자동 업데이트 (권장)
GitHub Actions로 매일 자동 실행:

```yaml
# .github/workflows/update_data.yml
name: Update Data
on:
  schedule:
    - cron: '0 0 * * *'  # 매일 오전 9시 (KST)
  workflow_dispatch:
```

### 수동 업데이트
```bash
python src/main.py
```

## 📊 데이터 소스

- **뉴스**: Yahoo Finance RSS, Motley Fool, MarketWatch
- **ETF Holdings**: Yahoo Finance API
- **감성 분석**: FinBERT (ProsusAI/finbert) + VADER

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **Visualization**: Plotly, Matplotlib, WordCloud
- **ML**: Transformers (FinBERT), VADER
- **Deployment**: Streamlit Cloud + GitHub

## 📈 사용 예시

### 1. 섹터 모멘텀 파악
긍정적 감성이 높은 섹터를 빠르게 식별

### 2. 개별 종목 분석
특정 기업의 최근 뉴스 감성 추이 확인

### 3. 리스크 모니터링
부정적 뉴스가 급증하는 섹터 조기 포착

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

이슈를 등록해주세요: [GitHub Issues](https://github.com/YOUR_USERNAME/market-monitor/issues)

## ⚠️ 면책 조항

이 도구는 정보 제공 목적으로만 사용됩니다. 투자 결정은 본인의 책임하에 이루어져야 합니다.

---

Made with ❤️ using Streamlit
