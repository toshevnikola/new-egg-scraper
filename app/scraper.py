import csv
import os
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

import settings
from app import logger


@dataclass
class ProductDetails:
    url: str
    title: str
    description: str
    final_price: str
    rating: float | None
    seller_name: str
    main_image_url: str


def append_product_details_to_csv(product_details: ProductDetails, csv_file_path: str):
    parent_dir_name = os.path.dirname(csv_file_path)
    os.makedirs(parent_dir_name, exist_ok=True)

    file_exists = os.path.exists(csv_file_path)
    with open(csv_file_path, "a") as f:
        writer = csv.writer(f)
        product_details_attr_dict = vars(product_details)
        if not file_exists:
            writer.writerow(list(product_details_attr_dict.keys()))
        writer.writerows([product_details_attr_dict.values()])


def fhir_request_with_retries(method: str, url: str, **kwargs):
    response = requests.request(method, url, **kwargs)
    response.raise_for_status()
    return response


def get_page_structure(url: str, requests_delay: float) -> BeautifulSoup:
    time.sleep(requests_delay)
    response = requests.get(url)
    response.raise_for_status()
    page_content = response.content
    soup = BeautifulSoup(page_content, "html.parser")
    return soup


def scrape_single_page_product_urls(page_number: int, page_size: int, requests_delay: float) -> list[str]:
    """
    Retrieve URL for <page_size> products shown on <page_number>

    Args:
        page_number: page to scrape urls for
        page_size: number of products shown per page

    Returns:
        list of product urls
    """
    page_url = settings.NEWEGG_DEALS_PAGE_URL.format(page_number=page_number, page_size=page_size)
    try:
        soup = get_page_structure(page_url, requests_delay=requests_delay)
    except HTTPError as e:
        raise e

    product_list = soup.find("div", {"id": "Product_List"})
    return [product.find_next("a").get("href") for product in product_list]


def scrape_product_urls(product_count: int, page_size: int, requests_delay: float, first_page_number: int) -> list[str]:
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
    page_number = first_page_number
    while total_scraped_urls < product_count:
        if page_number > settings.NEWEGG_PRODUCT_CATALOG_LAST_PAGE_NUMBER:
            logger.warning("Reached product catalog page limit.")
            break

        try:
            page_product_urls = scrape_single_page_product_urls(
                page_number=page_number,
                page_size=page_size,
                requests_delay=requests_delay,
            )
        except HTTPError as e:
            logger.error(f"Skipping page number {page_number}. Error: {str(e)}")
            page_product_urls = []
        product_urls.extend(page_product_urls)
        total_scraped_urls += len(page_product_urls)
        page_number += 1
        return product_urls[:product_count]


def get_product_description(soup: BeautifulSoup) -> str:
    description_items = soup.find("div", {"class": "product-bullets"}).find_all("li")
    return " ".join([item.text for item in description_items])


def get_product_rating(soup: BeautifulSoup) -> str | None:
    try:
        review_title_attr = soup.find("div", {"class": "product-rating"}).find("i").attrs.get("title")
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


def scrape_product_details(url: str, requests_delay: float) -> ProductDetails:
    soup = get_page_structure(url=url, requests_delay=requests_delay)

    page_main_section = soup.find("div", {"class": "product-wrap"})
    page_img_section = soup.find("div", {"class": "product-view"})
    page_buy_section = soup.find("div", {"class": "product-buy-box"})

    product_title = page_main_section.find("h1", {"class": "product-title"}).text
    product_description = get_product_description(page_main_section)
    product_rating = get_product_rating(page_main_section)

    product_main_image_url = page_img_section.find("img", {"class": "product-view-img-original"}).attrs.get("src")

    product_final_price = page_buy_section.find("li", {"class": "price-current"}).text
    product_seller_name = get_product_seller_name(page_buy_section)

    product_details = ProductDetails(
        url=url,
        title=product_title,
        description=product_description,
        final_price=product_final_price,
        rating=product_rating,
        seller_name=product_seller_name,
        main_image_url=product_main_image_url,
    )
    return product_details


def scrape_and_store_products(
    file_path: str,
    product_count: int,
    page_size: int,
    requests_delay: float,
    first_page_number: int,
):
    product_urls = scrape_product_urls(
        product_count=product_count,
        page_size=page_size,
        requests_delay=requests_delay,
        first_page_number=first_page_number,
    )
    for count, product_url in enumerate(product_urls):
        try:
            product_details = scrape_product_details(product_url, requests_delay=requests_delay)
            append_product_details_to_csv(product_details=product_details, csv_file_path=file_path)
            logger.debug(count)
        except HTTPError as e:
            logger.error(f"Skipping product {product_url}. Error: {str(e)}")
