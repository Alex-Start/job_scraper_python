import requests
from bs4 import BeautifulSoup

class DjinniJobScraper:
    # Default
    BASE_URL = "https://djinni.co"
    SEARCH_URL = "https://djinni.co/jobs/?primary_keyword=QA"
    VACANCY_CART = "ul.list-jobs > div[id^='job-item']"

    def __init__(self, filters, logger):
        self.filters = filters
        self.logger = logger
        self.session = requests.Session()
        self.page = 1
        self.seen_links = set()

    def get_logger(self):
        return self.logger

    def setup_driver(self):
        """Djinni does not need Selenium."""
        return None
    def driver_quit(self):
        pass

    def init_url(self, search_url, axaj_url):
        self.SEARCH_URL = search_url
        self.logger.info(f"Search URL: {search_url}")

    def fetch_page_html(self):
        url = f"{self.SEARCH_URL}&page={self.page}"
        self.logger.info(f"Fetching Djinni page {self.page}: {url}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://djinni.co/jobs/",
            "Connection": "keep-alive"
        }
        
        resp = self.session.get(url, headers=headers)
        #resp = self.session.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            self.logger.error(f"Failed to load page: {resp.status_code}")
            return None
        if "has been blocked" in resp.text:
            self.logger.error("🚫 Djinni blocked your IP")
            return None
        if resp.history:
            self.logger.warning(
                f"Redirected: {url} → {resp.url}"
            )
            return None
        if "page=" not in resp.url:
            self.logger.warning("⚠️ Page parameter missing in final URL")
            return None

        return resp.text

    def first_matching_location(self, locations):
        for loc in locations:
            if self.filters.job_matches_location(loc):
                return loc
        return None

    @staticmethod
    def add_job(jobs_list, title, company_name, location, description, link):
        """
        Adds a job entry to the given list in a consistent format.

        Args:
            jobs_list (list): The list to append the job to.
            title (str): Job title.
            company_name (str): Company name.
            location (str/list): Job location and rest params.
            link (str): URL to the job posting.
            description (str, optional): Job description (default: "").
        """
        jobs_list.append({
            "title": title,
            "company": company_name,
            "location": location,
            "description": description,
            "link": link
        })

    def scrape_jobs(self, existing_links):
        jobs = []
        jobs_matched_title = []
        if self.page == 1:
            self.html = self.fetch_page_html()
        if not self.html:
            return (jobs, )
        # TODO: it can block IP:>>> Your IP address, 94.142.235.80, has been blocked. Please contact us at magic@djinni.co.
        #self.logger.info(f">>> {self.html}")

        self.logger.info(f"🌍 Parsing page {self.page}")
        soup = BeautifulSoup(self.html, "html.parser")
        vacancies = soup.select(self.VACANCY_CART)
        self.logger.info(f"Found {len(vacancies)} vacancies on page {self.page}")

        if not vacancies:
            self.logger.info("✅ No more vacancies found.")
            return (jobs, )

        for i, item in enumerate(vacancies):
            try:
                self.logger.info("-----------")
                divCol = item.select_one("div.col")
                title_tag = divCol.select_one("h2.job-item__position")
                if not title_tag:
                    continue

                link = item.select_one("a.job_item__header-link")["href"]
                full_link = self.BASE_URL + link
                if not full_link or full_link in self.seen_links:
                    continue
                self.seen_links.add(full_link)

                title = title_tag.get_text(strip=True)

                company_tag = divCol.select_one("span.small")
                company = company_tag.get_text(strip=True) if company_tag else "Unknown"

                # get location info
                info_spans = item.select("div.fw-medium span.text-nowrap")
                info_items = [span.get_text(strip=True) for span in info_spans]

                self.logger.info(f"\n[{i+1}] {title} @ {company} info: {info_items}")
                self.logger.info(f"🔗 {full_link}")
                #is “You've applied”?
                applied_marker = item.find("a.text-bg-success", string=lambda t: t and "applied" in t.lower())
                if applied_marker:
                    self.logger.info(f"[{i+1}] Skipped (already applied)")
                    continue

                if not full_link or full_link in existing_links:
                    self.logger.info(f"⏭ Already processed: {title} @ {company}")
                    continue

                # short description
                description = item.select_one("div span.js-truncated-text").get_text(strip=True)

                # Apply your filters
                if not self.filters.job_matches_title(title):
                    self.logger.info(f"❌ {title} @ {company} : by title (skipped)")
                    self.add_job(jobs_matched_title, title, company, info_items, description, full_link)
                    continue

                if not self.first_matching_location(info_items):
                    self.logger.info(f"❌ {title} @ {company} — locations {info_items} : by location (skipped)")
                    self.add_job(jobs_matched_title, title, company, info_items, description, full_link)
                    continue

                # open the link to get full description
                session = requests.Session()
                response = session.get(full_link)
                soup = BeautifulSoup(response.text, "html.parser")
                #card = soup.find("div", class_="card-body")
                #applied_info = card.find(string=lambda t: "applied to this job already" in t)
                description_block = soup.select_one(".job-post__description")
                description = description_block.get_text("\n", strip=True) if description_block else ""
                self.logger.info(f"📄 Description (first 200 chars): {description[:200]}...")

                if not self.filters.job_matches(description):
                    self.logger.info(f"[{i+1}] ❌ {title} @ {company} by description (skipped)")
                    self.add_job(jobs_matched_title, title, company, info_items, description, full_link)
                    continue

                job = {
                    "title": title,
                    "company": company,
                    "location": info_items,
                    "description": description,
                    "link": full_link,
                }

                jobs.append(job)
                self.logger.info(f"✅ Match found: {title} @ {company}")

            except Exception as e:
                self.logger.error(f"Failed to parse job: {e}")

        return (jobs, jobs_matched_title)

    def go_to_next_page(self):
        """Djinni uses ?page=2 pagination. We detect end by checking if jobs disappear."""
        self.page += 1
        self.html = self.fetch_page_html()
        if not self.html:
           return False
        soup = BeautifulSoup(self.html, "html.parser")
        vacancies = soup.select(self.VACANCY_CART)
        if not vacancies:
            return False
        
        return len(vacancies) > 0