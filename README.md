# NewEgg Product Scraper
Python script to scrape products from https://www.newegg.com/

---

### How it works:
Each script execution will open `All Deals` page and navigate through the pages of the product catalog to collect product URLs.\
Product URLs are stored in-memory and when a total of `num_products` are collected, it will proceed to scrape the details page of the products.\
Details are scraped for each product and appended to a .csv file.

Configurable arguments:
- --num_products - How many product to scrape data for (defaul=500)
- --page_size - How many products per page are shown when navigating through the catalog (default=96)
- --first_page_number - Page number to start collecting products from, e.g --first_page_number=5, will skip pages 1 to 4 (default=1)
- --requests_delay - Delay in seconds before sending a request to retieve a page. Helpful against scraping detectors (default=1)
- --file_path - Output .csv file path (default=data/products_{unix_timestamp}.csv) 


---


### Setup

Clone the repository:
```
git clone https://github.com/toshevnikola/new-egg-scraper
cd new-egg-scraper
```

#### Local env
Few steps are required to run in local env
1. Setup virtal environment
```
python -m venv venv
```
or

```
virtualenv venv
```
2. Activate the virtual environment

Linux:
```
source venv/bin/activate 
```
Windows:
```
venv\Scripts\activate
```
3. Install the requirements
```
pip install -r requirements.txt
```
4. Run scraper
With default args:
```
python app/main.py
```

Overwrite default args:

```
python app/main.py --product_count=100 --page_size=60 --first_page_number=1 --requests_delay=2 
```

#### Docker-compose

Start the scraper as a docker service:

```
docker-compose up
```

Overwrite the default args by adding them as commands in the docker-compose.yaml file

#### Docker run
Start the scraper as a standalone docker container:

```
docker build . -t scraper-app:v1 
```

Run with default args:

```
docker run --rm --volume=./docker-data:/app/data scraper-app:v1
```

Overwrite default args:

```
docker run --rm --volume=./docker-data:/app/data scraper-app:v1 --product_count=100 --page_size=96 --first_page_number=1 --requests_delay=5
```

---

### Testing

Run unit tests
```
python -m pytest app/tests
```

---


### Development

Libraries used for linting and formatting:
- black - Code formatter
- flake8 - Linter
- isort[black] - Import sorter

For consistency run the following commands prior to committing:
```
black app
flake8 app
isort app
```

---

## License

[MIT](https://choosealicense.com/licenses/mit/)
