"""
biomni_tools - Compatibility module for legacy imports.

This module provides backward compatibility for code that imports from 'biomni_tools'
instead of the current 'biomni.tool' package structure.

Usage:
    from biomni_tools import search_protocols, advanced_web_search_claude
    
Is equivalent to:
    from biomni.tool.literature import advanced_web_search_claude
"""

# Re-export all tools from biomni.tool.literature
from biomni.tool.literature import (
    advanced_web_search_claude,
    advanced_web_search_serper,
    extract_pdf_content,
    extract_url_content,
    fetch_supplementary_info_from_doi,
    query_arxiv,
    query_pubmed,
    query_scholar,
    search_google,
)

# Re-export search_protocols if it exists
try:
    from biomni.tool.literature import search_protocols
except ImportError:
    # search_protocols might be in a different module or doesn't exist
    def search_protocols(query: str, *args, **kwargs) -> str:
        """Search for protocols using PubMed as fallback."""
        return query_pubmed(f"protocol {query}", max_papers=5)

# Alias for google_search_with_tool (may be referenced)
google_search_with_tool = search_google

# Export all available functions
__all__ = [
    'advanced_web_search_claude',
    'advanced_web_search_serper',
    'extract_pdf_content',
    'extract_url_content',
    'fetch_supplementary_info_from_doi',
    'google_search_with_tool',
    'query_arxiv',
    'query_pubmed',
    'query_scholar',
    'search_google',
    'search_protocols',
]
