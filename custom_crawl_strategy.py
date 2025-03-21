from urllib.parse import urlparse
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

class CustomFilteredCrawlStrategy(BFSDeepCrawlStrategy):
    """Custom deep crawl strategy to only follow links within a specified base path."""
    
    def __init__(self, base_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = base_path.rstrip("/")

    async def extract_links(self, page, *args, **kwargs):
        """Extract only links that match the allowed base path."""
        links = await super().extract_links(page, *args, **kwargs)
        filtered_links = [link for link in links if self.is_valid_link(link)]
        return filtered_links

    def is_valid_link(self, link):
        """Check if the link starts with the desired base path."""
        parsed_link = urlparse(link)
        return parsed_link.path.startswith(self.base_path)

