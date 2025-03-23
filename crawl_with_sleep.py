import asyncio
import os
import argparse
import random
import json
from urllib.parse import urlparse
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    FilterChain,
    URLPatternFilter,
    BFSDeepCrawlStrategy,
    CrawlResult,
)
import json

from crawl import *

# Create output folders if they don't exist
DATA_FOLDER = "data"
DEBUG_FOLDER = "debug"
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DEBUG_FOLDER, exist_ok=True)

# Global dictionary to store URL -> filename mapping.
url_to_filename = {}

json_lock = asyncio.Lock()  # for saving JSON mappping


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Crawl a website using Crawl4AI, convert pages to Markdown, save output immediately, and log URL-to-file mapping."
    )
    parser.add_argument(
        "-u", "--url", required=True, help="The base website URL to scrape"
    )
    parser.add_argument(
        "-d",
        "--max_depth",
        type=int,
        default=2,
        help="Maximum depth to crawl (default: 2, use -1 for unlimited, 0 for only the base page).",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=300000,
        help="Timeout per page request in milliseconds (default: 300000).",
    )
    parser.add_argument(
        "-s",
        "--sleep_timer",
        type=float,
        default=2.0,
        help="Upper bound of randomized sleep timer in seconds after each process finishes (default: 2.0).",
    )
    parser.add_argument(
        "-c",
        "--concurrent_tasks",
        type=int,
        default=3,
        help="Number of concurrent asynchronous tasks for scraping (default: 3).",
    )
    parser.add_argument(
        "--ext",
        choices=[".md", ".txt", ".html"],
        default=".md",
        help="Output file format: .md for Markdown (HTML converted to Markdown) .txt for plain text, .html for raw HTML",
    )
    return parser.parse_args()


async def periodic_update(
    debug_file: str,
    interval=60,
):
    """Periodically write the URL mapping to a JSON file."""
    while True:
        await asyncio.sleep(interval)
        async with json_lock:
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(url_to_filename, f, indent=4)
            print(f"[DEBUG] Periodically updated URL mapping saved to '{debug_file}'")


async def on_result_hook(result:CrawlResult, desired_base, ext, sleep_timer, data_folder, _skip_diff_base=False):
    """
    Asynchronous hook that processes each scraped result.
       It saves the page if the normalized URL starts with the desired base,
    updates the global mapping, and (optionally) waits between calls for a random duration with specified upper bound
    """
    if result is None:
        print("[DEBUG] Hook received None result")
        return
    norm_url = normalize_url(result.url)
    if _skip_diff_base and not norm_url.startswith(desired_base):
        print(
            f"[DEBUG] Skipping {result.url} (normalized: {norm_url} does not start with {desired_base})"
        )
        return
    if result.success:
        content = convert_crawl_result(result, ext)
        if not content or str(content).strip() == "":
            print(f"[WARNING] Parsed content from {result.url} is empty.")
        else:
            depth = int(result.metadata.get("depth", 0) or 0)
            filename = save_content(
                result.url, content, depth, ext, desired_base, data_folder
            )
            async with json_lock:
                url_to_filename[result.url] = filename
            print(f"[DEBUG] Updated mapping for {result.url}")
    else:
        msg = f"[ERROR] Failed to scrape {result.url}: {result.error_message}"
        print(msg)
        async with json_lock:
                url_to_filename[result.url] = msg
    sleep_rand = random.uniform(0, sleep_timer)
    print(f"[INFO] Sleeping for {sleep_rand:-2f}s...")
    await asyncio.sleep(sleep_rand)


async def main(
    data_folder=DATA_FOLDER,
    debug_folder=DEBUG_FOLDER,
):
    args = parse_arguments()
    parsed_url = urlparse(args.url)
    # Normalize the base URL to ensure it ends with a slash.
    desired_base = normalize_url(args.url)
    print(f"[DEBUG] Base URL set to: {desired_base}")

    # Create data directory configured wiht website name:
    data_folder = os.path.join(
        data_folder, parsed_url.netloc, parsed_url.path.replace("/", "%")
    )
    os.makedirs(data_folder, exist_ok=True)
    debug_file = os.path.join(debug_folder, f"{desired_base.replace('/', '%')}.json")
    
    # Generate a custom filter for URLs: only stay within the specified base
    url_filter = URLPatternFilter(patterns=[f"{desired_base}*"])
    crawler_config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=None if args.max_depth == -1 else args.max_depth,
            filter_chain=FilterChain([url_filter]),
            include_external=False,
        ),
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed"), 
            # options={
            #     "body_width": 80,
            # },
            ## -> not required for now
        ),
        verbose=True,
        page_timeout=args.timeout,
        wait_until="networkidle",
        stream=True,
        exclude_external_links=True,
        exclude_social_media_links=True,
    )

    updater_task = asyncio.create_task(
        periodic_update(debug_file=debug_file)
    )
    async with AsyncWebCrawler(
        config=BrowserConfig(
            headless=True,
            text_mode=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ),
        # concurrent_tasks=args.concurrent_tasks, ## commented out until bugfix examined
    ) as crawler:
        print(
            f"[DEBUG] Starting crawl with depth {args.max_depth } and sleep timer of {args.sleep_timer}s between hook calls..."
        )
        async for result in await crawler.arun(args.url, config=crawler_config):
            await on_result_hook(
                result, desired_base, args.ext, args.sleep_timer, data_folder
            )

    # Cancel the periodic updater and perform a final write of the JSON mapping.
    updater_task.cancel()
    async with json_lock:
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(url_to_filename, f, indent=4)
    print(f"[DEBUG] Final URL mapping saved to '{debug_file}'")


if __name__ == "__main__":
    asyncio.run(main())
