# AI Crypto Relative Strength Scanner

BTC 대비 강한 Bitget USDT Futures 알트코인을 4시간봉 기준으로 스캔하고, AI 점수/랭킹/PNG 리포트/Telegram 게시/GitHub Pages 대시보드 데이터를 생성하는 Python 프로젝트입니다.

## 주요 기능

- Bitget USDT-M Futures 4시간봉 기반 자동 대상 갱신
- `EXCHANGE=binance` 설정 시 Binance USDT-M Futures도 사용 가능
- BTC 대비 상대강도 계산
- 최근 5봉 누적 강도, 거래량 증가, EMA 추세, 변동성 안정성 기반 AI 점수
- TOP10/TOP20, 신규 진입, 연속 강세, 알트 시즌 지수 산출
- JSON 파일 저장 및 Git 버전 관리
- Telegram 텍스트 및 이미지 리포트 게시
- FastAPI 기반 로컬 API 제공
- GitHub Pages 정적 대시보드 제공

## 빠른 시작

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main scan
python -m app.main serve --host 127.0.0.1 --port 8000
```

스캔 후 주요 산출물은 `data/` 아래에 저장됩니다.

- `data/history/YYYY/MM/DD/HHMM.json`
- `data/ranking/latest.json`
- `data/ranking/top10.json`
- `data/ranking/top20.json`
- `data/ranking/leading.json`
- `data/ranking/altscore.json`
- `data/dashboard/dashboard.json`
- `data/dashboard/index.html`
- `data/report/YYYYMMDD_HHMM.png`

## 환경변수

`.env.example`을 참고하세요.

- `DATA_DIR`: 기본값 `data`
- `EXCHANGE`: 기본값 `bitget`
- `BITGET_BASE_URL`: 기본값 `https://api.bitget.com`
- `BITGET_PRODUCT_TYPE`: 기본값 `USDT-FUTURES`
- `BINANCE_FAPI_BASE_URL`: Binance 사용 시 기본값 `https://fapi.binance.com`
- `REPORT_DIR`: 기본값 `data/report`
- `ENABLE_GIT_VERSIONING`: `true`이면 스캔 후 `data/`를 commit/push
- `GIT_REMOTE`, `GIT_BRANCH`: Git push 대상
- `TELEGRAM_BOT_TOKEN`: Telegram Bot Token
- `TELEGRAM_CHAT_ID`: 비공개 채널/채팅 ID
- `MIN_QUOTE_VOLUME`: 24시간 최소 USDT 거래대금
- `MIN_LISTING_DAYS`: 상장 초기 종목 제외 기준

## API

- `GET /api/top10`
- `GET /api/top20`
- `GET /api/latest`
- `GET /api/history/{symbol}`
- `GET /api/dashboard`
- `GET /api/altscore`

## 테스트

```bash
pytest
```

## GitHub Actions

`.github/workflows/scan.yml`은 KST 01:00, 05:00, 09:00, 13:00, 17:00, 21:00에 맞춰 UTC cron으로 실행됩니다. GitHub Actions 저장소 환경변수/시크릿에 Telegram 값을 등록하면 자동 게시가 가능합니다.

GitHub Pages는 `data/dashboard/index.html` 또는 별도 Pages publish 경로에서 JSON 파일을 읽는 방식으로 운영할 수 있습니다.

## 계산 메모

PRD V2.1의 Relative Strength 수식 표기는 `AltReturn * BTCReturn`로 되어 있지만, 예시는 `AltReturn - BTCReturn`입니다. 구현은 예시와 V2 정의에 맞춰 `AltReturn - BTCReturn`을 사용합니다.
