import csv
import os
from unittest.mock import patch

from bs4 import BeautifulSoup

from app import scraper, settings

product_details = scraper.ProductDetails(
    url="https://www.google.com",
    title="Test Title",
    description="Test Description",
    final_price="$18.50",
    rating="4.5",
    seller_name="Test Seller Name",
    main_image_url="https://www.google.com",
)

TEMP_FOLDER_NAME = "temp_folder"


def test_append_product_details_to_csv():
    """Product details row should be appended in file"""
    file_path = f"{TEMP_FOLDER_NAME}/test.csv"
    try:
        os.mkdir(TEMP_FOLDER_NAME)
        scraper.append_product_details_to_csv(product_details=product_details, csv_file_path=file_path)

        with open(file_path, "r") as f:
            reader = csv.reader(f)
            file_contents = list(reader)

        assert file_contents == [
            ["url", "title", "description", "final_price", "rating", "seller_name", "main_image_url"],
            [
                "https://www.google.com",
                "Test Title",
                "Test Description",
                "$18.50",
                "4.5",
                "Test Seller Name",
                "https://www.google.com",
            ],
        ]

    finally:
        # cleanup
        os.remove(file_path)
        os.rmdir(TEMP_FOLDER_NAME)


@patch("app.scraper.scrape_single_page_product_urls")
def test_scrape_product_urls(mock_single_page_product_urls):
    """Exactly <product_count> product should be returned"""
    page_size = 30
    product_count = 1171
    max_page_size = settings.NEWEGG_PRODUCT_CATALOG_LAST_PAGE_NUMBER
    mock_responses = []
    for page in range(max_page_size):
        mock_responses.append([f"www.test-url-{page*page_size+ind}.com" for ind in range(page_size)])

    mock_single_page_product_urls.side_effect = mock_responses
    urls = scraper.scrape_product_urls(
        product_count=product_count, page_size=page_size, requests_delay=1, first_page_number=1
    )
    assert mock_single_page_product_urls.call_count == 40  # 1171 products = 40 requests * 30 products each page
    assert urls[0] == "www.test-url-0.com"
    assert urls[-1] == f"www.test-url-{product_count-1}.com"


@patch("app.scraper.get_page_structure")
def test_scrape_single_page_product_urls_empty(mock_get_page_structure):
    """Empty list should be returned if <div id="Product_List"> is not present"""
    mock_get_page_structure.return_value = BeautifulSoup("<p>Test</p>", "html.parser")
    res = scraper.scrape_single_page_product_urls(page_number=1, page_size=10, requests_delay=1)
    assert res == []


def test_find_product_description():
    product_main_section = BeautifulSoup(
        """
        <div class="product-bullets">
            <ul>
                <li>Desc1.</li>
                <li>Desc2.</li>
                <li>Desc3.</li>
            </ul>
        </div>
        """,
        "html.parser",
    )
    description = scraper.find_product_description(product_main_section)
    assert description == "Desc1. Desc2. Desc3."


def test_find_product_rating_na():
    product_page_main_section = BeautifulSoup("<div> </div>", "html.parser")
    rating = scraper.find_product_rating(product_page_main_section=product_page_main_section)
    assert rating == "N/A"


def test_find_product_rating_valid():
    expected_rating = "4.2"
    product_page_main_section = BeautifulSoup(
        f"""<div class="product-rating"> <i title="{expected_rating} out of 5"></i></div>""", "html.parser"
    )
    rating = scraper.find_product_rating(product_page_main_section=product_page_main_section)
    assert rating == expected_rating


def test_find_product_seller_name():
    expected_name = "SellerName"
    page_buy_section = BeautifulSoup(
        f"""
            <div class="product-seller">
            <a href="test">Sold & Shipped by {expected_name}</a>
            </div>
        """,
        "html.parser",
    )
    name = scraper.find_product_seller_name(page_buy_section=page_buy_section)
    assert name == expected_name
