# 경제 데이터 수집 시스템

2010년부터 현재까지의 경제 데이터를 수집하고 MongoDB에 저장하는 자동화 시스템

## 📊 수집 데이터

| 카테고리 | 항목 | 수집 주기 |
|---------|------|---------|
| 환율 | USD, JPY, CNY, EUR | 일별 |
| 주가지수 | KOSPI, KOSDAQ, DOW, NASDAQ, S&P500 | 일별 |
| 원자재 | 금, 은, 원유, 구리, 곡물 등 | 일별 |
| 지수 | DXY(달러인덱스), VIX(변동성) | 일별 |
| 기준금리 | 한국, 미국 연방기금금리 | 변동시 |
| 심리지수 | 소비자심리, 경제심리, 뉴스심리 | 월별/일별 |
| 경제지표 | CPI, 수출입물가, 기대인플레이션 | 월별 |

## 🏗️ 프로젝트 구조

```
.
├── common/                    # 공통 모듈
│   ├── config.py             # 설정 및 API 키
│   ├── db_utils.py           # MongoDB 유틸리티
│   └── data_utils.py         # 데이터 처리 유틸리티
│
├── initial_setup/            # 전체 데이터 수집 (1회성)
│   ├── exchange_all.py       # 환율 전체
│   ├── stock_all.py          # 주가지수 전체
│   ├── commodities_all.py    # 원자재/지수 전체
│   ├── interest_all.py       # 기준금리 전체
│   ├── mental_all.py         # 심리지수 전체
│   └── economic_all.py       # 경제지표 전체
│
├── daily_update/             # 일일 업데이트
│   ├── exchange_cron.py      # 환율 업데이트
│   ├── stock_cron.py         # 주가지수 업데이트
│   ├── commodities_cron.py   # 원자재/지수 업데이트
│   ├── interest_cron.py      # 기준금리 업데이트
│   ├── mental_cron.py        # 심리지수 업데이트
│   ├── economic_cron.py      # 경제지표 업데이트
│   └── main.py              # 통합 실행 스크립트
│
├── .github/workflows/
│   └── daily-update.yml      # GitHub Actions 자동화
│
├── requirements.txt
└── README.md
```

## 🚀 빠른 시작

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 초기 데이터 수집 (최초 1회만)

```bash
# 전체 수집
cd initial_setup
python exchange_all.py
python stock_all.py
python commodities_all.py
python interest_all.py
python mental_all.py
python economic_all.py
```

### 3. 일일 업데이트 실행

```bash
cd daily_update

# 전체 업데이트
python main.py

# 특정 카테고리만
python main.py --only exchange

# 특정 카테고리 제외
python main.py --except mental

# 여러 개 선택
python main.py --categories exchange,stock,commodities
```

## ⚙️ GitHub Actions 설정

### 1. GitHub Secrets 추가

Repository → Settings → Secrets and variables → Actions

다음 secrets를 추가하세요:
- `MONGO_URI`: MongoDB 연결 URI
- `MONGO_DB`: 데이터베이스 이름
- `BOK_API_KEY`: 한국은행 API 키
- `FRED_API_KEY`: FRED API 키

자세한 내용은 [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) 참고

### 2. 자동 실행

- **자동**: 매일 UTC 00:00 (한국시간 오전 9시) 자동 실행
- **수동**: Actions 탭 → "Daily Data Update" → "Run workflow"

### 3. 특정 카테고리만 실행 (수동)

1. Actions 탭 → "Daily Data Update" 클릭
2. "Run workflow" 버튼 클릭
3. "실행할 카테고리" 입력란에 입력:
   - 전체: 비워둠
   - 환율만: `exchange`
   - 여러 개: `exchange,stock,commodities`

## 📦 의존성

- **pymongo**: MongoDB 연결
- **pandas**: 데이터 처리
- **yfinance**: 주가/원자재 데이터
- **fredapi**: 미국 경제 데이터
- **requests**: HTTP 요청

## 🗄️ 데이터베이스 구조

### MongoDB 컬렉션

| 컬렉션명 | 설명 | 주요 필드 |
|---------|------|---------|
| USD, JPY, CNY, EUR | 환율 | date, rate, currency_code |
| KOSPI, NASDAQ, ... | 주가지수 | date, open, high, low, close, volume |
| GOLD, CRUDE_OIL, ... | 원자재 | date, open, high, low, close, price |
| KOR_BASE_RATE | 한국 기준금리 | date, rate, country |
| US_FED_RATE | 미국 연방기금금리 | date, rate, series_id |
| consumer_sentiment | 소비자심리지수 | date, value, item_code |
| economic_sentiment | 경제심리지수 | date, value, item_code |
| news_sentiment | 뉴스심리지수 | date, value, item_code |
| cpi_index | 소비자물가지수 | date, value, indicator_name |
| export_import_price_index | 수출입물가지수 | date, value, indicator_name, type |
| inflation_expectation | 기대인플레이션 | date, value, indicator_name |

## 🔧 개발

### 로컬 환경 설정

```bash
# .env 파일 생성
cat > .env << EOF
MONGO_URI=mongodb+srv://...
MONGO_DB=exchange_all
BOK_API_KEY=your_key
FRED_API_KEY=your_key
EOF

# python-dotenv 설치
pip install python-dotenv
```

### 테스트 실행

```bash
# 특정 스크립트만 테스트
python daily_update/exchange_cron.py

# 통합 테스트
python daily_update/main.py
```

## 📝 라이선스

MIT License

## 🤝 기여

이슈나 PR은 언제나 환영합니다!

## 📞 문의

문제가 발생하면 Issue를 등록해주세요.