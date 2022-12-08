from bs4 import BeautifulSoup
import requests


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


def scrape_product_urls(product_count: int) -> list[str]:
    """
    Retrieve URLs for <product_count> products

    Iterates all the pages from 1 to 100 and scrapes the urls of all the listed products
    until total of <product_count> product URLs are collected

    Args:
        product_count: number of products to retrieve URLs for

    Returns:
        list of product urls with max length of <product_count>
    """
    product_urls = []
    total_scraped_urls = 0
    page_number = 1
    while total_scraped_urls < product_count:
        page_product_urls = scrape_single_page_product_urls(page_number)
        product_urls.extend(page_product_urls)
        total_scraped_urls += len(page_product_urls)
        page_number += 1
        if page_number == 100:
            break
    return product_urls[:product_count]


if __name__ == "__main__":
    all_urls = scrape_product_urls(product_count=500)
