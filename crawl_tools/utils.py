import time
import re
from urllib.parse import urlparse
import html2text
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone
import textwrap
from crawl4ai import CrawlResult
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


def split_into_paragraphs(content, ext, width=80):
    if ext == ".md":
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.body_width = width
        md_text = converter.handle(content)
        paragraphs = md_text.split("\n\n")
        wrapped = "\n\n".join(textwrap.fill(p, width=width) for p in paragraphs)
        return wrapped
    elif ext == ".txt":
        soup = BeautifulSoup(content, "html.parser")
        txt = soup.get_text(separator="\n")
        paragraphs = txt.split("\n\n")
        return "\n\n".join(textwrap.fill(p, width=width) for p in paragraphs)
    else:
        return content


def convert_and_wrap(content, ext, width=80, verbose=False):
    """Convert HTML content to Markdown or plain text."""
    if ext == ".md":
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.body_width = width  # Attempt wrapping at 80 characters
        converted = converter.handle(content)
        if verbose:
            log_print("[DEBUG] Raw HTML length:", len(content))
            log_print("[DEBUG] Converted Markdown length:", len(converted))
            log_print("[DEBUG] Converted Markdown preview:", converted[:200])
        return converted
    elif ext == ".txt":
        soup = BeautifulSoup(content, "html.parser")
        txt = soup.get_text(separator="\n")
        if verbose:
            log_print("[DEBUG] Raw HTML length:", len(content))
            log_print("[DEBUG] Extracted Text length:", len(txt))
            log_print("[DEBUG] Extracted Text preview:", txt[:200])
        return txt
    else:
        return content


def convert_crawl_result(result: CrawlResult, ext, cleaned=True):
    if ext == ".html":
        if cleaned:
            return result.fit_html
        return result.html
    if cleaned:
        return result.markdown.fit_markdown
    return result.markdown


def normalize_url(url):
    """
    Normalize a URL by lowercasing the netloc, removing leading 'www.' if present,
    and ensuring the path ends with a slash.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{netloc}{path}/"


def is_query_url(url):
    return "?" in str(url)


def filter_queries(url):
    url = normalize_url(url)
    if is_query_url:
        return url.split("?")[0]
    

def response_url(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    # Initialize the Chrome driver (ensure chromedriver is in PATH)
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.set_page_load_timeout(300)
        driver.get(url)
        # Wait to ensure dynamic content loads.
        time.sleep(5)
        # Get the final URL after any redirections.
        final_url = driver.current_url
        driver.quit()
        return final_url
    
    except TimeoutException as te:
        driver.quit()
        raise Exception("URL not accessible due to timeout: " + str(te))
    except Exception as e:
        driver.quit()
        raise Exception("URL not accessible: " + str(e))    

def convert_content(content, ext):
    """Convert HTML content to Markdown or plain text."""
    if ext == ".md":
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.body_width = 0
        return converter.handle(content)
    elif ext == ".txt":
        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text(separator="\n")
    else:
        return content


def convert_to_utc_string(unix_timestamp):
    """
    Converts a Unix timestamp to a UTC timestamp string with offset.

    Args:
        unix_timestamp (int): The Unix timestamp (seconds since the epoch).

    Returns:
        str: The formatted UTC timestamp, e.g. "YYYYMMDD_HHMMSS+0000".
    """
    utc_datetime = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    return utc_datetime.strftime("%Y%m%d_%H%M%S%z")

def log_print(message: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"({timestamp} UTC) {message}")

def clean_text(text):
    """Clean text by removing extra newlines and multiple spaces."""
    text = re.sub(r"\n{2,}", "\n", text)
    lines = [re.sub(r" +", " ", line.strip()) for line in text.splitlines()]
    return "\n".join(lines)


def get_page_slug(url, base_url):
    """Extract a slug from the URL relative to the base URL."""
    if not url.startswith(base_url):
        return "unknown"
    relative = url[len(base_url) :].strip("/")
    if relative == "":
        return "base"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", relative)
    return slug


def save_content(url, content, depth, ext, base_url, data_folder):
    """Convert, clean, and save content to a file; return the filename."""
    # converted = convert_content(content, ext)
    # cleaned = clean_text(content)
    slug = get_page_slug(url, base_url)
    timestamp = convert_to_utc_string(int(time.time()))
    filename = os.path.join(
        data_folder, f"scraped_content_depth{depth}_{slug}_{timestamp}{ext}"
    )
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        log_print(f"[DEBUG] Saved '{filename}' (Size: {os.path.getsize(filename)} bytes)")
    except PermissionError as pe:
        log_print(f"[ERROR] Permission denied when writing to '{filename}': {pe}")
    return filename

def generate_json_filename(desired_base, depth):
    return f"{desired_base.replace('/', '%')}_depth{depth}_{convert_to_utc_string(int(time.time()))}.json"
