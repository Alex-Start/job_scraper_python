from selenium import webdriver
#import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os, re, time

from base_job_scraper import BaseJobScraper
from utils.filters import Filters
from utils.delays import human_delay

class LinkedInJobScraper(BaseJobScraper):
    # -----------------------------------
    # CONFIGURATION
    # -----------------------------------
	# Default
    SEARCH_URL = "https://www.linkedin.com/jobs/collections/recommended/?discover=recommended&discoveryOrigin=JOBS_HOME_JYMBII"

    # Chrome profile for persistent session
    PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profile")
    XPATH_JOB_ELEMENTS = "//li[@data-occludable-job-id]"

    def __init__(self, filters, logger):
        self.driver = None
        self.filters = filters
        self.logger = logger
    
    def get_logger(self):
        return self.logger
   
    def init_url(self, search_url, axaj_url):
        self.SEARCH_URL = search_url
        self.logger.info(f"Search URL: {search_url}")

    def setup_driver(self):
        # ----------------------------------
        # SETUP DRIVER (Selenium + Stealth)
        # -----------------------------------
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.PROFILE_DIR}")   # custom profile folder
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(options=options)

        # Apply stealth mode
        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
        )

        self.driver.get(self.SEARCH_URL)
    
        return self.driver

    def driver_quit(self):
        self.logger.info(f"🔹 Browser session is kept in '{self.PROFILE_DIR}/' for next runs.")
        try:
            self.driver.quit()
        except Exception:
            self.logger.warning("⚠️ Could not quit driver cleanly")

    def normalize_link(self, link: str) -> str:
        """
        Extracts only the base LinkedIn job link:
        https://www.linkedin.com/jobs/view/<job-id>/
        """
        match = re.search(r"(https://www\.linkedin\.com/jobs/view/\d+)", link)
        if match:
            return match.group(1) + "/"  # Ensure trailing slash
        return link  # fallback if pattern not matched

    def go_to_next_page(self, timeout=5):
        """
        Clicks the 'Next' button in LinkedIn job search pagination.
        Returns True if the button was found and clicked, False otherwise.
        """
        try:
            # Wait for the button to be clickable
            next_button = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jobs-search-pagination__button--next"))
            )
            self.driver.execute_script("arguments[0].click();", next_button)  # safer than .click()
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def is_job_viewed(self, job_element) -> bool:
        """
        Returns True if the job card has the 'Viewed' footer.
        """
        try:
            footer = job_element.find_element(
                By.CSS_SELECTOR,
                "li.job-card-container__footer-job-state"
            )
            return "Viewed" in footer.text.strip()
        except:
            return False

    @staticmethod
    def add_job(jobs_list, title, company_name, location, description, link):
        """
        Adds a job entry to the given list in a consistent format.
    
        Args:
            jobs_list (list): The list to append the job to.
            title (str): Job title.
            company_name (str): Company name.
            location (str): Job location.
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

    # -----------------------------------
    # SCRAPING
    # -----------------------------------
    def scrape_jobs(self, existing_links):
        jobs = []
        jobs_matched_title = []

        # Scroll to load all jobs on the first page
        #load_all_jobs(driver)

        # Find all job cards
        job_cards = self.driver.find_elements(By.XPATH, self.XPATH_JOB_ELEMENTS)
        # always check first - always it is opened when page is loaded
        check_first = True
    
        for i, card in enumerate(job_cards):
            try:
                self.logger.info("-----------")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                human_delay(2, 4)

                if not check_first and self.is_job_viewed(card):
                    self.logger.info("⏭️ Skipping already viewed job")
                    continue  # skip this job

                check_first = False

                # find link element inside job card
                link_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title--link")#"a.job-card-container__link"
                link = self.normalize_link(link_elem.get_attribute("href"))
                #title = link_elem.get_attribute("aria-label")
                title = link_elem.text.strip()
            
                # company name
                company_elem = card.find_element(By.XPATH, ".//div[contains(@class,'artdeco-entity-lockup__subtitle')]")#".artdeco-entity-lockup__subtitle span"
                company_name = company_elem.text.strip()

                self.logger.info(f"\n[{i+1}] {title} @ {company_name}")
                self.logger.info(f"🔗 {link}")

                if not self.filters.job_matches_title(title):
                    self.logger.info(f"[{i+1}] ❌ {title} @ {company_name} : by title (skipped)")
                    continue

                # Location
                location_elem = card.find_element(By.XPATH, ".//div[contains(@class,'artdeco-entity-lockup__caption')]//li")
                location = location_elem.text.strip()

                if not self.filters.job_matches_location(location):
                    self.logger.info(f"[{i+1}] ❌ {title} @ {company_name} : by location (skipped)")
                    self.add_job(jobs_matched_title, title, company_name, location, "", link)
                    continue

                if link in existing_links:
                    self.logger.info(f"[{i+1}] ⏭ Already reviewed: {title} @ {company_name}")
                    self.add_job(jobs_matched_title, title, company_name, location, "", link)
                    continue

                # --- Click to open job ---
                self.driver.execute_script("arguments[0].click();", link_elem)
                #card.click()
                human_delay(3, 6)
            
                # wait for description to appear
                job_desc_elem = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#job-details")))
                description = job_desc_elem.text.strip()

                self.logger.info(f"📄 Description (first 200 chars): {description[:200]}...")
                #time.sleep(3)

                if self.filters.job_matches(description):
                    jobs.append({
                        "title": title,
                        "company": company_name,
						"location": location,
                        "description": description,
                        "link": link
                    })
                    self.logger.info(f"[{i+1}] ✅ {title} @ {company_name} (MATCHED)")
                else:
                    self.logger.info(f"[{i+1}] ❌ {title} @ {company_name} (skipped)")
                    self.add_job(jobs_matched_title, title, company_name, location, description, link)

                human_delay(5, 12)

            except Exception as e:
                self.logger.info(f"⚠️ Error reading job {i+1}: {e}")
                continue

        return (jobs, jobs_matched_title)

    def detect_captcha(self):
        """Check if a CAPTCHA is present"""
        try:
            self.driver.find_element(By.ID, "captcha-internal")
            self.logger.info("⚠️ CAPTCHA detected! Please solve it manually in the browser...")
            while True:
                input("Press Enter after solving CAPTCHA...")
                break
            return True
        except NoSuchElementException:
            return False
