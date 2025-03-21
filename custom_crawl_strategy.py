from urllib.parse import urlparse
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy


class CustomFilteredCrawlStrategy(BFSDeepCrawlStrategy):
    """
    Custom deep crawl strategy that only follows links whose paths start with the specified base path.
    The desired_base parameter enforces that only URLs starting exactly with that string are followed.
    """
    def __init__(self, base_path, desired_base, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path.rstrip("/")
        self.desired_base = desired_base 

    async def extract_links(self, page, *args, **kwargs):
        links = await super().extract_links(page, *args, **kwargs)
        filtered_links = []
        for link in links:
            # Only keep the link if it starts with the desired base.
            if link.startswith(self.desired_base):
                filtered_links.append(link)
            else:
                self.logger.info(f"[DEBUG] Filtering out link: {link}")
        return filtered_links
    
    async def can_process_url(self, url: str, depth: int) -> bool:
        """
        Validates the URL and applies the filter chain.
        For the start URL (depth 0) filtering is bypassed.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Missing scheme or netloc")
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Invalid scheme")
            if "." not in parsed.netloc:
                raise ValueError("Invalid domain")
        except Exception as e:
            self.logger.warning(f"Invalid URL: {url}, error: {e}")
            return False

        if depth != 0 and not await self.filter_chain.apply(url):
            return False
        
        if not url.startswith(self.desired_base):
            self.logger.info(f"Skipping {url} (outside desired path)")
            return False
