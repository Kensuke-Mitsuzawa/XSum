import requests
import logging
import time
import math
import os
import sys
from pathlib import Path
import typing as ty
import tqdm

"""Rewritten by Kensuke Mitsuzawa <kensuke.mit@gmail.com>.
The original code can not cope with the connection issues.
"""


# --- Logger Setup (Python 3 style) ---
def setup_logger():
    logger = logging.getLogger('internet_archive_downloader')
    logger.setLevel(logging.DEBUG) # Set to INFO for less verbose output

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Only INFO and above to console
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = logging.FileHandler('logs/download.log')
    file_handler.setLevel(logging.DEBUG) # All debug messages to file
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger



def download_wayback_html(url: str, downloads_dir: Path, timeout=15, max_attempts=5):
    """
    Downloads HTML content from a Wayback Machine URL with robust error handling.

    Args:
        url (str): The full Wayback Machine URL (e.g., https://web.archive.org/web/...).
        downloads_dir (str): Directory to save the downloaded HTML.
        timeout (int): Timeout for the request in seconds.
        max_attempts (int): Maximum number of retry attempts.

    Returns:
        str: The decoded HTML content if successful, None otherwise.
    """
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
    # end if

    # Get file id
    fileid = url.replace("http://web.archive.org/web/", "")
    fileid = fileid.replace("http://", "")
    htmlfileid = fileid.replace("/", "-") + ".html"

    # # Sanitize URL for filename (basic example, improve for complex URLs)
    # # Using the timestamp from the URL as a unique identifier for the filename
    # try:
    #     parts = url.split('/')
    #     # Expected format: https://web.archive.org/web/YYYYMMDDhhmmss[id_]/original_url
    #     if len(parts) >= 6 and parts[4].isdigit() and len(parts[4]) >= 14:
    #         timestamp = parts[4]
    #         original_url_path = "/".join(parts[5:]) # Get the rest of the original URL path
    #         # Create a somewhat unique and readable filename
    #         filename_slug = "".join(c for c in original_url_path if c.isalnum() or c in ('-', '_')).strip()
    #         if not filename_slug:
    #             filename_slug = "index" # Fallback if path is empty
    #         html_file_id = f"{timestamp}_{filename_slug[:50]}.html" # Truncate for sanity
    #     else:
    #         # Fallback for unexpected URL formats
    #         import hashlib
    #         html_file_id = hashlib.md5(url.encode('utf-8')).hexdigest() + ".html"
    # except Exception as e:
    #     logger.warning(f"Could not parse URL for filename, using hash: {url}. Error: {e}")
    #     import hashlib
    #     html_file_id = hashlib.md5(url.encode('utf-8')).hexdigest() + ".html"

    # file_path = os.path.join(downloads_dir, html_file_id)
    file_path_save = downloads_dir / htmlfileid

    # Mimic a common browser User-Agent to avoid blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1', # Do Not Track request header
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    attempts = 0
    while attempts < max_attempts:
        try:
            logger.debug(f"Attempt {attempts + 1}/{max_attempts} to download: {url}")
            req = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers)
            req.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # Internet Archive often wraps the original content in an iframe or adds banners.
            # To get the raw, unwrapped content, you can append 'id_' to the timestamp in the URL.
            # Example: https://web.archive.org/web/20170830184626id_/http://www.bbc.com/sport/rugby-league/39733931
            # If the initial URL doesn't have 'id_', you might try to construct it.
            # However, for simplicity, we'll download the full page first.
            # If you specifically want the raw content, modify the 'url' to include 'id_' before making the request.

            content = req.text
            # It's better to write the raw text directly if req.text is already decoded
            with open(file_path_save, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Successfully saved: {url} to {file_path_save}")
            return content

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [404, 503] and attempts == max_attempts - 1:
                logger.error(f"HTTP Error {e.response.status_code} for {url}. Max attempts reached. Giving up.")
                return None
            else:
                logger.warning(f"HTTP Error {e.response.status_code} for {url}. Retrying... ({e})")
        except requests.exceptions.ConnectionError:
            logger.error(f"ConnectionError: {url}. Retrying...")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout Error: {url}. Retrying...")
        except requests.exceptions.TooManyRedirects:
            logger.error(f"TooManyRedirects: {url}. Giving up.")
            return None
        except requests.exceptions.RequestException as e: # Catch any other requests-related errors
            logger.error(f"An unexpected requests error occurred for {url}: {e}. Retrying...")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred for {url}: {e}. Giving up.")
            return None

        # Exponential back-off.
        time.sleep(math.pow(2, attempts))
        attempts += 1

    logger.error(f"Failed to download {url} after {max_attempts} attempts.")
    return None


def load_source_url_list(path_list: Path) -> ty.List[str]:
    seq_url = []
    with open(path_list) as f:
        seq_url = list(f.readlines())
    # end with

    return seq_url


def main(path_file_source_url_list: Path, 
         path_file_missing_url_list: Path, 
         downloads_dir: Path = Path("./xsum-raw-downloads"),
         timeout: int = 15, 
         max_attempts: int = 5):
    assert path_file_source_url_list.exists()

    seq_source_url_list = load_source_url_list(path_file_source_url_list)
    if path_file_missing_url_list:
        seq_missing_url_list = load_source_url_list(path_file_missing_url_list)
        seq_source_url_list = seq_missing_url_list
    # end if

    downloads_dir = Path(downloads_dir)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Files to be downloaded: {len(seq_source_url_list)}")
    for url in tqdm.tqdm(seq_source_url_list):
        download_wayback_html(url=url, downloads_dir=downloads_dir, timeout=timeout, max_attempts=max_attempts)

        # deleting the url from the missing url list
    # end for


# --- Example Usage ---
if __name__ == "__main__":
    logger = setup_logger()
    
    urls_file_to_download = "XSum-WebArxiveUrls.txt"
    missing_urls_file = "XSum-WebArxiveUrls.missing.txt" 
    downloads_dir = "./xsum-raw-downloads"

    main(
        path_file_missing_url_list=Path(missing_urls_file),
        path_file_source_url_list=Path(urls_file_to_download),
        downloads_dir=Path(downloads_dir)
    )

