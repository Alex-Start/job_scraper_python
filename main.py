import argparse, sys
from linkedin_job_scraper import LinkedInJobScraper
from dou_job_scraper import DouJobScraper
from utils.filters import Filters
from utils.storage import Storage
# from indeed_scraper import IndeedScraper  # future

from urllib.parse import urlsplit, urlunsplit

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

    existing_links = storage[0].load_existing_jobs()
    if len(storage)>1:
        existing_links_matched_title = storage[1].load_existing_jobs()
    all_jobs = []
    while True:
        new_jobs = scraper.scrape_jobs(existing_links)
        storage[0].save_jobs_to_file(new_jobs[0], existing_links)
        existing_links.update({job["link"] for job in new_jobs[0]})
        all_jobs.extend(new_jobs[0])
        if len(new_jobs)>1:
            # Filter out already-known jobs
            new_jobs_skipped = [
                job for job in new_jobs[1] if job["link"] not in existing_links_matched_title
            ]
            # Add new links to existing_links_matched_title
            storage[1].save_jobs_to_file(new_jobs_skipped, existing_links_matched_title)
            existing_links_matched_title.update({job["link"] for job in new_jobs_skipped})
        if not scraper.go_to_next_page():
            break

    logger.info(f"\n✅ Found {len(all_jobs)} new jobs")

    # Cleanup driver
    scraper.driver_quit()

def createDouXhrLoadUrl(url):
    if url == None:
        return ""
    parts = urlsplit(url)
    # parts.path -> '/vacancies/'

    # Insert 'xhr-load' into the path
    new_path = parts.path.rstrip('/') + '/xhr-load/'

    # Rebuild the new URL
    new_url = urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))

    return new_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Scraper CLI")
    parser.add_argument(
        "-choice",
        choices=[LINKEDIN, DOU, INDEED],
        help="Choose which scraper to use",
    )
    parser.add_argument(
        "-url",
        help="Base search URL to scrape",
    )
    args = parser.parse_args()

    # --- interactive fallback if no choice ---
    if not args.choice:
        print("Choose site:")
        for key, (name, _) in SCRAPERS.items():
            print(f"{key}. {name}")

        choice = input("Enter choice: ")
        scraper_info = SCRAPERS.get(choice)
    else:
        scraper_info = None
        for _, (name, scraper_cls) in SCRAPERS.items():
            if name == args.choice:
                scraper_info = (name, scraper_cls)
                break
        else:
            print(f"Incorrect choice: {args.choice}")
            sys.exit()

    if scraper_info and scraper_info[1]:
        site_name = scraper_info[0].lower()
        logger = LoggerHelper.get_logger(scraper_info[0].lower())

        MUST_HAVE_TITLE = ["Test Automation", "Quality Assurance", "Quality Engineer", r"\bQA\b", r"\bAQA\b", "QA Automation", "QA Tester", "Test Engineer", "in Test", "SDET", "Testing", "Automation Engineer"]
        EXCLUDE_TITLE = ["Python", "C#", "iOS", "JavaScript"]
        MUST_HAVE_TEXT = [r"\bJava\b"]  # regex with word boundary
        OPTIONAL_TEXT = [r"\bJava\b", "Cucumber", r"\bSQL\b", "API", "Selenium", "TestNG", "TeamCity"]

        filters = Filters(logger)
        filters.set_must_have_title(MUST_HAVE_TITLE)
        filters.set_exclude_title(EXCLUDE_TITLE)
        filters.set_must_have_text(MUST_HAVE_TEXT)
        filters.set_optional_text(OPTIONAL_TEXT)

        # Site-specific filter setup
        if site_name == LINKEDIN.lower():
            filters.set_must_have_location(["Prague", r"Czechia \(Remote\)", r"European Union \(Remote\)"])
            search_url = args.url or "https://www.linkedin.com/jobs/collections/recommended/?discover=recommended"
            ajax_url = ""
        elif site_name == DOU.lower():
            filters.set_must_have_location(["віддалено"])
            search_url = args.url or "https://jobs.dou.ua/vacancies/?category=QA"
            ajax_url = createDouXhrLoadUrl(args.url) or "https://jobs.dou.ua/vacancies/xhr-load/?category=QA" #TODO need to use args.url properly
        else:
            sys.exit()

        storage = (Storage(logger, f"{site_name}.txt"), Storage(logger, f"{site_name}_matched_title.txt"))
        scraper = scraper_info[1](filters, logger)
        scraper.init_url(search_url, ajax_url)
        run_scraper(scraper, filters, storage, logger)
    else:
        print("❌ Not implemented yet")