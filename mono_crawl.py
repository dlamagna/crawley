import asyncio
import os
import time
import argparse
import re
import json
from urllib.parse import urlparse
from crawl4ai import (
    AsyncWebCrawler, 
    CrawlerRunConfig, 
    BrowserConfig,
    BFSDeepCrawlStrategy,
    DefaultMarkdownGenerator,
    PruningContentFilter,
)
import html2text
import json
from bs4 import BeautifulSoup

from custom_crawl_strategy import CustomFilteredCrawlStrategy
# Create output folders if they don't exist
DATA_FOLDER = "data"
DEBUG_FOLDER = "debug"
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DEBUG_FOLDER, exist_ok=True)

# Global dictionary to store URL -> filename mapping.
url_to_filename = {}

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Crawl a website using Crawl4AI, convert pages to Markdown, save output immediately, and log URL-to-file mapping."
    )
    parser.add_argument("-u", "--url", required=True,
                        help="The base website URL to scrape")
    parser.add_argument("-d", "--max_depth", type=int, default=2,
                        help="Maximum depth to crawl (default: 2, use -1 for unlimited, 0 for only the base page).")
    parser.add_argument("-t", "--timeout", type=int, default=120000,
                        help="Timeout per page request in milliseconds (default: 120000).")
    parser.add_argument("-s", "--sleep_timer", type=float, default=1.0,
                        help="Sleep timer in seconds between processing results (default: 1.0).")
    parser.add_argument("--ext", choices=[".md", ".txt"], default=".md",
                        help="Output file format: .md for Markdown (HTML converted to Markdown) or .txt for plain text.")
    return parser.parse_args()

def convert_content(content, ext):
    """Convert HTML content to Markdown or plain text."""
    if ext == ".md":
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.body_width = 0
        return converter.handle(content)
    elif ext == ".txt":
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(separator="\n")
    else:
        return content

def clean_text(text):
    """Clean text by removing extra newlines and multiple spaces."""
    text = re.sub(r'\n{2,}', '\n', text)
    lines = [re.sub(r' +', ' ', line.strip()) for line in text.splitlines()]
    return "\n".join(lines)

def get_page_slug(url, base_url):
    """Extract a slug from the URL relative to the base URL."""
    if not url.startswith(base_url):
        return "unknown"
    relative = url[len(base_url):].strip('/')
    if relative == "":
        return "base"
    slug = re.sub(r'[^A-Za-z0-9]+', '_', relative)
    return slug

def save_content(url, content, depth, ext, base_url):
    """Convert, clean, and save content to a file; return the filename."""
    converted = convert_content(content, ext)
    cleaned = clean_text(converted)
    slug = get_page_slug(url, base_url)
    timestamp = int(time.time())
    filename = os.path.join(DATA_FOLDER, f"scraped_content_depth{depth}_{slug}_{timestamp}{ext}")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(cleaned)
    print(f"[DEBUG] Saved '{filename}' (Size: {os.path.getsize(filename)} bytes)")
    return filename

async def on_result_hook(result, desired_base, ext, sleep_timer):
    """
    Asynchronous hook that processes each scraped result.
    It saves the page if the URL starts with the desired base, updates the global mapping,
    and writes the mapping to a JSON file in the debug folder after every successful scrape.
    """
    if result is None:
        print("[DEBUG] Hook received None result")
        return
    if not result.url.startswith(desired_base):
        print(f"[DEBUG] Skipping {result.url} (outside desired path)")
        return
    if result.success:
        content = result.markdown.fit_markdown if ext == ".md" else result.raw_text
        if not content or content.strip() == "":
            print(f"[WARNING] Parsed content from {result.url} is empty.")
        else:
            depth = int(result.metadata.get('depth', 0) or 0)
            filename = save_content(result.url, content, depth, ext, desired_base)
            url_to_filename[result.url] = filename
            # Write the updated mapping to a debug JSON file immediately.
            debug_file = os.path.join(DEBUG_FOLDER, "results.json")
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(url_to_filename, f, indent=4)
            print(f"[DEBUG] Updated URL mapping saved to '{debug_file}'")
    else:
        print(f"[ERROR] Failed to scrape {result.url}: {result.error_message}")
    await asyncio.sleep(sleep_timer)

async def main():
    args = parse_arguments()
    parsed_url = urlparse(args.url)
    # Normalize the base URL to ensure it ends with a slash.
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path.rstrip('/')}/"
    print(f"[DEBUG] Base URL set to: {base_url}")
    desired_base = base_url  # We only want URLs that start exactly with the input base.
    
    # Create data directory configured wiht website name:
    DATA_FOLDER = os.path.join(DATA_FOLDER, parsed_url.netloc, parsed_url.path.replace("/", "_"))
    # Cusotm crawl strategy to ensure staying within the base URL provided
    custom_strategy = CustomFilteredCrawlStrategy(
        base_path=parsed_url.path.rstrip("/"),
        desired_base=desired_base,
        max_depth=None if args.max_depth == -1 else args.max_depth,
        include_external=False
    )
    crawler_config = CrawlerRunConfig(
        deep_crawl_strategy=custom_strategy,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
        ),
        verbose=True,
        page_timeout=args.timeout,
        wait_until="networkidle"
    )
    
    async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            text_mode=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ), concurrent_tasks=3) as crawler:
        # Register hook using a lambda to pass extra parameters.
        crawler.hooks = {"after_scrape": lambda result: on_result_hook(result, desired_base, args.ext, args.sleep_timer)}
        print(f"[DEBUG] Starting crawl with sleep timer of {args.sleep_timer} sec between hook calls...")
        results = await crawler.arun(args.url, config=crawler_config)
        print(f"[DEBUG] Crawl complete. Total results: {len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
