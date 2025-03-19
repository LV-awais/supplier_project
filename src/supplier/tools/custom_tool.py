import asyncio

import time
from crewai.tools import BaseTool

from dotenv import load_dotenv
load_dotenv()

from scrapfly import ScrapflyClient, ScrapeConfig, ScrapeApiResponse
# Initialize the Exa tool with your API key

import json
import os
import requests
from urllib.parse import urlparse

from crewai.tools import BaseTool

import os
import requests
from typing import List


class SerperSearchTool(BaseTool):
    name: str = "SerperSearchTool"
    description: str = (
        "Fetch up to 5 pages of Google search results using the Serper API. "
        "Retrieves verified suppliers, their websites, descriptions, and metadata."
    )

    def _run(self, topic: str, country: str, max_pages: int = 1, queries: List[str] = None):
        """
        Searches for verified suppliers using Serper API with multi-page retrieval.
        """
        api_key = os.getenv("SERPER_API_KEY")  # Ensure API key is set in environment
        base_url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

        # List of domains to exclude
        excluded_domains = ["reddit.com", "quora.com","linkedin.com", "ebay.com", "amazon.com", "walmart.com", "newegg.com","BestBuy.com"]

        all_results = []
        for query in queries:
            for page in range(max_pages):
                # Construct the 'q' parameter to include the query and exclude specified domains
                q_param = query + " " + " ".join([f"-site:{domain}" for domain in excluded_domains])

                payload = {
                    "q": q_param,
                    "location": country,
                    "num": 10,  # Fetch 10 results per page
                    "page": page * 10  # Adjust start index for pagination
                }

                response = requests.post(base_url, json=payload, headers=headers)

                if response.status_code == 200:
                    response_data = response.json()
                    search_location = response_data.get("searchParameters", {}).get("location", country)

                    # Extract supplier results
                    results = response_data.get("organic", [])
                    for result in results:
                        supplier_data = {
                            "business_name": result.get("title"),
                            "url": result.get("link"),
                            "description": result.get("snippet"),
                            "metadata": {
                                "location": search_location,
                                "sitelinks": [site.get("link") for site in result.get("sitelinks", [])]
                            }
                        }
                        all_results.append(supplier_data)
                else:
                    print(f"⚠️ Error fetching page {page + 1} for query '{query}': {response.text}")

        return all_results


scrapfly = ScrapflyClient(key=os.getenv("SCRAPFLY_API_KEY"))

# Base configuration for Scrapfly requests
BASE_CONFIG = {
    "asp": True,      # Helps to avoid Zoominfo blocking
    "country": "US"   # Sets proxy location to US
}

def parse_company(response: ScrapeApiResponse) -> dict:
    """
    Parse the company page to extract the JSON data.
    The JSON data is assumed to be in a script tag with an ID of either
    'app-root-state' or 'ng-state', and the JSON structure contains a key "pageData".
    """
    data_text = response.selector.css("script#app-root-state::text").get()
    if not data_text:
        data_text = response.selector.css("script#ng-state::text").get()
    if not data_text:
        raise ValueError("No company data script found.")
    data = json.loads(data_text)
    return data["pageData"]

async def scrape_company(url: str) -> dict:
    """
    Asynchronously scrape the given company URL using Scrapfly and return the raw JSON data.
    """
    response = await scrapfly.async_scrape(ScrapeConfig(url, **BASE_CONFIG))
    return parse_company(response)

class CombinedTool(BaseTool):
    name: str = "CombinedTool"
    description: str = (
        "Fetches domain age for a list of URLs using the Apivoid API, retrieves Trustpilot review data, "
        "and scrapes company details from ZoomInfo by leveraging SerperAPI and Scrapfly."
    )

    def _run(self, suppliers: list[dict] = None) -> str:
        """
        Retrieves domain age details, Trustpilot review data, and company data in one run.

        Parameters:
            suppliers (list): A list of dictionaries containing business information,
                              including the URL for domain age lookup.

        Returns:
            str: A JSON string containing domain age information, Trustpilot review data,
                 and scraped company data.
        """
        results = {}

        if suppliers:
            # Environment variables and headers setup


            apivoid_api_key = os.getenv("APIVOID_API_KEY")
            serper_api_key = os.getenv("SERPER_API_KEY")
            headers = {
                "X-API-KEY": serper_api_key,
                "Content-Type": "application/json"
            }

            domain_age_results = {}
            trustpilot_results = {}
            company_data_results = {}

            for supplier in suppliers:
                try:
                    url = supplier["url"]
                    parsed_url = urlparse(url)
                    domain_parts = parsed_url.netloc.split('.')

                    # Handle subdomains (e.g., www.example.com -> example.com)
                    if len(domain_parts) > 2:
                        main_domain = ".".join(domain_parts[-2:])
                    else:
                        main_domain = parsed_url.netloc

                    # Derive business name (can be adjusted as needed)
                    business_name = main_domain.split('.')[0]

                    # ------------------------------
                    # Part 1: Domain Age via Apivoid API
                    # ------------------------------
                    host = parsed_url.netloc.split(':')[0]  # Remove port if present
                    apivoid_url = f"https://endpoint.apivoid.com/domainage/v1/pay-as-you-go/?key={apivoid_api_key}&host={host}"
                    response = requests.get(apivoid_url)
                    time.sleep(1)
                    response.raise_for_status()
                    data = response.json()
                    domain_age = data.get('data', {}).get('domain_age_in_years', '')
                    domain_age_results[url] = domain_age

                    # ------------------------------
                    # Part 2: Trustpilot Reviews via SerperAPI
                    # ------------------------------
                    tp_search_payload = json.dumps({
                        "q": f"{business_name} site:trustpilot.com",
                        "num": 10,
                        "location": "United States"
                    })
                    tp_search_url = "https://google.serper.dev/search"
                    tp_response = requests.post(tp_search_url, headers=headers, data=tp_search_payload)
                    time.sleep(1)
                    tp_search_data = tp_response.json()

                    trustpilot_link = None
                    for result in tp_search_data.get("organic", []):
                        link = result.get("link", "")
                        if "trustpilot.com" in link and business_name.lower() in link.lower():
                            trustpilot_link = link
                            break

                    if trustpilot_link:
                        # Scrape the Trustpilot page
                        scrape_payload = json.dumps({"url": trustpilot_link})
                        scrape_url = "https://google.serper.dev/scrape"
                        scrape_response = requests.post(scrape_url, headers=headers, data=scrape_payload)
                        time.sleep(1)
                        scrape_data = scrape_response.json()

                        og_title = scrape_data.get("metadata", {}).get("og:title", "N/A")
                        aggregate_rating = None
                        for item in scrape_data.get("jsonld", {}).get("@graph", []):
                            if item.get("@type") == "AggregateRating":
                                aggregate_rating = item
                                break
                        review_count = aggregate_rating.get("reviewCount") if aggregate_rating else None

                        local_business_info = {}
                        for item in scrape_data.get("jsonld", {}).get("@graph", []):
                            if item.get("@type") == "LocalBusiness":
                                local_business_info = {
                                    "name": item.get("name"),
                                    "description": item.get("description"),
                                    "address": item.get("address", {})
                                }
                                break

                        trustpilot_results[business_name] = {
                            "og_title": og_title,
                            "aggregate_rating": aggregate_rating,
                            "review_count": review_count,
                            "local_business_info": local_business_info
                        }
                    else:
                        trustpilot_results[business_name] = {"error": f"No Trustpilot page found for {business_name}."}

                    # ------------------------------
                    # Part 3: Company Data via Scrapfly & ZoomInfo
                    # ------------------------------
                    # Use SerperAPI to search for a ZoomInfo URL using the business name
                    zi_search_payload = json.dumps({
                        "q": f"{business_name} site:zoominfo.com",
                        "num": 10,
                        "location": "United States"
                    })
                    zi_search_response = requests.post(tp_search_url, headers=headers, data=zi_search_payload)
                    zi_search_data = zi_search_response.json()

                    zoominfo_link = None
                    for result in zi_search_data.get("organic", []):
                        link = result.get("link", "")
                        if "zoominfo.com" in link:
                            zoominfo_link = link
                            break

                    if zoominfo_link:
                        try:
                            # Run the asynchronous Scrapfly scraping synchronously.
                            company_data = asyncio.run(scrape_company(zoominfo_link))
                        except Exception as scrape_error:
                            company_data = {"error": f"Scraping failed: {str(scrape_error)}"}
                    else:
                        company_data = {"error": f"No ZoomInfo page found for {business_name}."}

                    company_data_results[business_name] = company_data

                except Exception as e:
                    error_message = f"Error processing supplier {supplier.get('url', 'N/A')}: {str(e)}"
                    domain_age_results[url] = f"Error: {str(e)}"
                    trustpilot_results[business_name] = {"error": str(e)}
                    company_data_results[business_name] = {"error": str(e)}

            # Aggregate all results into a single JSON structure
            results = {
                "domain_age": domain_age_results,
                "trustpilot_reviews": trustpilot_results,
                "company_data": company_data_results
            }

        return json.dumps(results, indent=2)
