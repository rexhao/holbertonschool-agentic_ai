
import requests
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def scrape_website(url):
    """Scrape a webpage and extract article information."""

    # Validate URL
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        logging.error("Invalid URL: %s", url)
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PythonScraper/1.0)"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # Extract article titles and links
        articles = soup.find_all("h2")

        for article in articles:
            title = article.get_text(strip=True)

            link_tag = article.find("a")
            link = link_tag.get("href") if link_tag else ""

            if title:
                results.append({
                    "title": title,
                    "link": link,
                    "scraped_at": datetime.now().isoformat()
                })

        logging.info(
            "Successfully scraped %s. Found %d records.",
            url, len(results)
        )

        return results

    except requests.exceptions.Timeout:
        logging.error("Request timed out: %s", url)

    except requests.exceptions.ConnectionError:
        logging.error("Connection failed: %s", url)

    except requests.exceptions.HTTPError as error:
        logging.error("HTTP error: %s", error)

    except requests.exceptions.RequestException as error:
        logging.error("Request error: %s", error)

    except Exception as error:
        logging.exception("Unexpected scraping error: %s", error)

    return []


def save_to_csv(data, filename="scraped_data.csv"):
    """Save scraped records into a CSV file."""

    if not data:
        logging.warning("No data available to save.")
        return

    try:
        with open(
            filename,
            mode="w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=["title", "link", "scraped_at"]
            )

            writer.writeheader()
            writer.writerows(data)

        logging.info("Data successfully saved to %s", filename)
        print(f"Saved {len(data)} records to {filename}")

    except (OSError, csv.Error) as error:
        logging.error("Failed to save CSV: %s", error)


# Main execution
if __name__ == "__main__":

    target_url = "https://example.com"

    scraped_data = scrape_website(target_url)

    save_to_csv(scraped_data)

    print("Scraping process completed.")
