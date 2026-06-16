from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import uvicorn

from app.api.fastapi_app import create_app
from app.collector.binance import BinanceFuturesCollector
from app.collector.bitget import BitgetFuturesCollector
from app.config.settings import Settings
from app.database.json_repository import JSONRepository
from app.ranking.ranker import RankingEngine
from app.report.image_report import ImageReportGenerator
from app.report.text_report import render_text_report
from app.telegram.publisher import TelegramPublisher
from app.utils.git_versioning import GitVersioner


def run_scan(settings: Settings) -> None:
    repository = JSONRepository(settings.data_dir)
    repository.migrate()
    collector = create_collector(settings)
    if isinstance(collector, BitgetFuturesCollector):
        symbols = collector.discover_symbols(settings.min_quote_volume, settings.min_listing_days)
    else:
        symbols = collector.discover_symbols(settings.min_quote_volume)
    btc = collector.fetch_series("BTCUSDT", settings.scan_interval)
    if repository.has_scan(btc.latest.close_time):
        print(f"Scan already processed: {btc.latest.close_time.isoformat()}")
        return

    markets = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(collector.fetch_series, symbol, settings.scan_interval): symbol for symbol in symbols}
        for future in as_completed(futures):
            markets.append(future.result())

    report = RankingEngine().rank(
        btc=btc,
        markets=markets,
        previous_top10=repository.previous_top10(),
        previous_streaks=repository.previous_streaks(),
        leading_scores=repository.leading_scores(),
    )
    repository.save_report(report)

    text = render_text_report(report)
    image_path = ImageReportGenerator(settings.report_dir).generate(report)
    telegram_sent = TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id).publish(text, image_path)
    if settings.enable_git_versioning:
        GitVersioner(remote=settings.git_remote, branch=settings.git_branch).commit_and_push(
            f"Update scan data {report.scan_time.isoformat()}"
        )
    print(text)
    print(f"Telegram sent: {telegram_sent}")
    if image_path:
        print(f"Image report: {image_path}")


def create_collector(settings: Settings) -> BinanceFuturesCollector | BitgetFuturesCollector:
    if settings.exchange == "bitget":
        return BitgetFuturesCollector(settings.bitget_base_url, settings.bitget_product_type)
    if settings.exchange == "binance":
        return BinanceFuturesCollector(settings.binance_fapi_base_url)
    raise ValueError(f"Unsupported exchange: {settings.exchange}")


def serve(settings: Settings, host: str, port: int) -> None:
    repository = JSONRepository(settings.data_dir)
    repository.migrate()
    print(f"Serving API at http://{host}:{port}")
    uvicorn.run(create_app(repository), host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan")
    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    settings = Settings.from_env()
    if args.command == "scan":
        run_scan(settings)
    elif args.command == "serve":
        serve(settings, args.host, args.port)


if __name__ == "__main__":
    main()
