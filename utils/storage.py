import os, re
import csv

class Storage:
    OUTPUT_FILE = "filtered_jobs.txt"

    def __init__(self, logger, file_name):
        self.logger = logger
        self.OUTPUT_FILE = file_name

    # -----------------------------------
    # LOAD PREVIOUS JOBS
    # -----------------------------------
    def load_existing_jobs_csv(self):
        if not os.path.exists(OUTPUT_FILE):
            return set()
        with open(self.OUTPUT_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return set(row["link"] for row in reader)

    def load_existing_jobs(self):
        if not os.path.exists(self.OUTPUT_FILE):
            return set()

        job_links = set()
        with open(self.OUTPUT_FILE, encoding="utf-8") as f:
            content = f.read()

            # Each job block ends with link=...
            matches = re.findall(r" link=(.+)", content)
            for link in matches:
                job_links.add(link.strip())

        return job_links

    # -----------------------------------
    # SAVE JOBS (APPEND NEW ONLY)
    # -----------------------------------
    def save_jobs_to_csv(self, jobs):
        file_exists = os.path.exists(self.OUTPUT_FILE)
        with open(self.OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "description", "link"])
            if not file_exists:
                writer.writeheader()
            writer.writerows(jobs)
        self.logger.info(f"\n✅ Saved {len(jobs)} new jobs to {self.OUTPUT_FILE}")

    def save_jobs_to_file(self, jobs, existing_links):
        """
        1. ----------------------------
        title=...
        company=...
        description=...
        ...
        link=...
        2. ----------------------------
        ...
        """
        i = len(existing_links)
        with open(self.OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            for i, job in enumerate(jobs, start=i+1):
                f.write(f"{i}. ----------------------------\n")
                f.write(f" title={job.get('title','')}\n")
                f.write(f" company={job.get('company','')}\n")
                f.write(f" location={job.get('location','')}\n")
                f.write(f" salary={job.get('salary','')}\n")      # optional
                f.write(f" date={job.get('date','')}\n")          # optional
                f.write(f" description={job.get('description','')}\n")
                f.write(f" link={job.get('link','')}\n")
                f.write("\n")  # Add a blank line between jobs

        self.logger.info(f"\n✅ Saved {len(jobs)} new jobs to {self.OUTPUT_FILE}")