from pathlib import Path

DEFAULT_PRODUCT_COUNT = 500
DEFAULT_PAGE_SIZE = 96
DEFAULT_START_PAGE_NUMBER = 1
DEFAULT_REQUEST_DELAY_IN_SEC = 1
NEWEGG_DEALS_PAGE_URL = (
    "https://www.newegg.com/Newegg-Deals/EventSaleStore/ID-9447/Page-{page_number}?PageSize={page_size}"
)
NEWEGG_PRODUCT_CATALOG_LAST_PAGE_NUMBER = 100

DATA_DIR = Path(__file__).parent.parent / "data"
