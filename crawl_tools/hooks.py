from typing import Union, Dict
import asyncio
import random
import json
from crawl4ai import CrawlResult
from crawl_tools.utils import (
    normalize_url,
    log_print,
    convert_crawl_result,
    save_content,

)

async def local_result_hook(
    result:CrawlResult, 
    desired_base: str, 
    ext:str, 
    sleep_timer:Union[int,float], 
    data_folder:str, 
    json_lock:asyncio.Lock,
    url_to_filename: Dict,
    _skip_diff_base:bool=False,
):
    """
    Asynchronous hook that processes each scraped result.
       It saves the page if the normalized URL starts with the desired base,
    updates the global mapping, and (optionally) waits between calls for a random duration with specified upper bound
    """
    if result is None:
        log_print("[DEBUG] Hook received None result")
        return
    norm_url = normalize_url(result.url)
    if _skip_diff_base and not norm_url.startswith(desired_base):
        log_print(
            f"[DEBUG] Skipping {result.url} (normalized: {norm_url} does not start with {desired_base})"
        )
        return
    if result.success:
        content = convert_crawl_result(result, ext)
        if not content or str(content).strip() == "":
            log_print(f"[WARNING] Parsed content from {result.url} is empty.")
        else:
            depth = int(result.metadata.get("depth", 0) or 0)
            filename = save_content(
                result.url, content, depth, ext, desired_base, data_folder
            )
            async with json_lock:
                url_to_filename[result.url] = filename
            log_print(f"[DEBUG] Updated mapping for {result.url}")
    else:
        msg = f"[ERROR] Failed to scrape {result.url}: {result.error_message}"
        log_print(msg)
        async with json_lock:
                url_to_filename[result.url] = msg
    sleep_rand = random.uniform(0, sleep_timer)
    log_print(f"[INFO] Sleeping for {sleep_rand:.2f}s...")
    await asyncio.sleep(sleep_rand)

    
async def api_result_hook(
    result:CrawlResult, 
    desired_base: str, 
    ext:str, 
    sleep_timer:Union[int,float], 
    data_folder:str, 
    json_lock:asyncio.Lock,
    url_to_filename: Dict,
    _skip_diff_base:bool=False,
):
    """
    Asynchronous hook that processes each scraped result.
       It saves the page if the normalized URL starts with the desired base,
    updates the global mapping, and (optionally) waits between calls for a random duration with specified upper bound
    """
    if result is None:
        log_print("[DEBUG] Hook received None result")
        return
    norm_url = normalize_url(result.url)
    if _skip_diff_base and not norm_url.startswith(desired_base):
        log_print(
            f"[DEBUG] Skipping {result.url} (normalized: {norm_url} does not start with {desired_base})"
        )
        return
    if result.success:
        content = convert_crawl_result(result, ext)
        if not content or str(content).strip() == "":
            log_print(f"[WARNING] Parsed content from {result.url} is empty.")
        else:
            depth = int(result.metadata.get("depth", 0) or 0)
            filename = save_content(
                result.url, content, depth, ext, desired_base, data_folder
            )
            async with json_lock:
                url_to_filename[result.url] = filename
            log_print(f"[DEBUG] Updated mapping for {result.url}")
    else:
        msg = f"[ERROR] Failed to scrape {result.url}: {result.error_message}"
        log_print(msg)
        async with json_lock:
                url_to_filename[result.url] = msg
    sleep_rand = random.uniform(0, sleep_timer)
    log_print(f"[INFO] Sleeping for {sleep_rand:.2f}s...")
    await asyncio.sleep(sleep_rand)

async def periodic_json_update(
    debug_file: str,
    json_lock:asyncio.Lock,
    url_to_filename:Dict,
    interval=60,
):
    """Periodically write the URL mapping to a JSON file."""
    while True:
        await asyncio.sleep(interval)
        async with json_lock:
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(url_to_filename, f, indent=4)
            log_print(f"[DEBUG] Periodically updated URL mapping saved to '{debug_file}'")
