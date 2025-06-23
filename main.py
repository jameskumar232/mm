import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from PyPDF2 import PdfMerger
import time
import certifi
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://epaper.malaimurasu.com/"
LOG_FILE = "log.txt"

def log(message):
    print(message)
    with open(LOG_FILE, "a") as f:
        f.write(f"{message}\n")

def clear_log():
    open(LOG_FILE, "w").close()

def get_yesterday_date():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y/%m/%d"), yesterday.strftime("%Y/%m/%d").split("/")

def get_number_of_pages():
    try:
        response = requests.get(BASE_URL, verify=certifi.where(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        select = soup.find("select", {"id": "idGotoPageList"})
        options = select.find_all("option")
        return len(options)
    except Exception as e:
        log(f"Error fetching number of pages: {e}")
        return 0

def download_pdf(url, filename, retries=3, page_num=None):
    for attempt in range(retries):
        log(f"Attempt {attempt + 1}")
        try:
            response = requests.get(url, stream=True, timeout=10, verify=certifi.where())
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            log(f"page {page_num} downloaded")
            return True
        except Exception as e:
            time.sleep(2)
    log(f"Failed to download page {page_num}")
    return False

def combine_pdfs(pdf_list, output_filename):
    log("Combining downloaded PDFs...")
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_filename)
    merger.close()
    log(f"Combined PDFs into {output_filename}")

def cleanup_files(pdf_list):
    log("Cleaning up individual page files...")
    for file in pdf_list:
        try:
            os.remove(file)
            log(f"Deleted: {file}")
        except Exception as e:
            log(f"Error deleting {file}: {e}")

def main():
    clear_log()
    formatted_date, [year, month, day] = get_yesterday_date()
    edition = "Chennai"
    page_prefix = "CHE_P"

    num_pages = get_number_of_pages()
    if num_pages == 0:
        log("No pages found. Exiting.")
        return

    log(f"no of pages {num_pages}")

    downloaded_files = []
    for i in range(1, num_pages + 1):
        page_number = f"{i:02d}"
        pdf_url = f"{BASE_URL}{year}/{month}/{day}/{edition}/{page_prefix}{page_number}.pdf"
        filename = f"page_{page_number}.pdf"
        log(f"downloading page {i}")
        if download_pdf(pdf_url, filename, page_num=i):
            downloaded_files.append(filename)

    if downloaded_files:
        combine_pdfs(downloaded_files, "malaimurasu.pdf")
        cleanup_files(downloaded_files)
        log("Done!")

if __name__ == "__main__":
    main()
