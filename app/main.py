import argparse
from datetime import datetime

from app import scraper, settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Newegg scraper argument parser.")
    parser.add_argument(
        "--product_count",
        type=int,
        help="Number of product to scrape",
        default=settings.DEFAULT_PRODUCT_COUNT,
    )
    parser.add_argument(
        "--page_size",
        type=int,
        help="Product catalog page size",
        choices=[32, 60, 96],
        default=settings.DEFAULT_PAGE_SIZE,
    )
    parser.add_argument(
        "--first_page_number",
        type=int,
        help="Page number to start from",
        default=settings.DEFAULT_START_PAGE_NUMBER,
    )
    parser.add_argument(
        "--requests_delay",
        type=float,
        help="Delay between requests",
        default=settings.DEFAULT_REQUEST_DELAY_IN_SEC,
    )
    parser.add_argument(
        "--file_path",
        type=str,
        help="Path to store scraped data",
        default=settings.DEFAULT_FILE_PATH.format(timestamp=int(datetime.now().timestamp())),
    )
    args = parser.parse_args()

    scraper.scrape_and_store_products(
        file_path=args.file_path,
        product_count=args.product_count,
        page_size=args.page_size,
        first_page_number=args.first_page_number,
        requests_delay=args.requests_delay,
    )
