"""HTML DOM and metadata inspector for technical SEO/AEO analysis.

Parses raw HTML using Python's standard library html.parser, extracting
structured indexability signals, metadata tags, heading hierarchy, links,
images, scripts, and Schema.org JSON-LD structured data.
"""

from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class HTMLPageInspector(HTMLParser):
    """Event-driven parser inspecting technical SEO signals from HTML."""

    def __init__(self, target_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.target_url = target_url
        self.base_domain = urlparse(target_url).netloc.lower() if target_url else ""

        # Title & Meta
        self.title: Optional[str] = None
        self.meta_description: Optional[str] = None
        self.meta_robots: List[str] = []
        self.viewport: Optional[str] = None
        self.open_graph: Dict[str, str] = {}

        # Canonical
        self.canonical_hrefs: List[str] = []

        # Headings
        self.h1_tags: List[str] = []
        self.h2_tags: List[str] = []
        self.h3_tags: List[str] = []

        # Links & Media
        self.links: List[Dict[str, Any]] = []
        self.images: List[Dict[str, Any]] = []
        self.scripts: List[Dict[str, Any]] = []
        self.stylesheets: List[str] = []

        # Structured Data
        self.json_ld_raw: List[str] = []
        self.json_ld_schemas: List[Dict[str, Any]] = []
        self.json_ld_errors: List[str] = []

        # Internal state tracking
        self._current_tag: Optional[str] = None
        self._text_accumulator: List[str] = []
        self._current_link: Optional[Dict[str, Any]] = None
        self._inside_script_json_ld: bool = False
        self._html_size_bytes: int = 0

    @classmethod
    def inspect(cls, html_content: str, target_url: str = "") -> HTMLPageInspector:
        """Factory method to parse an HTML document and return inspector results."""
        inspector = cls(target_url=target_url)
        inspector._html_size_bytes = len(html_content.encode("utf-8")) if html_content else 0
        if html_content:
            inspector.feed(html_content)
            inspector.close()
        return inspector

    @property
    def html_size_bytes(self) -> int:
        """Total size of the parsed HTML in bytes."""
        return self._html_size_bytes

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower == "title":
            self._current_tag = "title"
            self._text_accumulator = []

        elif tag_lower == "meta":
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            content = attr_dict.get("content", "").strip()

            if name == "description":
                self.meta_description = content
            elif name in ("robots", "googlebot", "bingbot"):
                directives = [d.strip().lower() for d in content.split(",") if d.strip()]
                self.meta_robots.extend(directives)
            elif name == "viewport":
                self.viewport = content
            elif prop.startswith("og:"):
                self.open_graph[prop] = content

        elif tag_lower == "link":
            rel = attr_dict.get("rel", "").lower()
            href = attr_dict.get("href", "").strip()
            if "canonical" in rel and href:
                self.canonical_hrefs.append(href)
            elif "stylesheet" in rel and href:
                self.stylesheets.append(href)

        elif tag_lower in ("h1", "h2", "h3"):
            self._current_tag = tag_lower
            self._text_accumulator = []

        elif tag_lower == "a":
            href = attr_dict.get("href", "").strip()
            rel = attr_dict.get("rel", "").lower()

            is_empty = href in ("", "#") or href.lower().startswith("javascript:")
            is_internal = True
            if href.startswith(("http://", "https://", "//")):
                link_netloc = urlparse(href if not href.startswith("//") else f"https:{href}").netloc.lower()
                is_internal = (link_netloc == self.base_domain) if self.base_domain else False

            self._current_link = {
                "href": href,
                "rel": rel,
                "is_internal": is_internal,
                "is_empty": is_empty,
                "text": "",
            }
            self._current_tag = "a"
            self._text_accumulator = []

        elif tag_lower == "img":
            src = attr_dict.get("src", "").strip()
            alt = attr_dict.get("alt")
            loading = attr_dict.get("loading", "").lower()
            has_alt = alt is not None and len(alt.strip()) > 0
            self.images.append({
                "src": src,
                "alt": alt,
                "loading": loading,
                "has_alt": has_alt,
            })

        elif tag_lower == "script":
            script_type = attr_dict.get("type", "").lower()
            src = attr_dict.get("src", "").strip()
            is_async = "async" in attr_dict
            is_defer = "defer" in attr_dict

            if script_type == "application/ld+json":
                self._inside_script_json_ld = True
                self._text_accumulator = []
            elif src:
                self.scripts.append({
                    "src": src,
                    "type": script_type,
                    "is_render_blocking": not (is_async or is_defer),
                    "is_external": True,
                })

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()

        if tag_lower == "title" and self._current_tag == "title":
            text = "".join(self._text_accumulator).strip()
            if text:
                self.title = text
            self._current_tag = None

        elif tag_lower == "h1" and self._current_tag == "h1":
            text = "".join(self._text_accumulator).strip()
            if text:
                self.h1_tags.append(text)
            self._current_tag = None

        elif tag_lower == "h2" and self._current_tag == "h2":
            text = "".join(self._text_accumulator).strip()
            if text:
                self.h2_tags.append(text)
            self._current_tag = None

        elif tag_lower == "h3" and self._current_tag == "h3":
            text = "".join(self._text_accumulator).strip()
            if text:
                self.h3_tags.append(text)
            self._current_tag = None

        elif tag_lower == "a" and self._current_link is not None:
            text = "".join(self._text_accumulator).strip()
            self._current_link["text"] = text
            self.links.append(self._current_link)
            self._current_link = None
            if self._current_tag == "a":
                self._current_tag = None

        elif tag_lower == "script" and self._inside_script_json_ld:
            raw_json = "".join(self._text_accumulator).strip()
            if raw_json:
                self.json_ld_raw.append(raw_json)
                try:
                    parsed = json.loads(raw_json)
                    if isinstance(parsed, dict):
                        self.json_ld_schemas.append(parsed)
                    elif isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict):
                                self.json_ld_schemas.append(item)
                except Exception as exc:
                    self.json_ld_errors.append(str(exc))
            self._inside_script_json_ld = False

    def handle_data(self, data: str) -> None:
        if self._current_tag in ("title", "h1", "h2", "h3", "a") or self._inside_script_json_ld:
            self._text_accumulator.append(data)
