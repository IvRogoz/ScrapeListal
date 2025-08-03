import requests
from bs4 import BeautifulSoup
import shutil
import os
import sys
import tkinter as tk
from tkinter import simpledialog
import time

# Constants
START_PAGE = 0
IMAGES_PER_PAGE = 50
TIMEOUT = 20
MAX_RETRIES = 3
RETRY_DELAY = 2  # Seconds to wait between retries

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.listal.com/',
}

# Initialize Tkinter
ws = tk.Tk()
ws.title("Scrape Listal")
ws.overrideredirect(1)
ws.withdraw()

# Get user input
base_url = simpledialog.askstring("Input", "Url", parent=ws)
pagination = simpledialog.askinteger("Input", "Number of Pages", parent=ws)

# Validate inputs
if not base_url or not pagination:
    print("Invalid input. Exiting...")
    ws.destroy()
    sys.exit(1)

# Create directory based on base_url
folder = base_url.replace("https://www.listal.com/", "").replace("/pictures", "")
if not os.path.exists(folder):
    os.makedirs(folder)
folder = f"./{folder}/"

def update_progress(progress, total, image):
    filled_length = int(round(100 * progress / float(total)))
    sys.stdout.write(f'\r [\033[1;34mPROGRESS\033[0;0m] [\033[0;32m{"#" * (filled_length // 5)}\033[0;0m]:{filled_length}% {progress}/{total} : {image}')
    if progress == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

# Calculate total images
total_image_count = (pagination - START_PAGE) * IMAGES_PER_PAGE
current_image_count = 0
duplicate_count = 0

# Create a requests session for connection reuse
session = requests.Session()
session.headers.update(HEADERS)

try:
    print(f"Total Images to Download: {total_image_count}")
    for page in range(START_PAGE, pagination):
        url = base_url if page == 0 else f"{base_url}/{page}"
        print(f"\nScraping from: {url}")

        # Fetch page with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = session.get(url, timeout=TIMEOUT)
                response.raise_for_status()  # Raise exception for bad status codes
                soup = BeautifulSoup(response.text, 'html.parser')
                images = soup.find_all(class_='imagewrap-inner')
                print(f"Found {len(images)} images on page {page}")
                break
            except requests.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"Error fetching page {url}: {e}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"Failed to fetch page {url} after {MAX_RETRIES} attempts: {e}")
                    images = []  # Set empty list to skip this page
                    break

        for index, item in enumerate(images):
            current_image_count += 1
            try:
                # Fetch individual image page
                image_page_url = item.find('a')['href']
                for attempt in range(MAX_RETRIES):
                    try:
                        response = session.get(image_page_url, timeout=TIMEOUT)
                        response.raise_for_status()
                        individual_soup = BeautifulSoup(response.text, 'html.parser')
                        found = individual_soup.find(id='itempagewrapper')
                        if not found:
                            print(f"No image found on {image_page_url}")
                            continue
                        img_url = found.find('img')['src']
                        break
                    except requests.RequestException as e:
                        if attempt < MAX_RETRIES - 1:
                            print(f"Error fetching image page {image_page_url}: {e}. Retrying in {RETRY_DELAY} seconds...")
                            time.sleep(RETRY_DELAY)
                        else:
                            print(f"Failed to fetch image page {image_page_url} after {MAX_RETRIES} attempts: {e}")
                            continue
                    except (AttributeError, TypeError) as e:
                        print(f"Error parsing image page {image_page_url}: {e}")
                        break

                if not img_url:
                    continue

                # Download image
                file_name = os.path.join(folder, img_url.split('/')[-1])
                base, ext = os.path.splitext(file_name)
                
                # Handle duplicate filenames
                while os.path.exists(file_name):
                    duplicate_count += 1
                    file_name = f"{base}_{duplicate_count}{ext}"

                for attempt in range(MAX_RETRIES):
                    try:
                        res = session.get(img_url, stream=True, timeout=TIMEOUT)
                        res.raise_for_status()
                        with open(file_name, 'wb') as f:
                            shutil.copyfileobj(res.raw, f)
                        if os.path.exists(file_name):
                            update_progress(current_image_count, total_image_count, os.path.basename(file_name))
                        else:
                            print(f"Failed to save image: {file_name}")
                        break
                    except requests.RequestException as e:
                        if attempt < MAX_RETRIES - 1:
                            print(f"Error downloading image {img_url}: {e}. Retrying in {RETRY_DELAY} seconds...")
                            time.sleep(RETRY_DELAY)
                        else:
                            print(f"Failed to download image {img_url} after {MAX_RETRIES} attempts: {e}")
            except Exception as e:
                print(f"Error processing image {index + 1} on page {page}: {e}")
                continue

except Exception as e:
    print(f"Script terminated with error: {e}")
finally:
    session.close()
    ws.destroy()
    print("Script completed.")
