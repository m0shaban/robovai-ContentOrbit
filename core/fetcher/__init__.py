# RSS Feed Fetcher Module
from .rss_parser import RSSFetcher

__all__ = ["RSSFetcher"]

# Re-export for convenience
Fetcher = RSSFetcher
