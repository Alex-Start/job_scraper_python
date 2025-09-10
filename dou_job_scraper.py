import requests
from bs4 import BeautifulSoup
import time
import random
import re

from base_job_scraper import BaseJobScraper
from utils.filters import Filters

class DouJobScraper(BaseJobScraper):
    # Default
    SEARCH_URL = "https://jobs.dou.ua/vacancies/?category=QA"
    AJAX_URL = "https://jobs.dou.ua/vacancies/xhr-load/?category=QA"
    VACANCY_CART = "li.l-vacancy, div.l-vacancy.__hot"
    
    def __init__(self, filters, logger):
        self.filters = filters
        self.logger = logger
        self.page = 1
        self.session = requests.Session()
        self.csrf_token = None
        self.seen_links = set()
    
    def get_logger(self):
        return self.logger
    
    def setup_driver(self):
        pass
    def driver_quit(self):
        pass

    def init_url(self, search_url, ajax_url):
        self.SEARCH_URL = search_url
        self.AJAX_URL = ajax_url

    def fetch_initial_page(self):
        """Load the first page and extract CSRF token."""
        resp = self.session.get(self.SEARCH_URL, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        token_elem = soup.select_one("input[name=csrfmiddlewaretoken]")
        if token_elem:
            self.csrf_token = token_elem["value"]
            self.logger.info(f"CSRF token: {self.csrf_token}")
        return resp.text

    def fetch_page_html(self):
        """Fetch initial page or next AJAX batch."""
        if self.page == 1:
            return self.fetch_initial_page()

        if not self.csrf_token:
            raise RuntimeError("CSRF token missing. Call fetch_initial_page() first.")

        self.logger.info(f"🔎 Fetching next {20} jobs from AJAX")
        resp = self.session.post(
            self.AJAX_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": self.SEARCH_URL,
                "X-Requested-With": "XMLHttpRequest",
            },
            data={
                "csrfmiddlewaretoken": self.csrf_token,
                "count": 20*self.page,
            },
        )
        resp.raise_for_status()
        data = resp.json()  # parse JSON
        return data.get("html", "")  # return only the HTML string

    def go_to_next_page(self):
        """Fetch next batch of vacancies via AJAX."""
        self.page += 1
        self.html = self.fetch_page_html()
        soup = BeautifulSoup(self.html, "html.parser")
        vacancies = soup.select(self.VACANCY_CART)

        if not vacancies:
            self.logger.info("No more vacancies returned from DOU.")
            return False

        return True
    def fetch_full_description(self, job_url: str) -> str:
        """Fetch the full vacancy description from its page."""
        try:
            resp = self.session.get(job_url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            desc_elem = soup.select_one("div.b-typo.vacancy-section")
            return desc_elem.get_text(" ", strip=True) if desc_elem else ""
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to fetch full description for {job_url}: {e}")
            return ""

    def scrape_jobs(self, existing_links):
        jobs = []
        if self.page == 1:
            self.html = self.fetch_page_html()
        # else: get html from go_to_next_page
        self.logger.info(f"🌍 Parsing page {self.page}")
        soup = BeautifulSoup(self.html, "html.parser")
        vacancies = soup.select(self.VACANCY_CART)
        self.logger.info(f"Found {len(vacancies)} vacancies on page {self.page}")

        if not vacancies:
            self.logger.info("✅ No more vacancies found.")
            return jobs

        for vac in vacancies:
            title_elem = vac.select_one("div.title a.vt")
            if not title_elem:
                continue

            link = title_elem["href"].split("?")[0] if title_elem else None
            if link in self.seen_links:
                continue
            self.seen_links.add(link)

            date = vac.select_one("div.date")
            company_elem = vac.select_one("div.title a.company")
            salary_elem = vac.select_one("div.title span.salary")
            cities_elem = vac.select_one("div.title span.cities")
            desc_elem = vac.select_one("div.sh-info")

            title = title_elem.get_text(strip=True)
            company_name = company_elem.get_text(strip=True) if company_elem else ""
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            location = cities_elem.get_text(strip=True) if cities_elem else ""
            # short description
            description_short = desc_elem.get_text(" ", strip=True) if desc_elem else ""
            # Full description fetch
            description = self.fetch_full_description(link)
            date_text = date.get_text(strip=True) if date else ""

            if not link or link in existing_links:
                self.logger.info(f"⏭ Already processed: {title} @ {company_name}")
                continue

            # Filters
            if not self.filters.job_matches_title(title):
                self.logger.info(f"❌ {title} @ {company_name} : by title (skipped)")
                continue

            if not self.filters.job_matches_location(location):
                self.logger.info(f"❌ {title} @ {company_name} : by location (skipped)")
                continue

            if not self.filters.job_matches(description):
                continue

            job = {
                "title": title,
                "company": company_name,
                "location": location,
                "date": date_text,
                "salary": salary,				
                "description": description,
                "link": link,
            }
            jobs.append(job)
            self.logger.info(f"✅ Match found: {title} @ {company_name}")

        return jobs