from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
import os

# File Path
DATA_DIR = "data_file"
CSV_FILE = os.path.join(DATA_DIR, "mero__jobs.csv")

# Create folder if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)


# Headless options
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")


# Initialize the driver
driver = webdriver.Chrome(options=options)
driver.get("https://merojob.com/")

wait = WebDriverWait(driver, 10)

# Click "Individual Jobs"
try:
    individual_jobs_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Individual Jobs')]"))
    )
    individual_jobs_button.click()
except:
    print("Could not find 'Individual Jobs' button. Trying alternative...")
    individual_jobs_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Jobs')]"))
    )
    individual_jobs_button.click()

time.sleep(2)

job_elements = wait.until(
    EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, ".rounded-lg.border.bg-card.text-card-foreground.shadow-sm.hover\\:shadow-xl")
    )
)

# Scrape jobs
scraped_jobs = []

for job in job_elements:
    try:
        lines = job.text.split("\n")

        job_title = lines[0] if len(lines) > 0 else "N/A"
        company = lines[1] if len(lines) > 1 else "N/A"
        experience = lines[2] if len(lines) > 2 else "N/A"

        level = "N/A"
        salary = "N/A"
        apply_before = "N/A"

        for line in lines:
            line_lower = line.lower()

            # Extract Level
            if "level" in line_lower:
                level = line.split(":")[-1].strip()

            # Extract Apply Before
            elif "apply before" in line_lower:
                apply_before = line.split(":")[-1].strip()

            # Extract Salary (robust detection)
            elif (
                "rs." in line_lower
                or "lakh" in line_lower
                or "negotiable" in line_lower
                or "month" in line_lower
                or "year" in line_lower
            ):
                salary = line.strip()

        scraped_jobs.append({
            "Job Title": job_title,
            "Company": company,
            "Experience": experience,
            "Level": level,
            "Salary": salary,
            "Apply Before": apply_before
        })

    except Exception as e:
        print(f"Error processing job: {e}")

# Load existing jobs
existing_jobs = []
old_jobs_data = []

if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row["Job Title"], row["Company"])
            existing_jobs.append(key)
            old_jobs_data.append(row)

# Filter new jobs
new_jobs = []
for job in scraped_jobs:
    job_key = (job["Job Title"], job["Company"])
    if job_key not in existing_jobs:
        new_jobs.append(job)
        existing_jobs.append(job_key)

# Combine new + old
combined_jobs = new_jobs + old_jobs_data

# Write CSV
fieldnames = [
    "Job Title",
    "Company",
    "Experience",
    "Level",
    "Salary",
    "Apply Before"
]

with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for job in combined_jobs:
        writer.writerow(job)

print(f"{len(new_jobs)} new jobs added to the top of '{CSV_FILE}'")

driver.quit()
