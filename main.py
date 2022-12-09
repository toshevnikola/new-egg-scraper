import logging
import os
import time
import csv
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.Logger(name="logger", level="INFO")


@dataclass
class ProductInfo:
    url: str
    title: str
    description: str
    final_price: str
    rating: Optional[float]
    seller_name: str
    main_image_url: str


def get_page_structure(url: str) -> BeautifulSoup:
    page_content = requests.get(url).content
    soup = BeautifulSoup(page_content, "html.parser")
    return soup


def scrape_single_page_product_urls(page_number: int, page_size: int = 96) -> list[str]:
    """
    Retrieve URL for <page_size> products shown on <page_number>

    Args:
        page_number: page to scrape urls for
        page_size: number of products shown per page

    Returns:
        list of product urls
    """
    soup = get_page_structure(
        url=f"https://www.newegg.com/Newegg-Deals/EventSaleStore/ID-9447/Page-{page_number}?PageSize={page_size}"
    )
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

def append_product_info_to_csv(product_info: ProductInfo, csv_file_path: str):
    parent_dir_name = os.path.dirname(csv_file_path)
    os.makedirs(parent_dir_name, exist_ok=True)
    file_exists = os.path.exists(csv_file_path)
    with open(csv_file_path, "a") as f:
        writer = csv.writer(f)
        product_info_attr_dict = vars(product_info)
        if not file_exists:
            writer.writerow(list(product_info_attr_dict.keys()))
        writer.writerows([product_info_attr_dict.values()])

def get_product_description(soup: BeautifulSoup) -> str:
    description_items = soup.find("div", {"class": "product-bullets"}).find_all("li")
    return " ".join([item.text for item in description_items])


def get_product_rating(soup: BeautifulSoup) -> str | None:
    try:
        review_title_attr = (
            soup.find("div", {"class": "product-rating"}).find("i").attrs.get("title")
        )
    except AttributeError:
        logger.info("No reviews for product")
        return "N/A"
    if not review_title_attr:
        return "N/A"
    rating = review_title_attr.split(" out of ")[0]
    try:
        float(rating)
        return rating
    except ValueError:
        return "N/A"


def get_product_seller_name(soup: BeautifulSoup):

    seller_name = soup.find("div", {"class": "product-seller"}).find("a").text
    seller_name = seller_name.replace("Sold & Shipped by ", "")
    return seller_name


def scrape_product_details(url: str) -> ProductInfo:
    soup = get_page_structure(url=url)
    page_main_section = soup.find("div", {"class": "product-wrap"})
    page_img_section = soup.find("div", {"class": "product-view"})
    page_buy_section = soup.find("div", {"class": "product-buy-box"})

    product_title = page_main_section.find("h1", {"class": "product-title"}).text
    product_description = get_product_description(page_main_section)
    product_rating = get_product_rating(page_main_section)

    product_main_image_url = page_img_section.find(
        "img", {"class": "product-view-img-original"}
    ).attrs.get("src")

    product_final_price = page_buy_section.find("li", {"class": "price-current"}).text
    product_seller_name = get_product_seller_name(page_buy_section)

    product_info = ProductInfo(
        url=url,
        title=product_title,
        description=product_description,
        final_price=product_final_price,
        rating=product_rating,
        seller_name=product_seller_name,
        main_image_url=product_main_image_url,
    )
    return product_info


if __name__ == "__main__":
    PRODUCT_COUNT = 500
    FILE_PATH = f"data/{str(PRODUCT_COUNT)}_products.csv"
    PAGE_SIZE = 96
    product_urls = scrape_product_urls(product_count=PRODUCT_COUNT, page_size=PAGE_SIZE)
    for ind, product_url in enumerate(product_urls):
        product_info = scrape_product_details(product_url)
        append_product_info_to_csv(product_info=product_info, csv_file_path=FILE_PATH)
        time.sleep(0.2)
