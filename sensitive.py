"""Sensitive topic detection for the GitLab Guide chatbot."""

import re

SENSITIVE_KEYWORDS: frozenset[str] = frozenset([
    "compensation",
    "salary",
    "equity",
    "legal",
    "termination",
    "pip",
    "performance improvement plan",
    "harassment",
    "medical leave",
    "severance",
    "layoff",
])

SENSITIVE_URL_PATHS: frozenset[str] = frozenset([
    "/handbook/total-rewards/",
    "/handbook/legal/",
    "/handbook/people-group/employment/",
])

DISCLAIMER_HTML: str = """
<div style="
    background-color: #fff3e0;
    border-left: 4px solid #fc6d26;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 12px;
    font-family: sans-serif;
    font-size: 0.9em;
    color: #3d2b00;
">
    <strong style="color: #fc6d26;">⚠️ Sensitive Topic</strong><br>
    For official guidance on this topic, please verify with your HR/People Ops team or Legal before acting on this information.
</div>
"""


def is_sensitive(query: str, source_urls: list[str]) -> bool:
    """Return True if query contains a sensitive keyword or any source URL contains a sensitive path.

    - Keyword matching is case-insensitive and uses whole-word/phrase boundaries.
    - URL path matching checks if any URL contains a sensitive path substring.
    - Pure Python, no I/O, cannot fail.
    """
    query_lower = query.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if " " in keyword:
            # Multi-word phrase: simple substring match (case-insensitive)
            if keyword in query_lower:
                return True
        else:
            # Single word: whole-word boundary match
            if re.search(r"\b" + re.escape(keyword) + r"\b", query_lower):
                return True

    for url in source_urls:
        for path in SENSITIVE_URL_PATHS:
            if path in url:
                return True

    return False
