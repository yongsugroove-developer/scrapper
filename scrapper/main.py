from __future__ import annotations

import argparse
import logging
import sys
import warnings

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily keyword crawler and email digest")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run crawl and summary without sending email or writing sent-history",
    )
    return parser.parse_args()


def main() -> int:
    warnings.filterwarnings(
        "ignore",
        message=r"This package \(`duckduckgo_search`\) has been renamed to `ddgs`!.*",
        category=RuntimeWarning,
    )
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.simplefilter("ignore", ResourceWarning)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("duckduckgo_search").setLevel(logging.WARNING)
    logging.getLogger("trafilatura").setLevel(logging.CRITICAL)
    logging.getLogger("trafilatura.utils").setLevel(logging.CRITICAL)
    logging.getLogger("htmldate").setLevel(logging.CRITICAL)

    from scrapper.config import load_settings
    from scrapper.pipeline import run_daily_pipeline

    args = parse_args()

    try:
        settings = load_settings()
        report = run_daily_pipeline(settings, dry_run=args.dry_run)
    except Exception as exc:
        logging.exception("Pipeline failed: %s", exc)
        return 1

    logging.info(
        (
            "Run completed | dry_run=%s searched=%s selected=%s summarized=%s "
            "summary_success=%s summary_failed=%s summary_success_rate=%.2f "
            "summary_failed_reasons=%s sent_email=%s"
        ),
        report.dry_run,
        report.searched_count,
        report.selected_count,
        report.summarized_count,
        report.summary_success_count,
        report.summary_failed_count,
        report.summary_success_rate,
        dict(report.summary_failed_reason_counts),
        report.sent_email,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

