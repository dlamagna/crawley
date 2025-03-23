import time
import re
from urllib.parse import urlparse
import html2text
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone
import textwrap
from crawl4ai import CrawlResult


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
            print("[DEBUG] Raw HTML length:", len(content))
            print("[DEBUG] Converted Markdown length:", len(converted))
            print("[DEBUG] Converted Markdown preview:", converted[:200])
        return converted
    elif ext == ".txt":
        soup = BeautifulSoup(content, "html.parser")
        txt = soup.get_text(separator="\n")
        if verbose:
            print("[DEBUG] Raw HTML length:", len(content))
            print("[DEBUG] Extracted Text length:", len(txt))
            print("[DEBUG] Extracted Text preview:", txt[:200])
        return txt
    else:
        return content


def convert_crawl_result(result: CrawlResult, ext, cleaned=False):
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
        str: The formatted UTC timestamp, e.g. "YYYY_MM_DD_HH_MM_SS+0000".
    """
    utc_datetime = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    return utc_datetime.strftime("%Y_%m_%d_%H_%M_%S%z")


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
        print(f"[DEBUG] Saved '{filename}' (Size: {os.path.getsize(filename)} bytes)")
    except PermissionError as pe:
        print(f"[ERROR] Permission denied when writing to '{filename}': {pe}")
    return filename
