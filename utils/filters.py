import re

class Filters:

    # Filtering rules: default. TODO: use strategy approach to setup filter via classes verification
    MUST_HAVE_TITLE = ["Test Automation", "Quality Assurance", r"\bQA\b", r"\bAQA\b", "QA Automation", "Automation Test Engineer", "in Test"]
    EXCLUDE_TITLE = ["Python", "C#", "iOS"]
    MUST_HAVE_TEXT = [r"\bJava\b"]  # regex with word boundary
    OPTIONAL_TEXT = [r"\bJava\b", "Cucumber", r"\bSQL\b", "API", "Selenium", "TestNG", "TeamCity"] # TODO: to count score
    EXCLUDE_TEXT = []
    MUST_HAVE_LOCATION = []

    def __init__(self, logger):
        self.logger = logger

    def set_must_have_title(self, arr):
        self.MUST_HAVE_TITLE = arr

    def set_exclude_title(self, arr):
        self.EXCLUDE_TITLE = arr

    def set_must_have_text(self, arr):
        self.MUST_HAVE_TEXT = arr

    def set_optional_text(self, arr):
        self.OPTIONAL_TEXT = arr

    def set_exclude_text(self, arr):
        self.EXCLUDE_TEXT = arr

    def set_must_have_location(self, arr):
        self.MUST_HAVE_LOCATION = arr
        
    # -----------------------------------
    # JOB FILTER FUNCTION
    # -----------------------------------
    def job_matches_title(self, title: str) -> bool:
        text = title.lower()

        # must have any
        if not any(re.search(k, text, re.IGNORECASE) for k in self.MUST_HAVE_TITLE):
            return False

        # exclude words
        if any(re.search(k, text, re.IGNORECASE) for k in self.EXCLUDE_TITLE):
            return False

        return True
    def job_matches_location(self, location: str) -> bool:
        text = location.lower()

        if not any(re.search(k, text, re.IGNORECASE) for k in self.MUST_HAVE_LOCATION):
            return False

        return True
    def job_matches(self, description: str) -> bool:
        text = description.lower()

        if not any(re.search(k, text, re.IGNORECASE) for k in self.MUST_HAVE_TEXT):
            self.logger.info(f"Not matched MUST_HAVE: {self.MUST_HAVE_TEXT}")
            return False

        # must have at least one optional
        if not any(re.search(k, text, re.IGNORECASE) for k in self.OPTIONAL_TEXT):
            self.logger.info(f"Not matched OPTIONAL: {self.OPTIONAL_TEXT}")
            return False

        # exclude words
        if any(re.search(k, text, re.IGNORECASE) for k in self.EXCLUDE_TEXT):
            self.logger.info(f"Not matched due to EXCLUDE: {self.EXCLUDE_TEXT}")
            return False

        return True