"""Tests for the LPG-L1 web reader.

The reader exists because `webfetch` returns whole pages: for a GitHub repo
page roughly 80% of the bytes are site chrome, which crowds out the content an
agent actually needs. These tests pin the behaviour that fixes that.

Network tests are marked `network` and skipped by default so the suite stays
offline-safe and fast. Run them with:

    pytest vaultmind_forge/tests/test_web_reader.py -m network

The parser tests below use saved fixture HTML and always run.
"""

from __future__ import annotations

import pytest

from vaultmind_forge.l1.web_reader import (
    MIN_CONTENT_CHARS,
    Page,
    _clean,
    _RegionBuilder,
    fetch,
)

# A single body string reused across parser tests, long enough to clear
# MIN_CONTENT_CHARS so tests exercise selection rather than the length floor.
BODY = "Extracted documentation prose that stands in for a real article body. " * 12


def _build(html: str) -> str:
    builder = _RegionBuilder()
    builder.feed(html)
    builder.close()
    return builder.best_region()


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_prefers_the_article_over_a_longer_page_wrapper():
    """The real failure this module exists to prevent.

    A GitHub repo page wraps the README in a <main> that also contains the
    file listing. The wrapper is longer than the article, so ranking by length
    returns the file table instead of the README. Ranking must use semantic
    rank first.
    """
    filler = "".join(f"file-{i}.txt\n" for i in range(400))
    html = f"""
    <main>
      <div class="file-browser">{filler}</div>
      <article class="markdown-body entry-content">
        <h1>Real Documentation Heading</h1>
        <p>{'Actual prose content that an agent needs to read. ' * 40}</p>
      </article>
    </main>
    """
    result = _build(html)

    assert "Real Documentation Heading" in result
    assert "file-399.txt" not in result


def test_semantic_rank_beats_a_longer_bare_div():
    """A code block has no anchors, so density alone picks it over prose."""
    long_div = "bare wrapper text. " * 400
    html = f"""
    <div>{long_div}</div>
    <article>
      <p>{'The documentation body. ' * 30}</p>
    </article>
    """
    result = _build(html)

    assert "The documentation body." in result


def test_short_regions_are_rejected_regardless_of_quality():
    html = """
    <article><p>Too brief to be the article body.</p></article>
    """
    assert _build(html) == ""


def test_script_and_style_content_is_never_emitted():
    html = f"""
    <article>
      <script>var secret = "SHOULD_NOT_APPEAR";</script>
      <style>.x {{ color: SECRETSTYLE; }}</style>
      <p>{BODY}</p>
    </article>
    """
    result = _build(html)

    assert "Extracted documentation prose" in result
    assert "SHOULD_NOT_APPEAR" not in result
    assert "SECRETSTYLE" not in result


def test_void_elements_do_not_unbalance_the_skip_counter():
    """A regression guard for a real bug.

    Void elements never receive an end tag. Counting them toward the skip depth
    meant a single <img> or <path> inside a dropped subtree left the counter
    permanently above zero and silently discarded the entire rest of the page.
    """
    html = f"""
    <article>
      <p>Content before the images.</p>
      <img src="a.png"><br><hr>
      <p>{BODY}</p>
    </article>
    """
    result = _build(html)

    assert "Extracted documentation prose" in result


def test_unclosed_script_does_not_raise():
    html = f"""
    <article>
      <p>Before the script.</p>
      <script>var a = 1;
      <p>{BODY}</p>
    </article>
    """
    # An unterminated <script> legitimately swallows the remainder, so the only
    # guarantee here is that the parser terminates and returns text.
    assert isinstance(_build(html), str)


def test_malformed_markup_does_not_raise():
    html = "<article><p>text<div><span>unclosed"
    assert isinstance(_build(html), str)


def test_html_entities_are_decoded():
    html = "<article><p>&lt;tag&gt; &amp; &quot;quotes&quot; " + "body " * 80 + "</p></article>"
    result = _build(html)

    assert "&lt;tag&gt;" not in result
    assert "<tag>" in result
    assert "&amp;" not in result


def test_clean_strips_blank_runs_and_nav_lines():
    assert _clean("a\n\n\n\n\nb") == "a\n\nb"
    assert _clean("Sign in  Pricing") == ""
    assert _clean("Real content here") == "Real content here"


def test_clean_keeps_long_lines_starting_with_nav_words():
    """The nav filter is length-bounded so real prose survives."""
    long_line = "Sign in is required before you can use this documented feature path"
    assert _clean(long_line) == long_line


# ---------------------------------------------------------------------------
# fetch()
# ---------------------------------------------------------------------------


def test_rejects_non_http_urls():
    """No file:// or other scheme smuggling. Read-only over HTTP(S) only."""
    for bad in ("file:///C:/Windows/win.ini", "ftp://example.com/x", "notaurl"):
        with pytest.raises(ValueError):
            fetch(bad)


def test_page_reports_thin_extraction():
    assert Page("u", 200, "text/html", "x" * 10).is_thin
    assert not Page("u", 200, "text/html", "x" * (MIN_CONTENT_CHARS + 10)).is_thin





# ---------------------------------------------------------------------------
# Network (opt-in)
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_fetches_a_real_page_and_extracts_the_article():
    page = fetch("https://github.com/jamait/awesome-opencode-skills")

    assert page.status == 200
    assert page.rendered is True
    assert len(page.text) > 2000
    assert "Awesome OpenCode Skills" in page.text
    # The repo file listing is the thing this module exists to avoid.
    assert ".gitignore" not in page.text.split("\n")[0]


@pytest.mark.network
def test_network_failure_is_reported_not_raised():
    page = fetch("https://opencode.invalid/definitely-not-a-real-host-xyz")

    assert page.rendered is False
    assert page.warnings
