import csv
import os
import time
from dataclasses import dataclass
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

from app import settings
from app.logger import logger


@dataclass
class ProductDetails:
    url: str
    title: str
    description: str
    final_price: str
    rating: str
    seller_name: str
    main_image_url: str


def append_product_details_to_csv(product_details: ProductDetails, csv_file_path: str) -> None:
    """
    Append product details row in <csv_file_path>

    If not exists, the file is created with ProductDetails attrs column names.
    Column names are ordered in the same fashion as defined in ProductDetails class

    Args:
        product_details: object containing scraped details of a product
        csv_file_path: path to the csv where new product will be added

    Returns:
        None
    """
    parent_dir_name = os.path.dirname(csv_file_path)
    os.makedirs(parent_dir_name, exist_ok=True)

    file_exists = os.path.exists(csv_file_path)
    with open(csv_file_path, "a") as f:
        writer = csv.writer(f)
        product_details_attr_dict = vars(product_details)
        if not file_exists:
            writer.writerow(list(product_details_attr_dict.keys()))
        writer.writerows([product_details_attr_dict.values()])


def get_page_structure(url: str, requests_delay: float) -> BeautifulSoup:
    """
    Send a request to retrieve page structure and convert it to a BeautifulSoup parsed document

    Args:
        url: url to retrieve contents from
        requests_delay: time to sleep before sending the request

    Raises:
        HTTPError if the request status response is 4xx or 5xx

    Returns:
        BeautifulSoup object
    """
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
        requests_delay: Delay between subsequent requests in seconds

    Raises:
        HTTPError

    Returns:
        list of product urls
    """
    page_url = settings.NEWEGG_DEALS_PAGE_URL.format(page_number=page_number, page_size=page_size)
    soup = get_page_structure(page_url, requests_delay=requests_delay)
    product_list = soup.find("div", {"id": "Product_List"})
    if not product_list:
        logger.warning(f"Product list not available for page {page_url}")
        return []

    urls = []
    pprint(product_list)
    for product in product_list:
        a_tag = product.find_next("a")
        if a_tag:
            urls.append(a_tag.get("href"))

    return urls


def scrape_product_urls(product_count: int, page_size: int, requests_delay: float, first_page_number: int) -> list[str]:
    """
    Retrieve URLs for <product_count> products

    Iterates all the pages from <first_page_number> to <NEWEGG_PRODUCT_CATALOG_LAST_PAGE_NUMBER>
    and scrapes the urls of all the listed products
    until total of <product_count> product URLs are collected

    Args:
        product_count: number of products to retrieve URLs for
        page_size: number of products shown per page
        requests_delay: Delay between subsequent requests in seconds
        first_page_number: Starting page when iterating through the product catalog

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


def find_product_description(product_page_main_section: BeautifulSoup) -> str:
    """
    Find the product description from the main section of the product page

    Args:
        product_page_main_section: parsed DOM document containing single section

    Returns:
        Text containing all the description items separated with white space
    """
    try:
        description_items = product_page_main_section.find("div", {"class": "product-bullets"}).find_all("li")
    except Exception as e:
        logger.warning(str(e))
        description_items = []
    return " ".join([item.text for item in description_items])


def find_product_rating(product_page_main_section: BeautifulSoup) -> str:
    """
    Find the product rating from the main section of the product page

    Args:
        product_page_main_section: parsed DOM document containing single section

    Returns:
        Text field containing the product rating if exists or N/A
    """
    try:
        review_title_attr = (
            product_page_main_section.find("div", {"class": "product-rating"}).find("i").attrs.get("title")
        )
    except Exception:
        return "N/A"
    if not review_title_attr:
        return "N/A"
    rating = review_title_attr.split(" out of ")[0]
    try:
        float(rating)
        return rating
    except ValueError:
        return "N/A"


def find_product_seller_name(page_buy_section: BeautifulSoup):
    """
    Find the product seller name in the buy section of the product page

    Args:
        page_buy_section: parsed DOM document containing single section

    Returns:
        Name of the seller
    """
    try:
        seller_name = page_buy_section.find("div", {"class": "product-seller"}).find("a").text
        seller_name = seller_name.replace("Sold & Shipped by ", "")
    except Exception as e:
        logger.warning(str(e))
        seller_name = "N/A"
    return seller_name


def scrape_product_details(url: str, requests_delay: float) -> ProductDetails:
    """
    Scrape product details for a given product url

    Args:
        url: Url to scrape product details for
        requests_delay: Delay between subsequent requests

    Raises:
        HTTPError

    Returns:
        ProductDetails object

    """
    soup = get_page_structure(url=url, requests_delay=requests_delay)

    page_main_section = soup.find("div", {"class": "product-wrap"})
    page_img_section = soup.find("div", {"class": "product-view"})
    page_buy_section = soup.find("div", {"class": "product-buy-box"})

    product_title = page_main_section.find("h1", {"class": "product-title"}).text
    product_description = find_product_description(page_main_section)
    product_rating = find_product_rating(page_main_section)

    product_main_image_url = page_img_section.find("img", {"class": "product-view-img-original"}).attrs.get("src")

    product_final_price = page_buy_section.find("li", {"class": "price-current"}).text
    product_seller_name = find_product_seller_name(page_buy_section)

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
) -> None:
    """
    Scrape <product_count> products and store them in <file_path>

    Args:
        file_path: File path to store product
        product_count: Number of products to scrape and store
        page_size: Number of products per page when listing the product catalog
        requests_delay: Delay between subsequent requests in seconds
        first_page_number: Starting page when iterating through the product catalog

    Returns:
        None
    """
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
