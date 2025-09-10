from linkedin_job_scraper import LinkedInJobScraper
from dou_job_scraper import DouJobScraper
from utils.filters import Filters
from utils.storage import Storage
# from indeed_scraper import IndeedScraper  # future

from logger import LoggerHelper

LINKEDIN = "Linkedin_job"
DOU = "Dou_job"
INDEED = "Indeed_job (soon)"
SCRAPERS = {
    "1": (LINKEDIN, LinkedInJobScraper),
    "2": (DOU, DouJobScraper),
    "3": (INDEED, None),
}

def run_scraper(scraper, filters, storage, logger):
    driver = scraper.setup_driver()

    input("👉 Log in if needed and press Enter...")

    existing_links = storage.load_existing_jobs()
    all_jobs = []
    while True:
        new_jobs = scraper.scrape_jobs(existing_links)
        storage.save_jobs_to_file(new_jobs, existing_links)
        all_jobs.extend(new_jobs)
        if not scraper.go_to_next_page():
            break

    logger.info(f"\n✅ Found {len(all_jobs)} new jobs")

    # Cleanup driver
    scraper.driver_quit()


if __name__ == "__main__":
    print("Choose site:")
    for key, (name, _) in SCRAPERS.items():
        print(f"{key}. {name}")

    choice = input("Enter choice: ")
    scraper_info = SCRAPERS.get(choice)

    if scraper_info and scraper_info[1]:
        site_name = scraper_info[0].lower()
        logger = LoggerHelper.get_logger(scraper_info[0].lower())

        MUST_HAVE_TITLE = ["Test Automation", "Quality Assurance", r"\bQA\b", r"\bAQA\b", "QA Automation", "Automation Test Engineer", "in Test"]
        EXCLUDE_TITLE = ["Python", "C#", "iOS"]
        MUST_HAVE_TEXT = [r"\bJava\b"]  # regex with word boundary
        OPTIONAL_TEXT = [r"\bJava\b", "Cucumber", r"\bSQL\b", "API", "Selenium", "TestNG", "TeamCity"]

        filters = Filters(logger)
        filters.set_must_have_title(MUST_HAVE_TITLE)
        filters.set_exclude_title(EXCLUDE_TITLE)
        filters.set_must_have_text(MUST_HAVE_TEXT)
        filters.set_optional_text(OPTIONAL_TEXT)

        # Site-specific filter setup
        if site_name == LINKEDIN.lower():
            filters.set_must_have_location(["Prague"])
            #search_url = "https://www.linkedin.com/jobs/collections/recommended/?discover=recommended"
            search_url = "https://www.linkedin.com/jobs/search/?f_F=qa%2Cit&f_T=11227%2C20648%2C209%2C12514%2C2837%2C16638&f_TPR=r2592000&f_WT=1%2C3%2C2&geoId=104328612&keywords=QA%2C%20Automation&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R&spellCorrectionEnabled=true"
            ajax_url = None
        elif site_name == DOU.lower():
            filters.set_must_have_location(["віддалено"])
            search_url = "https://jobs.dou.ua/vacancies/?category=QA"
            ajax_url = "https://jobs.dou.ua/vacancies/xhr-load/?category=QA"

        storage = Storage(logger, f"{site_name}.txt")
        scraper = scraper_info[1](filters, logger)
        scraper.init_url(search_url, ajax_url)
        run_scraper(scraper, filters, storage, logger)
    else:
        print("❌ Not implemented yet")