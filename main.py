import os
import time
import csv
import requests
from bs4 import BeautifulSoup


def scrape_single_page_product_urls(page_number: int, page_size: int = 96) -> list[str]:
    """
    Retrieve URL for <page_size> products shown on <page_number>

    Args:
        page_number: page to scrape urls for
        page_size: number of products shown per page

    Returns:
        list of product urls
    """
    page_content = requests.get(
        f"https://www.newegg.com/Newegg-Deals/EventSaleStore/ID-9447/Page-{page_number}?PageSize={page_size}"
    ).content
    soup = BeautifulSoup(page_content, "html.parser")
    product_list = soup.find("div", {"id": "Product_List"})
    return [product.find_next("a").get("href") for product in product_list]


def scrape_product_urls(product_count: int, page_size: int) -> list[str]:
    """
    Retrieve URLs for <product_count> products

    Iterates all the pages from 1 to 100 and scrapes the urls of all the listed products
    until total of <product_count> product URLs are collected

    Args:
        product_count: number of products to retrieve URLs for
        page_size: number of products shown per page

    Returns:
        list of product urls with max length of <product_count>
    """
    product_urls = []
    total_scraped_urls = 0
    page_number = 1
    while total_scraped_urls < product_count:
        time.sleep(1)
        page_product_urls = scrape_single_page_product_urls(
            page_number=page_number, page_size=page_size
        )
        product_urls.extend(page_product_urls)
        total_scraped_urls += len(page_product_urls)
        page_number += 1
        if page_number == 100:
            break
    return product_urls[:product_count]


def store_urls_as_csv(urls: list[str], csv_file_path: str, overwrite_file: bool = True):
    parent_dir_name = os.path.dirname(csv_file_path)
    os.makedirs(parent_dir_name, exist_ok=True)

    if os.path.exists(csv_file_path) and not overwrite_file:
        raise FileExistsError(
            "File with the same path already exists. Set overwrite_file=True to overwrite it."
        )
    with open(csv_file_path, "w") as f:
        writer = csv.writer(
            f,
        )
        writer.writerow(["product_url"])
        writer.writerows([[url] for url in urls])


def load_product_urls_from_csv(file_path: str) -> tuple[str, list[str]]:
    with open(file_path, "r") as f:
        reader = csv.reader(
            f,
        )
        column_name = next(reader)[0]
        product_urls = [product[0] for product in reader]
    return column_name, product_urls


if __name__ == "__main__":
    PRODUCT_COUNT = 25
    FILE_PATH = f"data/{str(PRODUCT_COUNT)}_products.csv"
    PAGE_SIZE = 32
    all_urls = scrape_product_urls(product_count=PRODUCT_COUNT, page_size=PAGE_SIZE)
    store_urls_as_csv(
        all_urls,
        csv_file_path=FILE_PATH,
        overwrite_file=True,
    )
    column_name, product_urls = load_product_urls_from_csv(file_path=FILE_PATH)
