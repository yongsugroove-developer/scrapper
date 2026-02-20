from __future__ import annotations

import argparse
import logging
import sys

from scrapper.config import load_settings
from scrapper.pipeline import run_daily_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily keyword crawler and email digest")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run crawl and summary without sending email or writing sent-history",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    args = parse_args()

    try:
        settings = load_settings()
        report = run_daily_pipeline(settings, dry_run=args.dry_run)
    except Exception as exc:
        logging.exception("Pipeline failed: %s", exc)
        return 1

    logging.info(
        "Run completed | dry_run=%s searched=%s selected=%s summarized=%s sent_email=%s",
        report.dry_run,
        report.searched_count,
        report.selected_count,
        report.summarized_count,
        report.sent_email,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

