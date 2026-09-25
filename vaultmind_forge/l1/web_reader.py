"""Content-focused web reader for LPG-L1 reference gathering.

WHY THIS EXISTS
`webfetch` returns whole pages, including site navigation, cookie banners,
footers, and "Sign in" chrome. For a page like the GitHub awesome-list that
means roughly 80% of the returned bytes are boilerplate that crowds out the
content an agent actually needs. This module fetches a URL and reduces the
response to main content as plain text, using only the standard library.

WHAT IT DOES NOT DO
It is not a browser. It cannot render JavaScript, so pages that build their
content client-side will come back thin. When that happens this module reports
`rendered: false` so the caller knows the result is incomplete rather than
quietly trusting an empty extraction. Use a real browser for those.

DESIGN CONSTRAINTS (deliberate, do not relax without reading the reason)
- Standard library only. LPG targets Python 3.12 and this must run in the
  restricted environments described in AGENTS.md without an install step.
- Never executes content. Extracted text is untrusted data. Nothing here
  grants authority, permission, or consent, matching the advisory-only rule in
  LPGL1/L1/schemas/surface-binding.schema.json.
- Read-only over the network. No POST, no credentials, no cookies sent.
- Politeness: identifies itself and honours a bounded timeout.

REFINEMENT NOTES FOR LATER EDITION
- Extraction currently uses tag-stripping plus a boilerplate filter. A
  readability-style scoring pass would beat it on prose pages.
- No caching layer yet; repeated fetches of the same URL re-request.
- Single page only. `fetch_many` exists but there is no crawl frontier,
  depth limit, or visited set.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable

USER_AGENT = "lpg-l1-reference-reader/0.1 (+https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration)"
DEFAULT_TIMEOUT = 30
MAX_BYTES = 8_000_000

# Elements whose entire subtree is chrome, not content.
DROP_SUBTREE = {
    "script", "style", "noscript", "template", "svg", "canvas", "iframe",
    "nav", "header", "footer", "aside", "form", "button", "select", "textarea",
}

# Void elements never receive an end tag. They must not be counted in the skip
# depth, or one <img> or <path> inside a <nav> permanently unbalances the
# depth counter and everything after it is silently discarded.
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Elements that imply a line break in the extracted text.
BLOCK_TAGS = {
    "p", "div", "section", "article", "main", "br", "hr", "tr", "table",
    "ul", "ol", "dl", "dd", "dt", "blockquote", "pre", "h1", "h2", "h3",
    "h4", "h5", "h6", "figcaption", "address", "details", "summary",
}

# Content-bearing elements. When any of these are present we keep only what is
# inside them, which removes most site chrome without a scoring pass.
#
# Ranking matters. GitHub wraps its entire application UI, including the file
# listing and nav, in <main>, and puts the actual README in a nested
# <article class="markdown-body">. Selecting the first root encountered would
# pick <main> and return the whole chrome. The root with the most text wins.
CONTENT_ROOTS = {"main", "article", "section", "div"}
ROOT_RANK = {"article": 3, "main": 2, "section": 1, "div": 0}

# Class/id fragments that identify repeated chrome even inside kept sections.
CHROME_PATTERN = re.compile(
    r"(nav|menu|sidebar|footer|header|banner|breadcrumb|pagination|cookie|consent|"
    r"social|share|subscribe|newsletter|advert|promo|masthead|skip-link|"
    r"site-header|site-footer|github-header)",
    re.IGNORECASE,
)

# Markers that indicate a wrapper is the article body rather than chrome.
LABELLED_CONTENT = re.compile(
    r"(markdown|readme|content|post|entry|prose|article|body)",
    re.IGNORECASE,
)

# A region shorter than this is treated as chrome regardless of quality.
MIN_CONTENT_CHARS = 400

# Weight given to each anchor when scoring text density. Tuned so that prose
# with a normal number of inline links outranks a link-only listing.
LINK_PENALTY = 40

# Navigational link runs: "Sign in  Sign up  Pricing  Docs  Blog  ..."
_LINK_RUN = re.compile(r"^\s*\|?\s*(sign in|sign up|log ?in|log ?out|register|"
                       r"pricing|solutions|resources|enterprise|search|"
                       r"skip to content)\b", re.IGNORECASE)


class _RegionBuilder(HTMLParser):
    """Collect text for every candidate content region in a single pass.

    Each candidate region is a stack frame that accumulates the visible text
    inside it, plus a count of anchors. Scoring happens afterwards in
    `best_region` so the selection rule stays in one testable place.

    Why regions are scored rather than first-match-wins: GitHub wraps its whole
    application UI, file listing and nav included, in <main>, and puts the
    actual README in a nested <article class="markdown-body">. Taking the first
    root encountered returns the entire chrome instead of the article.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[dict] = [
            {"tag": "", "rank": -1, "text": [], "links": 0, "depth": 0}
        ]
        self._skip_depth = 0
        self._pending_break = False
        self.regions: list[dict] = []

    # -- helpers ---------------------------------------------------------
    def _emit(self, text: str) -> None:
        if self._skip_depth or not text:
            return
        if self._pending_break:
            self._stack[-1]["text"].append("\n\n")
            self._pending_break = False
        self._stack[-1]["text"].append(text)

    def _break(self) -> None:
        if not self._skip_depth:
            self._pending_break = True

    def _pop_region(self) -> None:
        frame = self._stack.pop()
        if frame["rank"] >= 0:
            frame["text"] = "".join(frame["text"])
            self.regions.append(frame)
            parent = self._stack[-1]
            # Let the parent keep the text and the anchor count, so an ancestor
            # wrapper is scored on the same content as its child. Without the
            # link rollup every ancestor looks anchor-free and wins on length.
            parent["text"].append(frame["text"])
            parent["links"] += frame["links"]

    # -- HTMLParser hooks ------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth:
            # A void element has no end tag, so it must not change the depth
            # or the counter never returns to zero and the rest is lost.
            if tag not in VOID_ELEMENTS:
                self._skip_depth += 1
            return

        if tag in DROP_SUBTREE:
            self._skip_depth = 1
            return

        marker = " ".join(f"{k}={v or ''}" for k, v in attrs if k in ("class", "id", "role"))
        # NOTE: chrome is deliberately NOT removed by skipping subtrees here.
        # An earlier version matched class/id against CHROME_PATTERN and skipped
        # those subtrees; on real pages that silently discarded the article
        # itself, because site wrappers carry names like "application-main" and
        # the article sits several levels inside them. Region scoring in
        # `best_region` plus the line filter in `_clean` remove chrome
        # without risking the loss of real content.

        rank = ROOT_RANK.get(tag, -1)
        # A labelled wrapper is a stronger candidate than its bare tag.
        if rank >= 0 and marker and LABELLED_CONTENT.search(marker):
            rank += 2

        if tag in BLOCK_TAGS:
            self._break()

        if tag in CONTENT_ROOTS:
            self._stack.append(
                {"tag": tag, "rank": rank, "text": [], "links": 0, "depth": len(self._stack)}
            )
            return
        if tag == "a":
            self._stack[-1]["links"] += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCK_TAGS:
            self._break()

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in CONTENT_ROOTS and len(self._stack) > 1:
            self._pop_region()
            return
        if tag in BLOCK_TAGS:
            self._break()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = re.sub(r"[ \t\r\f\v]+", " ", data)
        if text.strip():
            self._emit(text.strip())

    def close(self) -> None:  # type: ignore[override]
        super().close()
        while len(self._stack) > 1:
            self._pop_region()

    # -- scoring ---------------------------------------------------------
    def best_region(self) -> str:
        """Return the region most likely to be the article body.

        Ranking is driven by anchor density, not raw length. A page wrapper
        that contains a file listing has more text than the article but is
        almost entirely links; prose has few. Length is only a tie-breaker and
        a floor, because a short high-quality article should still beat a long
        navigation dump.

        This matters in practice: on a GitHub repo page the outermost <main>
        is roughly 17k characters while the README <article> is 15k, and the
        2k difference is almost entirely the file listing. Ranking by length
        picks the wrapper and returns the file table instead of the README.

        Anchor density alone is not sufficient either. A fenced code block has
        no anchors at all, so density scoring selects a 600-character config
        sample over a 15k-character README. Semantic rank therefore dominates,
        and density is only a tie-breaker within the same rank tier: the
        labelled article wrapper beats a bare <div> regardless of length.
        """
        best = ""
        best_score = -1.0
        for region in self.regions:
            text = region["text"]
            if not isinstance(text, str):
                continue
            length = len(text.strip())
            if length < MIN_CONTENT_CHARS:
                continue
            # Prose has few anchors; a menu or file list is mostly anchors.
            density = length / (1 + region["links"] * LINK_PENALTY)
            # Rank tiers dominate: a semantic article wrapper outranks a bare
            # div. Within a tier, prefer link-poor text, then prefer more text.
            score = (
                region["rank"] * 1_000_000.0
                + density * 100.0
                + min(length, 20_000) / 20_000.0
            )
            if score > best_score:
                best_score = score
                best = text
        return best


def _clean(text: str) -> str:
    """Normalise whitespace and drop obvious navigation link runs."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    out: list[str] = []
    for line in (line.strip() for line in text.splitlines()):
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if _LINK_RUN.match(line) and len(line) < 60:
            continue
        out.append(line)
    return "\n".join(out).strip()


@dataclass
class Page:
    url: str
    status: int
    content_type: str
    text: str
    rendered: bool = True
    warnings: list[str] = field(default_factory=list)

    @property
    def is_thin(self) -> bool:
        """True when extraction likely failed rather than found a short page."""
        return len(self.text) < 400


def _decode(body: bytes, content_type: str) -> str:
    charset = None
    match = re.search(r"charset=([\w\-]+)", content_type or "", re.IGNORECASE)
    if match:
        charset = match.group(1)
    for candidate in filter(None, (charset, "utf-8")):
        try:
            return body.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


def fetch(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_BYTES,
) -> Page:
    """Fetch one URL and reduce it to main content as text.

    This performs a GET only. It never sends credentials or cookies.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"refusing non-http url: {url!r}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        },
    )

    warnings: list[str] = []
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200) or 200
            content_type = response.headers.get("Content-Type", "")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                body = body[:max_bytes]
                warnings.append(f"truncated at {max_bytes} bytes")
    except urllib.error.HTTPError as exc:
        return Page(url, exc.code, exc.headers.get("Content-Type", ""), "", False,
                    [f"http {exc.code}: {exc.reason}"])
    except urllib.error.URLError as exc:
        return Page(url, 0, "", "", False, [f"network error: {exc.reason}"])
    except TimeoutError:
        return Page(url, 0, "", "", False, [f"timeout after {timeout}s"])

    text_source = _decode(body, content_type)

    if "json" in content_type.lower():
        try:
            return Page(url, status, content_type, json.dumps(json.loads(text_source), indent=2))
        except json.JSONDecodeError:
            warnings.append("content-type said json but body did not parse")

    if "html" not in content_type.lower() and "xml" not in content_type.lower():
        return Page(url, status, content_type, text_source, True, warnings)

    builder = _RegionBuilder()
    try:
        builder.feed(text_source)
        builder.close()
    except Exception as exc:  # malformed markup must not lose the page
        warnings.append(f"parse stopped early: {type(exc).__name__}")
    text = _clean(builder.best_region())

    if not text.strip() and text_source:
        # No candidate region scored well enough. Retry over the whole document
        # by treating the top-level frame as a region, rather than reporting an
        # empty page. Chrome is still removed by the DROP_SUBTREE and
        # CHROME_PATTERN filters, and the caller is told the extraction was
        # not from a recognised content root.
        whole = _RegionBuilder()
        whole._stack.append({"tag": "document", "rank": 0, "text": [], "links": 0, "depth": 0})
        try:
            whole.feed(text_source)
            whole.close()
        except Exception as exc:
            warnings.append(f"whole-document parse failed: {type(exc).__name__}")
        text = _clean("".join(whole.regions[0]["text"]) if whole.regions else "")
        if text:
            warnings.append("no content root scored; extracted whole document")

    if len(text) < 400:
        warnings.append("thin extraction; page may require JavaScript rendering")

    return Page(url, status, content_type, text, True, warnings)


def fetch_many(urls: Iterable[str], *, timeout: int = DEFAULT_TIMEOUT) -> list[Page]:
    """Fetch several URLs sequentially.

    Sequential on purpose: this is a courtesy fetcher, not a crawler. There is
    deliberately no concurrency, no retry storm, and no crawl frontier here.
    """
    return [fetch(url, timeout=timeout) for url in urls]


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy code page that cannot represent
    # emoji or CJK, which real documentation pages contain in quantity.
    # Without this the CLI crashes on a successful fetch.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        prog="forge-read",
        description="Fetch a URL and print main content as text.",
    )
    parser.add_argument("urls", nargs="+", help="one or more http(s) URLs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)

    pages = [fetch(u, timeout=args.timeout, max_bytes=args.max_bytes) for u in args.urls]

    if args.json:
        print(json.dumps(
            [
                {
                    "url": p.url,
                    "status": p.status,
                    "content_type": p.content_type,
                    "rendered": p.rendered,
                    "thin": p.is_thin,
                    "warnings": p.warnings,
                    "bytes_extracted": len(p.text),
                    "text": p.text,
                }
                for p in pages
            ],
            indent=2,
        ))
        return 0 if all(p.status and p.status < 400 and p.text for p in pages) else 1

    failures = 0
    for page in pages:
        print(f"=== {page.url} [{page.status}] {len(page.text)} chars")
        for warning in page.warnings:
            print(f"  ! {warning}")
        print()
        print(page.text or "(no content extracted)")
        print()
        if not page.text or page.status >= 400:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
