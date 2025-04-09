from urllib.parse import urlparse
from crawl4ai import BFSDeepCrawlStrategy, CrawlerRunConfig, CacheMode
from crawl_tools.interactions_js import wait_for_new_page, scroll_and_next
# from crawl.utils import normalize_url


def normalize_url(url):
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/")  # Remove trailing slash
    return f"{parsed.scheme}://{netloc}{path}/"  # Always end with a slash

CustomConfig = CrawlerRunConfig(
    # ... other settings ...
    session_id="some_session",
    js_code=scroll_and_next,
    wait_for=wait_for_new_page,
    js_only=True,
    cache_mode=CacheMode.BYPASS,
)

class CustomPaginationConfig(CrawlerRunConfig):
    pass


class CustomFilteredCrawlStrategy(BFSDeepCrawlStrategy):
    """
    Custom deep crawl strategy that only follows links whose paths start with the specified base path.
    The desired_base parameter enforces that only URLs starting exactly with that string are followed.
    """

    def __init__(self, base_path, desired_base, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path.rstrip("/")
        self.desired_base = desired_base

    # async def extract_links(self, page, *args, **kwargs):
    #     links = await super().extract_links(page, *args, **kwargs)
    #     filtered_links = []
    #     for link in links:
    #         # Only keep the link if it starts with the desired base.
    #         if link.startswith(self.desired_base):
    #             filtered_links.append(link)
    #         else:
    #             self.logger.info(f"[DEBUG] Filtering out link: {link}")
    #     return filtered_links
    # def is_within_desired_base(self, url, desired_base):
    #     normalized_url = normalize_url(url)
    #     normalized_base = normalize_url(desired_base)
    #     return normalized_url.startswith(normalized_base)

    # async def can_process_url(self, url: str, depth: int) -> bool:
    #     """
    #     Validates the URL and applies the filter chain.
    #     For the start URL (depth 0) filtering is bypassed.
    #     """
    #     try:
    #         parsed = urlparse(url)
    #         if not parsed.scheme or not parsed.netloc:
    #             raise ValueError("Missing scheme or netloc")
    #         if parsed.scheme not in ("http", "https"):
    #             raise ValueError("Invalid scheme")
    #         if "." not in parsed.netloc:
    #             raise ValueError("Invalid domain")
    #     except Exception as e:
    #         self.logger.warning(f"Invalid URL: {url}, error: {e}")
    #         return False

    #     if depth != 0 and not await self.filter_chain.apply(url):
    #         return False

    #     if not self.is_within_desired_base(url, self.desired_base):
    #         self.logger.info(f"Skipping {url} (outside desired path)")
    #         return False
