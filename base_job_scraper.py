from abc import ABC, abstractmethod

class BaseJobScraper(ABC):
    @abstractmethod
    def get_logger(self):
        """Return logger"""
        pass
    @abstractmethod
    def init_url(self, search_url, ajax_url):
        """Init search url"""
        pass
    @abstractmethod
    def setup_driver(self):
        """Initialize browser driver"""
        pass

    @abstractmethod
    def driver_quit(self):
        """Quit browser driver"""
        pass

    @abstractmethod
    def scrape_jobs(self):
        """Scrape jobs and return as list of dicts"""
        pass

    @abstractmethod
    def go_to_next_page(self):
        """Click next page if available, return True/False"""
        pass