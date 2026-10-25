"""Text and domain normalization utilities."""

import re
from urllib.parse import urlparse


def normalize_query(query: str) -> str:
    """Normalize query text for deterministic hashing and comparisons."""
    cleaned = re.sub(r"[^\w\s\-\?]", "", query.lower().strip())
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_domain(url_or_domain: str) -> str:
    """Extract clean lowercase root domain without scheme, port, or www."""
    raw = url_or_domain.strip().lower()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    domain = parsed.netloc or parsed.path
    # Strip port if present
    domain = domain.split(":")[0]
    # Strip www
    if domain.startswith("www."):
        domain = domain[4:]
    return domain
