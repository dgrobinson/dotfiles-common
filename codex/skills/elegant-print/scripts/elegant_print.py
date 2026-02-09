#!/usr/bin/env python
import argparse
import base64
import csv
import json
import math
import re
import subprocess
import sys
from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path
from urllib.parse import unquote_to_bytes, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from pypdf import PdfReader, PdfWriter

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
}

REPLACEMENTS = {
    "\u00a0": " ",
    "\u2018": "`",
    "\u2019": "'",
    "\u201c": "``",
    "\u201d": "''",
    "\u2013": "--",
    "\u2014": "---",
    "\u2026": "...",
    "\u2212": "-",
    "\u02c8": "'",
    "\u02b2": "y",
    "\u0268": "y",
    "\u0411": "B",
    "\u0435": "e",
    "\u0441": "s",
    "\u044b": "y",
    "\u0463": "e",
}

LATEX_SPECIALS = {
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "&": r"\&",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

UNICODE_LATEX = {
    "é": r"\'e",
    "ê": r"\^e",
    "ï": r"\"i",
}

ALLOWED_COMMANDS = {"emph", "textbf", "textit", "textsc"}
CONTENT_TYPE_IMAGE_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
    "image/webp": ".webp",
}
LATEX_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}


def normalize_text(s: str) -> str:
    for k, v in REPLACEMENTS.items():
        s = s.replace(k, v)
    return s


def latex_escape_plain(s: str) -> str:
    s = normalize_text(s)
    out = []
    for ch in s:
        if ch in UNICODE_LATEX:
            out.append(UNICODE_LATEX[ch])
            continue
        out.append(LATEX_SPECIALS.get(ch, ch))
    return "".join(out)


def latex_escape_with_commands(s: str) -> str:
    s = normalize_text(s)
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "\\":
            m = re.match(r"\\([A-Za-z]+)", s[i:])
            if m:
                cmd = m.group(1)
                j = i + 1 + len(cmd)
                if cmd in ALLOWED_COMMANDS and j < n and s[j] == "{":
                    depth = 0
                    k = j
                    while k < n:
                        if s[k] == "{":
                            depth += 1
                        elif s[k] == "}":
                            depth -= 1
                            if depth == 0:
                                break
                        k += 1
                    if depth == 0 and k < n:
                        inner = s[j + 1 : k]
                        out.append("\\" + cmd + "{" + latex_escape_plain(inner) + "}")
                        i = k + 1
                        continue
            out.append(r"\textbackslash{}")
            i += 1
            continue
        out.append(LATEX_SPECIALS.get(ch, ch))
        i += 1
    return "".join(out)


def soup_with_fallback(html: str) -> BeautifulSoup:
    for parser in ("lxml", "html5lib", "html.parser"):
        try:
            return BeautifulSoup(html, parser)
        except Exception:
            continue
    return BeautifulSoup(html, "html.parser")


def escape_url_for_url(url: str) -> str:
    return url.replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")


def href_target(url: str) -> str:
    safe = normalize_text(url or "").strip()
    if safe:
        safe = safe.split("#", 1)[0]
        safe = requests.utils.requote_uri(safe)
    safe = safe.replace("{", "%7B").replace("}", "%7D")
    return r"\detokenize{" + safe + "}"


def collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def direct_tags(node: Tag) -> list[Tag]:
    return [child for child in node.children if isinstance(child, Tag)]


def badge_palette(label: str) -> tuple[str, str]:
    key = collapse_ws(label).lower()
    if "root" in key:
        return "RootBg", "RootFg"
    if "system" in key:
        return "SystemBg", "SystemFg"
    if "developer" in key:
        return "DeveloperBg", "DeveloperFg"
    if "user" in key:
        return "UserBg", "UserFg"
    if "guideline" in key:
        return "GuidelineBg", "GuidelineFg"
    return "NeutralBadgeBg", "NeutralBadgeFg"


def render_badge(label: str) -> str:
    bg, fg = badge_palette(label)
    return r"\modelbadge{" + bg + "}{" + fg + "}{" + latex_escape_plain(label) + "}"


def promote_authority_prefix(rendered: str, plain: str) -> str:
    if not rendered:
        return rendered

    head = collapse_ws(plain)
    for label in ("Root", "System", "Developer", "User", "Guideline"):
        if re.match(rf"^{label}\s*:", head, flags=re.IGNORECASE) is None:
            continue

        cleaned = re.sub(rf"^\\textbf\{{{label}\}}\s*:\s*", "", rendered)
        cleaned = re.sub(rf"^{label}\s*:\s*", "", cleaned)
        return render_badge(label) + " " + cleaned
    return rendered


def word_count(s: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", s or ""))


def quality_palette(kind: str) -> tuple[str, str]:
    if kind == "good":
        return "GoodBadgeBg", "GoodBadgeFg"
    if kind == "bad":
        return "BadBadgeBg", "BadBadgeFg"
    return "NeutralBadgeBg", "NeutralBadgeFg"


def render_quality_badge(label: str, kind: str) -> str:
    bg, fg = quality_palette(kind)
    return r"\modelbadge{" + bg + "}{" + fg + "}{" + latex_escape_plain(label) + "}"


def extract_heading(node: Tag) -> tuple[str, list[str]]:
    parsed = BeautifulSoup(str(node), "lxml")
    h_copy = parsed.find(node.name)
    if h_copy is None:
        text = collapse_ws(node.get_text(" ", strip=True))
        return latex_escape_plain(text), []

    badges: list[str] = []
    for badge_wrap in h_copy.find_all(class_="section-badges"):
        for child in direct_tags(badge_wrap):
            label = collapse_ws(child.get_text(" ", strip=True))
            if label:
                badges.append(label)
        badge_wrap.decompose()

    title = collapse_ws(h_copy.get_text(" ", strip=True))
    return latex_escape_plain(title), badges


def infer_web_title(soup: BeautifulSoup, url: str) -> tuple[str, str]:
    og_title_tag = soup.find("meta", attrs={"property": "og:title"})
    twitter_title_tag = soup.find("meta", attrs={"name": "twitter:title"})
    og_title = collapse_ws(og_title_tag.get("content", "")) if og_title_tag else ""
    twitter_title = collapse_ws(twitter_title_tag.get("content", "")) if twitter_title_tag else ""
    page_title = collapse_ws(soup.title.get_text(" ", strip=True)) if soup.title else ""
    main_node = extract_main(soup)
    h1 = main_node.find("h1") if main_node else soup.find("h1")
    h1_text = collapse_ws(h1.get_text(" ", strip=True)) if h1 else ""

    if "model-spec.openai.com" in url:
        version = ""
        m_url = re.search(r"/(20\d{2}-\d{2}-\d{2})", url)
        if m_url:
            version = m_url.group(1)
        elif page_title:
            m_title = re.search(r"(20\d{2})[/-](\d{2})[/-](\d{2})", page_title)
            if m_title:
                version = f"{m_title.group(1)}-{m_title.group(2)}-{m_title.group(3)}"
        subtitle = f"Version {version}" if version else ""
        return "Model Spec", subtitle

    if og_title:
        return og_title, ""
    if twitter_title:
        return twitter_title, ""
    if h1_text and h1_text.lower() != "overview":
        return h1_text, ""
    if page_title:
        page_title = re.sub(r"\s+-\s+by\s+.+$", "", page_title).strip()
        return page_title, ""
    return h1_text or "Untitled", ""


def parse_date_candidate(value: str) -> datetime | None:
    raw = collapse_ws(value)
    if not raw:
        return None

    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", raw)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    iso = raw
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        return None


def format_doc_date(dt: datetime) -> str:
    return f"{dt.strftime('%B')} {dt.day}, {dt.year}"


def iter_json_nodes(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from iter_json_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_json_nodes(item)


def infer_web_date(soup: BeautifulSoup, url: str) -> str:
    candidates: list[str] = []

    for attrs in (
        {"property": "article:published_time"},
        {"name": "article:published_time"},
        {"property": "og:published_time"},
        {"name": "publish_date"},
        {"itemprop": "datePublished"},
    ):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            candidates.append(tag.get("content"))

    for time_tag in soup.find_all("time"):
        if time_tag.get("datetime"):
            candidates.append(time_tag.get("datetime"))
        else:
            text = time_tag.get_text(" ", strip=True)
            if text:
                candidates.append(text)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        payload = (script.string or script.get_text() or "").strip()
        if not payload:
            continue
        try:
            parsed = json.loads(payload)
        except Exception:
            continue
        for obj in iter_json_nodes(parsed):
            for key in ("datePublished", "dateCreated", "dateModified", "uploadDate"):
                value = obj.get(key)
                if isinstance(value, str):
                    candidates.append(value)

    m_url = re.search(r"/(20\d{2})[-/](\d{2})[-/](\d{2})(?:/|$)", url)
    if m_url:
        candidates.append(f"{m_url.group(1)}-{m_url.group(2)}-{m_url.group(3)}")

    seen: set[str] = set()
    for candidate in candidates:
        key = collapse_ws(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        dt = parse_date_candidate(key)
        if dt is not None:
            return format_doc_date(dt)
    return ""


class Converter:
    def __init__(
        self,
        footnotes_by_id: dict[str, str],
        footnotes_by_number: dict[int, str],
        page_url: str = "",
    ):
        self.footnotes_by_id = footnotes_by_id
        self.footnotes_by_number = footnotes_by_number
        self.page_url = page_url

    def convert_inline(self, node) -> str:
        if isinstance(node, NavigableString):
            txt = str(node)
            if not txt.strip():
                return " "
            return latex_escape_plain(txt)
        if not isinstance(node, Tag):
            return ""

        name = node.name.lower()
        if name in ("style", "script", "meta", "link"):
            return ""
        if name in ("em", "i"):
            return r"\emph{" + self.convert_children(node) + "}"
        if name in ("strong", "b"):
            return r"\textbf{" + self.convert_children(node) + "}"
        if name in ("code", "kbd", "samp"):
            return r"\texttt{" + latex_escape_plain(node.get_text()) + "}"
        if name == "cite":
            return r"\textit{" + self.convert_children(node) + "}"
        if name == "span":
            cls = node.get("class") or []
            if "character-name" in cls:
                return r"\textsc{" + self.convert_children(node) + "}"
            if "footnote-ref" in cls:
                return self._footnote_from_text(node.get_text())
            if "IPA" in cls:
                return self.convert_children(node)
            return self.convert_children(node)
        if name == "sup":
            cls = node.get("class") or []
            if "reference" in cls:
                return self._footnote_from_ref(node)
            return self._footnote_from_text(node.get_text())
        if name == "a":
            return self._convert_link(node)
        if name == "br":
            return r"\\"
        if name == "img":
            return ""
        return self.convert_children(node)

    def convert_children(self, node) -> str:
        parts = [self.convert_inline(child) for child in node.children]
        return "".join([p for p in parts if p])

    def _footnote_from_ref(self, node: Tag) -> str:
        notes = []
        for a in node.find_all("a", href=True):
            href = a.get("href", "")
            rendered = self._footnote_from_href(href)
            if rendered:
                notes.append(rendered)
                continue
            label = a.get_text(strip=True).strip("[]")
            if label.isdigit() and int(label) in self.footnotes_by_number:
                notes.append(r"\footnote{" + self.footnotes_by_number[int(label)] + "}")
            elif label:
                notes.append(r"\textsuperscript{" + latex_escape_plain(label) + "}")
        return "".join(notes)

    def _footnote_from_text(self, text: str) -> str:
        m = re.search(r"(\d+)", text)
        if not m:
            return ""
        num = int(m.group(1))
        if num in self.footnotes_by_number:
            return r"\footnote{" + self.footnotes_by_number[num] + "}"
        return r"\textsuperscript{" + str(num) + "}"

    def _convert_link(self, node: Tag) -> str:
        href = node.get("href", "")
        text = self.convert_children(node)
        plain_text = collapse_ws(node.get_text(" ", strip=True))
        classes = {c.lower() for c in (node.get("class") or [])}
        if href.startswith("//"):
            href = "https:" + href

        if "footnote-anchor" in classes:
            note = self._footnote_from_href(href)
            if note:
                return note

        note = self._footnote_from_href(href)
        if note:
            return note

        if href.startswith("/wiki/") or href.startswith("#"):
            return text
        if href.startswith("/") or href.startswith("./") or href.startswith("../"):
            if self.page_url:
                return self._render_hyperlink(urljoin(self.page_url, href), text, plain_text)
            return text
        if href.startswith("http"):
            return self._render_hyperlink(href, text, plain_text)
        return text

    def _fragment_for_same_page(self, href: str) -> str:
        href = collapse_ws(href)
        if not href:
            return ""
        if href.startswith("#"):
            return href[1:]
        if not self.page_url:
            return ""

        base = urlparse(self.page_url)
        resolved = urlparse(urljoin(self.page_url, href))
        same_host = resolved.netloc == base.netloc
        same_path = (resolved.path or "/") == (base.path or "/")
        if same_host and same_path and resolved.fragment:
            return resolved.fragment
        return ""

    def _footnote_from_href(self, href: str) -> str:
        fragment = self._fragment_for_same_page(href)
        if not fragment:
            return ""

        if fragment in self.footnotes_by_id:
            return r"\footnote{" + self.footnotes_by_id[fragment] + "}"

        m = re.search(r"footnote(?:-anchor)?-(\d+)", fragment)
        if m:
            num = int(m.group(1))
            if num in self.footnotes_by_number:
                return r"\footnote{" + self.footnotes_by_number[num] + "}"
        return ""

    def _render_hyperlink(self, href: str, rendered_text: str, plain_text: str) -> str:
        href_arg = href_target(href)
        label = rendered_text.strip()
        plain_lower = plain_text.lower()
        if not label:
            label = latex_escape_plain(self._compact_link_label(href))
        elif plain_lower.startswith("http://") or plain_lower.startswith("https://") or plain_lower.startswith("www."):
            label = latex_escape_plain(self._compact_link_label(href))

        return (
            r"\href{"
            + href_arg
            + r"}{\textcolor{LinkColor}{"
            + label
            + r"\hspace{0.32em}\linkicon}}"
        )

    def _compact_link_label(self, href: str) -> str:
        parsed = urlparse(href)
        host = parsed.netloc.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        return host or "link"


def extract_main(soup: BeautifulSoup) -> Tag:
    for selector in ["main", "article", "#content", "#main", ".content", ".post", ".article"]:
        node = soup.select_one(selector)
        if node:
            return node
    body = soup.find("body")
    return body if body else soup


def build_wikipedia_footnotes(soup: BeautifulSoup) -> dict[str, str]:
    footnotes: dict[str, str] = {}
    converter = Converter({}, {})
    for li in soup.select("ol.references > li[id]"):
        ref_id = li.get("id")
        if not ref_id:
            continue
        li_copy = BeautifulSoup(str(li), "lxml").find("li") or li
        for el in li_copy.find_all(["style", "script"]):
            el.decompose()
        for el in li_copy.select(".mw-cite-backlink, .reference-accessdate, .mw-cite-backlink span"):
            el.decompose()
        text_node = li_copy.find("span", class_="reference-text") or li_copy
        raw = converter.convert_children(text_node).strip()
        raw = re.sub(r"^\[\d+\]\s*", "", raw).strip()
        raw = re.sub(r"\s+", " ", raw)
        if raw:
            footnotes[ref_id] = raw
    return footnotes


def build_numbered_footnotes(container: Tag, page_url: str) -> tuple[dict[int, str], dict[str, str]]:
    footnotes_by_number: dict[int, str] = {}
    footnotes_by_id: dict[str, str] = {}
    converter = Converter({}, {}, page_url=page_url)

    def register_ids(text: str, num: int, *ids: str) -> None:
        if not text:
            return
        if num:
            footnotes_by_id[f"footnote-{num}"] = text
            footnotes_by_id[f"footnote-anchor-{num}"] = text
        for item in ids:
            key = collapse_ws(item)
            if key:
                footnotes_by_id[key] = text

    for p in container.select("p.footnote"):
        p_copy = BeautifulSoup(str(p), "lxml").find("p")
        num = 0
        span = p_copy.find("span", class_="footnote-ref") if p_copy else None
        if span:
            m = re.search(r"(\d+)", span.get_text())
            if m:
                num = int(m.group(1))
            span.decompose()

        raw = converter.convert_children(p_copy).strip() if p_copy else ""
        if not raw:
            p.decompose()
            continue

        if not num:
            m = re.match(r"^\[(\d+)\]\s*(.*)", raw)
            if m:
                num = int(m.group(1))
                text = m.group(2).strip()
            else:
                text = raw
        else:
            text = re.sub(r"^\[(\d+)\]\s*", "", raw).strip()

        if num and text:
            footnotes_by_number[num] = text
            register_ids(text, num, p.get("id", ""))
        p.decompose()

    for div in container.select("div.footnote"):
        div_copy = BeautifulSoup(str(div), "lxml").find("div")
        if div_copy is None:
            div.decompose()
            continue

        num = 0
        explicit_ids: list[str] = []
        number_link = div_copy.select_one("a.footnote-number")
        if number_link:
            explicit_ids.append(number_link.get("id", ""))
            href = collapse_ws(number_link.get("href", ""))
            if href:
                frag = urlparse(urljoin(page_url, href)).fragment
                if frag:
                    explicit_ids.append(frag)
                m = re.search(r"footnote(?:-anchor)?-(\d+)", frag)
                if m:
                    num = int(m.group(1))
            if not num:
                m = re.search(r"(\d+)", number_link.get_text(" ", strip=True))
                if m:
                    num = int(m.group(1))
            number_link.decompose()

        content = div_copy.select_one(".footnote-content") or div_copy
        text = collapse_ws(converter.convert_children(content))
        if num and text:
            footnotes_by_number[num] = text
            register_ids(text, num, div.get("id", ""), *explicit_ids)
        div.decompose()

    return footnotes_by_number, footnotes_by_id


def clean_container(container: Tag) -> None:
    for tag in container.find_all(["script", "style", "noscript", "nav", "footer", "aside", "form"]):
        tag.decompose()


def parse_dimension(value: str | None) -> int:
    if value is None:
        return 0
    m = re.search(r"\d+", str(value))
    return int(m.group(0)) if m else 0


class ImageStore:
    def __init__(self, page_url: str, outdir: Path):
        self.page_url = page_url
        self.outdir = outdir
        self.assets_dir = outdir / "elegant-print-assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, str] = {}
        self.counter = 0

    def fetch(self, img: Tag) -> str | None:
        src = self._pick_source(img)
        if not src:
            return None
        if not self._should_include(img, src):
            return None

        resolved = self._resolve_source(src)
        if not resolved:
            return None

        if resolved in self.cache:
            return self.cache[resolved]

        data, content_type = self._download(resolved)
        if data is None:
            return None

        ext = self._infer_extension(resolved, content_type)
        if ext == ".webp":
            data, ext = self._convert_webp(data)
        if ext not in LATEX_IMAGE_EXTS:
            print(f"warning: skipping unsupported image format {ext} from {resolved}", file=sys.stderr)
            return None

        self.counter += 1
        filename = f"image-{self.counter:03d}{ext}"
        path = self.assets_dir / filename
        path.write_bytes(data)

        rel = path.relative_to(self.outdir).as_posix()
        self.cache[resolved] = rel
        return rel

    def _pick_source(self, img: Tag) -> str:
        for attr in ("src", "data-src", "data-lazy-src", "data-original"):
            value = collapse_ws(img.get(attr, ""))
            if value:
                return value

        srcset = collapse_ws(img.get("srcset", ""))
        if srcset:
            first = srcset.split(",", 1)[0].strip()
            return first.split(" ", 1)[0].strip()

        return ""

    def _resolve_source(self, src: str) -> str:
        if src.startswith("data:image/"):
            return src
        if src.startswith("//"):
            src = "https:" + src
        return urljoin(self.page_url, src)

    def _should_include(self, img: Tag, src: str) -> bool:
        cls = " ".join(img.get("class") or []).lower()
        if any(token in cls for token in ("avatar", "icon", "logo", "emoji")):
            return False

        lower_src = src.lower()
        if "avatar" in lower_src and "substack-post-media.s3.amazonaws.com" not in lower_src:
            return False

        w = parse_dimension(img.get("width"))
        h = parse_dimension(img.get("height"))
        if w and h and max(w, h) <= 80:
            return False

        return True

    def _download(self, resolved: str) -> tuple[bytes | None, str]:
        if resolved.startswith("data:image/"):
            try:
                header, payload = resolved.split(",", 1)
            except ValueError:
                return None, ""
            content_type = header.split(";", 1)[0].replace("data:", "", 1).lower()
            if ";base64" in header:
                try:
                    return base64.b64decode(payload), content_type
                except Exception:
                    return None, content_type
            return unquote_to_bytes(payload), content_type

        try:
            resp = requests.get(resolved, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            print(f"warning: failed to download image {resolved}: {exc}", file=sys.stderr)
            return None, ""

        content_type = resp.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        return resp.content, content_type

    def _infer_extension(self, resolved: str, content_type: str) -> str:
        if content_type in CONTENT_TYPE_IMAGE_EXT:
            return CONTENT_TYPE_IMAGE_EXT[content_type]
        if content_type.endswith("+xml") and "svg" in content_type:
            return ".svg"

        parsed = urlparse(resolved)
        suffix = Path(parsed.path).suffix.lower()
        if suffix in (".jpeg", ".jpg", ".png", ".pdf", ".webp", ".svg"):
            return suffix
        return ".jpg"

    def _convert_webp(self, data: bytes) -> tuple[bytes, str]:
        try:
            from PIL import Image
        except Exception:
            print("warning: PIL not available; skipping webp image", file=sys.stderr)
            return b"", ".skip"

        with TemporaryDirectory(prefix="elegant-print-webp-") as tmp:
            tmpdir = Path(tmp)
            src = tmpdir / "input.webp"
            dst = tmpdir / "output.png"
            src.write_bytes(data)
            try:
                with Image.open(src) as im:
                    im.save(dst, format="PNG")
            except Exception as exc:
                print(f"warning: failed to convert webp image: {exc}", file=sys.stderr)
                return b"", ".skip"
            return dst.read_bytes(), ".png"


def render_list(node: Tag, converter: Converter) -> str:
    env = "enumerate" if node.name == "ol" else "itemize"
    items: list[str] = []
    for li in node.find_all("li", recursive=False):
        if not isinstance(li, Tag):
            continue

        inline_parts: list[str] = []
        plain_parts: list[str] = []
        nested: list[Tag] = []

        for child in li.children:
            if isinstance(child, Tag) and child.name in ("ul", "ol"):
                nested.append(child)
                continue
            if isinstance(child, NavigableString):
                text = converter.convert_inline(child)
                inline_parts.append(text)
                plain_parts.append(str(child))
            elif isinstance(child, Tag):
                inline_parts.append(converter.convert_inline(child))
                plain_parts.append(child.get_text(" ", strip=False))

        item_text = collapse_ws("".join(inline_parts))
        plain_text = collapse_ws("".join(plain_parts))
        if item_text:
            item_text = promote_authority_prefix(item_text, plain_text)
            items.append(r"\item " + item_text)
        else:
            items.append(r"\item")

        for sub in nested:
            sub_tex = render_list(sub, converter).rstrip()
            if sub_tex:
                items.append(sub_tex)
    if not items:
        return ""
    return "\\begin{" + env + "}\n" + "\n".join(items) + "\n\\end{" + env + "}\n\n"


def render_admonition(node: Tag, converter: Converter) -> str:
    parsed = BeautifulSoup(str(node), "lxml")
    div = parsed.find("div")
    if div is None:
        return ""

    for icon in div.select(".admonition-icon"):
        icon.decompose()

    blocks: list[str] = []
    for child in direct_tags(div):
        if child.name == "p":
            text = collapse_ws(converter.convert_children(child))
            if text:
                blocks.append(text)
        elif child.name in ("ul", "ol"):
            list_tex = render_list(child, converter).strip()
            if list_tex:
                blocks.append(list_tex)

    if not blocks:
        text = collapse_ws(converter.convert_children(div))
        if text:
            blocks.append(text)

    if not blocks:
        return ""

    body = "\n\n".join(blocks)
    return "\\begin{modeladmonition}\n" + body + "\n\\end{modeladmonition}\n\n"


def message_role(wrapper: Tag) -> str:
    role_name = wrapper.select_one(".role-name")
    if role_name:
        role = collapse_ws(role_name.get_text(" ", strip=True))
        if role:
            return role

    classes = wrapper.get("class") or []
    for role in ("assistant", "user", "developer", "system", "tool"):
        if role in classes:
            return role.capitalize()
    return "Assistant"


def message_quality(wrapper: Tag) -> tuple[str, str]:
    quality = wrapper.select_one(".role-quality .quality")
    if quality is None:
        return "", ""

    label = collapse_ws(quality.get_text(" ", strip=True))
    classes = [c.lower() for c in (quality.get("class") or [])]
    classes.extend(c.lower() for c in (wrapper.get("class") or []))

    kind = ""
    if "good" in classes or "compliant" in label.lower():
        kind = "good"
    elif "bad" in classes or "violation" in label.lower():
        kind = "bad"
    return label, kind


def message_palette(role: str, kind: str) -> tuple[str, str]:
    if kind == "good":
        return "GoodBg", "GoodFrame"
    if kind == "bad":
        return "BadBg", "BadFrame"

    role_key = role.lower()
    if "developer" in role_key:
        return "DeveloperMsgBg", "DeveloperMsgFrame"
    if "system" in role_key:
        return "SystemMsgBg", "SystemMsgFrame"
    if "user" in role_key:
        return "UserMsgBg", "UserMsgFrame"
    if "tool" in role_key:
        return "ToolMsgBg", "ToolMsgFrame"
    return "AssistantMsgBg", "AssistantMsgFrame"


def render_message_body(wrapper: Tag, converter: Converter) -> str:
    inner = wrapper.select_one(".message .inner-content")
    if inner is None:
        inner = wrapper.select_one(".message")
    if inner is None:
        return ""

    paragraphs: list[str] = []
    direct = direct_tags(inner)
    if direct:
        for child in direct:
            if child.name == "p":
                text = collapse_ws(converter.convert_children(child))
                if text:
                    paragraphs.append(text)
            elif child.name == "pre":
                raw = child.get_text("\n", strip=True)
                if raw:
                    monospaced = latex_escape_plain(raw).replace("\n", r"\\ ")
                    paragraphs.append(r"\texttt{" + monospaced + "}")
            elif child.name in ("ul", "ol"):
                list_tex = render_list(child, converter).strip()
                if list_tex:
                    paragraphs.append(list_tex)
            else:
                text = collapse_ws(converter.convert_children(child))
                if text:
                    paragraphs.append(text)
    else:
        text = collapse_ws(converter.convert_children(inner))
        if text:
            paragraphs.append(text)

    if not paragraphs:
        raw = collapse_ws(inner.get_text(" ", strip=True))
        if raw:
            paragraphs.append(latex_escape_plain(raw))

    return "\n\n".join(paragraphs)


def render_message_box(wrapper: Tag, converter: Converter, compact: bool = False) -> str:
    role = message_role(wrapper)
    quality_label, quality_kind = message_quality(wrapper)
    bg, frame = message_palette(role, quality_kind)

    title = latex_escape_plain(role)
    if quality_label:
        title += r" \hfill " + render_quality_badge(quality_label, quality_kind)

    body = render_message_body(wrapper, converter)
    commentary = wrapper.select_one(".commentary")
    commentary_text = collapse_ws(converter.convert_children(commentary)) if commentary else ""

    options = [
        f"colback={bg}",
        f"colframe={frame}",
        "boxrule=0.55pt",
        "arc=2pt",
        "left=7pt",
        "right=7pt",
        "top=5pt",
        "bottom=5pt",
        "before skip=0.3em",
        "after skip=0.3em",
        "fonttitle=\\sffamily\\bfseries\\small",
        "fontupper=\\small",
        "title={" + title + "}",
    ]
    if not compact:
        options.append("breakable")

    chunks = ["\\begin{tcolorbox}[" + ",".join(options) + "]"]
    if body:
        chunks.append(body)
    if commentary_text:
        chunks.append("{\\small\\itshape\\color{Muted} " + commentary_text + "}")
    chunks.append("\\end{tcolorbox}")
    return "\n".join(chunks) + "\n"


def render_assistant_pair(wrappers: list[Tag], converter: Converter) -> str:
    if len(wrappers) != 2:
        return "".join(render_message_box(w, converter) for w in wrappers)

    left = render_message_box(wrappers[0], converter, compact=True).strip()
    right = render_message_box(wrappers[1], converter, compact=True).strip()
    return (
        "\\noindent\\begin{minipage}[t]{0.49\\linewidth}\n"
        + left
        + "\n\\end{minipage}\\hfill\n"
        + "\\begin{minipage}[t]{0.49\\linewidth}\n"
        + right
        + "\n\\end{minipage}\n\n"
    )


def render_conversation(node: Tag, converter: Converter) -> str:
    blocks: list[str] = []
    for child in direct_tags(node):
        classes = child.get("class") or []
        if "figure" in classes:
            figure_text = collapse_ws(converter.convert_children(child))
            if figure_text:
                blocks.append("\\begin{modelexampletitle}\n" + figure_text + "\n\\end{modelexampletitle}\n")
            continue

        if "message-wrapper" in classes:
            blocks.append(render_message_box(child, converter))
            continue

        if "wrap-assistant" in classes:
            wrappers = [tag for tag in direct_tags(child) if "message-wrapper" in (tag.get("class") or [])]
            if (
                len(wrappers) == 2
                and "assistant" in (wrappers[0].get("class") or [])
                and "assistant" in (wrappers[1].get("class") or [])
            ):
                blocks.append(render_assistant_pair(wrappers, converter))
            else:
                blocks.extend(render_message_box(w, converter) for w in wrappers)

    if not blocks:
        return ""

    return (
        "\\begin{modelaside}\n"
        + "\\begin{modelconversation}\n"
        + "".join(blocks)
        + "\\end{modelconversation}\n"
        + "\\end{modelaside}\n\n"
    )


def render_pre_block(node: Tag) -> str:
    raw = node.get_text("\n", strip=True)
    if not raw:
        return ""
    return "\\begin{modelcode}\n" + raw + "\n\\end{modelcode}\n\n"


def render_image_block(image_path: str, caption_tex: str) -> str:
    path_tex = escape_url_for_url(image_path)
    block = (
        "\\begin{center}\n"
        "\\includegraphics[width=0.96\\linewidth,keepaspectratio]{" + path_tex + "}\n"
        "\\end{center}\n"
    )
    if caption_tex:
        block += "\\begin{center}\\small\\itshape " + caption_tex + "\\end{center}\n"
    return block + "\n"


def render_image_tag(node: Tag, image_store: ImageStore, caption_tex: str = "") -> str:
    image_path = image_store.fetch(node)
    if not image_path:
        return ""

    final_caption = collapse_ws(caption_tex)
    if not final_caption:
        alt = collapse_ws(node.get("alt", ""))
        if alt and alt.lower() not in {"image", "photo"}:
            final_caption = latex_escape_plain(alt)

    return render_image_block(image_path, final_caption)


def render_blocks(
    container: Tag,
    converter: Converter,
    hybrid: bool = False,
    image_store: ImageStore | None = None,
) -> list[str]:
    parts: list[str] = []
    flow_parts: list[str] = []
    flow_words = 0
    flow_blocks = 0
    handled_images: set[int] = set()

    def push_flow(tex: str, words: int) -> None:
        nonlocal flow_words, flow_blocks
        if not tex:
            return
        flow_parts.append(tex)
        flow_words += words
        flow_blocks += 1

    def flush_flow() -> None:
        nonlocal flow_words, flow_blocks
        if not flow_parts:
            return
        chunk = "".join(flow_parts)
        # Hybrid mode keeps headings/examples full width while packing long prose clusters.
        if hybrid and ((flow_blocks >= 2 and flow_words >= 110) or flow_words >= 180):
            parts.append("\\begin{hybridcols}\n" + chunk + "\\end{hybridcols}\n\n")
        else:
            parts.append(chunk)
        flow_parts.clear()
        flow_words = 0
        flow_blocks = 0

    for node in container.descendants:
        if not isinstance(node, Tag):
            continue

        classes = node.get("class") or []

        # Preserve semantically rich Model Spec blocks as dedicated print components.
        if "conversation" in classes:
            if node.find_parent("div", class_="conversation") is not None:
                continue
            flush_flow()
            conv = render_conversation(node, converter)
            if conv:
                parts.append(conv)
            continue

        if "admonition" in classes and "admonition-content" in classes:
            if node.find_parent("div", class_="admonition-content") is not None:
                continue
            flush_flow()
            admonition = render_admonition(node, converter)
            if admonition:
                parts.append(admonition)
            continue

        if node.find_parent("div", class_="conversation") is not None:
            continue
        if node.find_parent("div", class_="admonition-content") is not None:
            continue

        if node.name in ("h1", "h2", "h3", "h4"):
            flush_flow()
            text, badges = extract_heading(node)
            if not text:
                continue
            if text.startswith("Footnotes for Part"):
                continue
            level = {"h1": "section", "h2": "section", "h3": "subsection", "h4": "subsubsection"}.get(node.name)
            parts.append("\\" + level + "*{" + text + "}\\addcontentsline{toc}{" + level + "}{" + text + "}")
            if badges:
                badges_tex = " ".join(render_badge(label) for label in badges)
                parts.append("\n\\noindent\\hfill " + badges_tex + "\\par\\vspace{0.35em}\n")
            else:
                parts.append("\n")
        elif node.name == "figure":
            if image_store is None:
                continue
            if node.find_parent("figure") is not None:
                continue
            flush_flow()
            images = [img for img in node.find_all("img")]
            caption_node = node.find("figcaption")
            caption_tex = collapse_ws(converter.convert_children(caption_node)) if caption_node else ""
            emitted = False
            for idx, img in enumerate(images):
                img_tex = render_image_tag(
                    img,
                    image_store,
                    caption_tex if idx == len(images) - 1 else "",
                )
                if img_tex:
                    parts.append(img_tex)
                    handled_images.add(id(img))
                    emitted = True
            if emitted:
                continue
        elif node.name == "p":
            if node.find_parent(["blockquote", "li", "table", "figure"]):
                continue
            if "footnote" in (node.get("class") or []):
                continue
            text = converter.convert_children(node).strip()
            if text:
                push_flow(text + "\n\n", word_count(node.get_text(" ", strip=True)))
        elif node.name == "img":
            if image_store is None:
                continue
            if id(node) in handled_images:
                continue
            if node.find_parent("figure") is not None:
                continue
            flush_flow()
            img_tex = render_image_tag(node, image_store)
            if img_tex:
                parts.append(img_tex)
                handled_images.add(id(node))
        elif node.name == "div" and "figure" in classes:
            flush_flow()
            figure_text = collapse_ws(converter.convert_children(node))
            if figure_text:
                parts.append("\\begin{modelexampletitle}\n" + figure_text + "\n\\end{modelexampletitle}\n\n")
        elif node.name == "pre":
            if node.find_parent(["pre", "code"]) is not None:
                continue
            flush_flow()
            code_block = render_pre_block(node)
            if code_block:
                parts.append(code_block)
        elif node.name in ("ul", "ol"):
            if node.find_parent(["ul", "ol"]):
                continue
            list_tex = render_list(node, converter)
            if list_tex:
                push_flow(list_tex, word_count(node.get_text(" ", strip=True)))
        elif node.name == "blockquote":
            if node.find_parent("blockquote") is not None:
                continue
            quote = converter.convert_children(node).strip()
            if quote:
                push_flow("\\begin{quote}\n" + quote + "\n\\end{quote}\n\n", word_count(node.get_text(" ", strip=True)))
        elif node.name == "cite":
            if node.find_parent(["p", "blockquote", "li"]) is not None:
                continue
            cite = converter.convert_children(node).strip()
            if cite:
                push_flow("\\begin{flushright}\n" + cite + "\n\\end{flushright}\n\n", word_count(node.get_text(" ", strip=True)))
        elif node.name == "figcaption":
            if node.find_parent(["figure", "table"]) is None:
                continue
            if node.find_parent("figure") is not None:
                continue
            flush_flow()
            caption = converter.convert_children(node).strip()
            if caption:
                parts.append("\\begin{center}\\small " + caption + "\\end{center}\n\n")
        elif node.name == "hr":
            flush_flow()
            parts.append("\\vspace{0.8em}\\hrule\\vspace{0.8em}\n\n")

    flush_flow()
    return parts


def latex_preamble(title: str, subtitle: str, footer: str, columns: int, paper: str, hybrid: bool = False) -> str:
    if paper == "7x10":
        geometry = "paperwidth=7in,paperheight=10in,top=0.9in,bottom=1.0in,inner=1.0in,outer=1.6in,includeheadfoot"
        doc_opts = "11pt,twoside"
        conversation_inset = "0.68in"
    else:
        geometry = "letterpaper,top=1.1in,bottom=1.2in,inner=1.2in,outer=2.0in,includeheadfoot"
        doc_opts = "11pt,letterpaper,twoside"
        conversation_inset = "0.92in"

    use_multicol = columns == 2 or hybrid
    multicol_pkg = "\\usepackage{multicol}\n" if use_multicol else ""
    multicol_begin = "\\begin{multicols}{2}\n" if columns == 2 and not hybrid else ""
    multicol_end = "\\end{multicols}\n" if columns == 2 and not hybrid else ""

    subtitle_block = f"{{\\Large\\itshape {subtitle}}}\\\\[0.8em]" if subtitle else ""
    footer_block = f"{{\\large\\color{{Muted}} {footer}}}" if footer else ""

    preamble = f"""
\\documentclass[{doc_opts}]{{article}}
\\usepackage[{geometry}]{{geometry}}
\\usepackage{{microtype}}
\\usepackage{{xcolor}}
\\usepackage{{titlesec}}
\\usepackage{{fancyhdr}}
\\usepackage{{lastpage}}
\\usepackage{{setspace}}
\\usepackage{{enumitem}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{tgschola}}
\\usepackage{{tgheros}}
\\usepackage[english]{{babel}}
\\usepackage{{url}}
\\usepackage{{xurl}}
\\usepackage{{graphicx}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage[bottom,hang,flushmargin]{{footmisc}}
\\usepackage[most]{{tcolorbox}}
\\usepackage{{changepage}}
{multicol_pkg}

\\definecolor{{Accent}}{{HTML}}{{7A3B2E}}
\\definecolor{{LinkColor}}{{HTML}}{{245B93}}
\\definecolor{{Muted}}{{HTML}}{{6B6B6B}}
\\definecolor{{PageGray}}{{gray}}{{0.6}}
\\definecolor{{InfoBg}}{{HTML}}{{EAF1FF}}
\\definecolor{{InfoBorder}}{{HTML}}{{C6D5F5}}
\\definecolor{{ConversationBg}}{{HTML}}{{F6F7F9}}
\\definecolor{{ConversationBorder}}{{HTML}}{{D9DEE6}}
\\definecolor{{CodeBg}}{{HTML}}{{F7F8FB}}
\\definecolor{{CodeFrame}}{{HTML}}{{D9DCE5}}

\\definecolor{{RootBg}}{{HTML}}{{FDECEC}}
\\definecolor{{RootFg}}{{HTML}}{{8F1F20}}
\\definecolor{{SystemBg}}{{HTML}}{{EAF2FF}}
\\definecolor{{SystemFg}}{{HTML}}{{1D4E89}}
\\definecolor{{DeveloperBg}}{{HTML}}{{FFF2DE}}
\\definecolor{{DeveloperFg}}{{HTML}}{{8A4B00}}
\\definecolor{{UserBg}}{{HTML}}{{EAF8F2}}
\\definecolor{{UserFg}}{{HTML}}{{22633E}}
\\definecolor{{GuidelineBg}}{{HTML}}{{ECECF1}}
\\definecolor{{GuidelineFg}}{{HTML}}{{4A4B5A}}
\\definecolor{{NeutralBadgeBg}}{{HTML}}{{EFF0F3}}
\\definecolor{{NeutralBadgeFg}}{{HTML}}{{545763}}

\\definecolor{{AssistantMsgBg}}{{HTML}}{{F5F7FA}}
\\definecolor{{AssistantMsgFrame}}{{HTML}}{{D5DDE9}}
\\definecolor{{UserMsgBg}}{{HTML}}{{F2F6FF}}
\\definecolor{{UserMsgFrame}}{{HTML}}{{CEDBF2}}
\\definecolor{{DeveloperMsgBg}}{{HTML}}{{FFF6E9}}
\\definecolor{{DeveloperMsgFrame}}{{HTML}}{{EFD4A7}}
\\definecolor{{SystemMsgBg}}{{HTML}}{{EEF9F3}}
\\definecolor{{SystemMsgFrame}}{{HTML}}{{C5E3D2}}
\\definecolor{{ToolMsgBg}}{{HTML}}{{F3F3F6}}
\\definecolor{{ToolMsgFrame}}{{HTML}}{{D8D8DE}}
\\definecolor{{GoodBg}}{{HTML}}{{EEF8EA}}
\\definecolor{{GoodFrame}}{{HTML}}{{BFDDB5}}
\\definecolor{{BadBg}}{{HTML}}{{FBECEC}}
\\definecolor{{BadFrame}}{{HTML}}{{E8B9B9}}
\\definecolor{{GoodBadgeBg}}{{HTML}}{{E5F5E5}}
\\definecolor{{GoodBadgeFg}}{{HTML}}{{256B35}}
\\definecolor{{BadBadgeBg}}{{HTML}}{{FBE5E5}}
\\definecolor{{BadBadgeFg}}{{HTML}}{{922F33}}

\\hypersetup{{
  pdftitle={{{title}}}
}}

\\IfFileExists{{fontawesome5.sty}}{{%
  \\usepackage{{fontawesome5}}%
  \\newcommand{{\\linkicon}}{{\\raisebox{{0.04em}}{{\\scalebox{{0.72}}{{\\faExternalLink*}}}}}}%
}}{{%
  \\newcommand{{\\linkicon}}{{\\raisebox{{0.05em}}{{\\scalebox{{0.72}}{{$\\nearrow$}}}}}}%
}}

\\newcommand{{\\modelbadge}}[3]{{%
  \\begingroup
  \\setlength{{\\fboxsep}}{{3.5pt}}%
  \\colorbox{{#1}}{{\\textcolor{{#2}}{{\\sffamily\\bfseries\\scriptsize #3}}}}%
  \\endgroup
}}

\\newtcolorbox{{modeladmonition}}{{%
  colback=InfoBg,
  colframe=InfoBorder,
  boxrule=0.6pt,
  arc=2.5pt,
  left=9pt,right=9pt,top=7pt,bottom=7pt,
  before skip=0.6em,
  after skip=0.8em,
  breakable
}}

\\newtcolorbox{{modelconversation}}{{%
  colback=ConversationBg,
  colframe=ConversationBorder,
  boxrule=0.45pt,
  arc=2pt,
  left=8pt,right=8pt,top=6pt,bottom=6pt,
  before skip=0.55em,
  after skip=0.65em,
  breakable
}}

\\newenvironment{{modelaside}}{{%
  \\par\\smallskip
  \\ifodd\\value{{page}}\\begin{{adjustwidth}}{{0pt}}{{-{conversation_inset}}}\\else\\begin{{adjustwidth}}{{-{conversation_inset}}}{{0pt}}\\fi
  \\small
}}{{%
  \\end{{adjustwidth}}
  \\par\\smallskip
}}

\\newenvironment{{hybridcols}}{{%
  \\begin{{multicols}}{{2}}
  \\setlength{{\\columnsep}}{{1.2em}}
  \\raggedcolumns
}}{{%
  \\end{{multicols}}
}}

\\newtcolorbox{{modelexampletitle}}{{%
  colback=white,
  colframe=ConversationBorder,
  boxrule=0.4pt,
  arc=2pt,
  left=7pt,right=7pt,top=5pt,bottom=5pt,
  before skip=0.4em,
  after skip=0.5em,
  fontupper=\\small\\itshape
}}

\\newtcblisting{{modelcode}}{{%
  colback=CodeBg,
  colframe=CodeFrame,
  boxrule=0.45pt,
  arc=2pt,
  left=6pt,right=6pt,top=5pt,bottom=5pt,
  before skip=0.55em,
  after skip=0.75em,
  listing only,
  breakable,
  listing options={{basicstyle=\\ttfamily\\small,columns=fullflexible,keepspaces=true,showstringspaces=false,breaklines=true}}
}}

\\setstretch{{1.12}}
\\raggedbottom
\\setlength{{\\emergencystretch}}{{3em}}
\\setlength{{\\parindent}}{{1.1em}}
\\setlength{{\\parskip}}{{0pt}}
\\setlength{{\\footnotesep}}{{0.7em}}
\\interfootnotelinepenalty=10000

\\titleformat{{\\section}}
  {{\\sffamily\\bfseries\\Large\\color{{Accent}}}}
  {{}}%
  {{0pt}}
  {{\\Large}}

\\titleformat{{\\subsection}}
  {{\\sffamily\\bfseries\\color{{Accent}}}}
  {{}}%
  {{0pt}}
  {{}}

\\titleformat{{\\subsubsection}}
  {{\\sffamily\\itshape\\color{{Accent}}}}
  {{}}%
  {{0pt}}
  {{}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyfoot[LE,RO]{{\\thepage\\textcolor{{PageGray}}{{ / \\pageref{{LastPage}}}}}}
\\renewcommand{{\\headrulewidth}}{{0pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}
\\fancypagestyle{{plain}}{{%
  \\fancyhf{{}}%
  \\fancyfoot[LE,RO]{{\\thepage\\textcolor{{PageGray}}{{ / \\pageref{{LastPage}}}}}}%
  \\renewcommand{{\\headrulewidth}}{{0pt}}%
}}

\\setlist[itemize]{{leftmargin=1.5em}}
\\setlist[description]{{leftmargin=1.8em, labelsep=0.6em}}

\\begin{{document}}
\\thispagestyle{{plain}}

\\begin{{center}}
{{\\LARGE\\scshape {title} }}\\\\[0.45em]
{subtitle_block}{footer_block}
\\end{{center}}
\\vspace{{0.7em}}

\\tableofcontents
\\newpage

{multicol_begin}
"""

    return preamble, multicol_end


def build_web_tex(url: str, columns: int, paper: str, outdir: Path, hybrid: bool = False) -> tuple[str, str]:
    html = requests.get(url, headers=HEADERS, timeout=30).text
    soup = soup_with_fallback(html)

    title_text, subtitle_text = infer_web_title(soup, url)
    doc_date = infer_web_date(soup, url)
    if doc_date:
        date_label = f"Published {doc_date}"
        if subtitle_text:
            if date_label not in subtitle_text:
                subtitle_text = f"{subtitle_text} | {date_label}"
        else:
            subtitle_text = date_label

    footnotes_by_id: dict[str, str] = {}
    footnotes_by_number: dict[int, str] = {}

    if "wikipedia.org" in url:
        footnotes_by_id = build_wikipedia_footnotes(soup)
        content = soup.select_one("div.mw-parser-output") or extract_main(soup)
    else:
        content = extract_main(soup)

    clean_container(content)
    footnotes_by_number, extra_footnote_ids = build_numbered_footnotes(content, url)
    footnotes_by_id.update(extra_footnote_ids)

    converter = Converter(footnotes_by_id, footnotes_by_number, page_url=url)
    image_store = ImageStore(url, outdir)

    body_parts = render_blocks(content, converter, hybrid=hybrid, image_store=image_store)

    title_text = latex_escape_plain(title_text)
    if " (" not in title_text and "(" in title_text:
        title_text = title_text.replace("(", " (", 1)
    subtitle_text = latex_escape_plain(subtitle_text)
    host = urlparse(url).netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    footer = latex_escape_plain(f"Source: {host}") if host else ""

    preamble, closing = latex_preamble(title_text, subtitle_text, footer, columns, paper, hybrid=hybrid)
    body = "".join(body_parts)
    tex = preamble + body + "\n" + closing + "\\end{document}\n"
    return tex, title_text


def format_paragraphs(text: str) -> str:
    text = normalize_text(text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    escaped_parts = []
    for p in parts:
        p = re.sub(r"\s+", " ", p.strip())
        escaped_parts.append(latex_escape_with_commands(p))
    return "\n\n".join(escaped_parts)


def build_csv_tex(csv_path: Path, columns: int, paper: str) -> str:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if any((v or "").strip() for v in row.values())]

    title = latex_escape_plain("CSLAW 2026 Data")
    subtitle = latex_escape_plain(csv_path.name)
    footer = latex_escape_plain("Generated for print")

    preamble, closing = latex_preamble(title, subtitle, footer, columns, paper)

    blocks = []
    for row in rows:
        entry_id = (row.get("ID") or "").strip()
        paper_title = (row.get("Title") or "").strip()
        authors = (row.get("Authors") or "").strip()
        abstract = (row.get("Abstract") or "").strip()

        parts = []
        if entry_id:
            parts.append(r"\noindent\textsc{ID " + latex_escape_plain(entry_id) + "}")
        if paper_title:
            parts.append(r"\noindent\textbf{" + latex_escape_with_commands(paper_title) + "}")
        if authors:
            parts.append(r"\noindent\textit{" + latex_escape_with_commands(authors) + "}")
        if abstract:
            parts.append(format_paragraphs(abstract))
        block = "\n".join(parts)
        if block.strip():
            blocks.append(block)

    body = "\n\\vspace{0.8em}\\hrule\\vspace{0.9em}\n\n".join(blocks)
    tex = preamble + body + "\n" + closing + "\\end{document}\n"
    return tex


def write_and_compile(tex: str, outdir: Path, basename: str, open_pdf: bool) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    tex_path = outdir / f"{basename}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    subprocess.run(["tectonic", "-X", "compile", str(tex_path), "--outdir", str(outdir)], check=True)
    pdf_path = outdir / f"{basename}.pdf"
    if open_pdf:
        subprocess.run(["open", str(pdf_path)], check=False)
    return pdf_path


def booklet_cover_tex(
    title: str,
    booklet_idx: int,
    booklet_total: int,
    content_start: int,
    content_end: int,
    paper: str,
) -> str:
    if paper == "7x10":
        geometry = "paperwidth=7in,paperheight=10in,top=1.0in,bottom=1.0in,left=0.9in,right=0.9in"
    else:
        geometry = "letterpaper,top=1.1in,bottom=1.1in,left=1.0in,right=1.0in"

    title = latex_escape_plain(title)
    range_text = latex_escape_plain(f"Content pages {content_start}-{content_end}")

    return f"""
\\documentclass[11pt]{{article}}
\\usepackage[{geometry}]{{geometry}}
\\usepackage{{xcolor}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{tgschola}}
\\usepackage{{tgheros}}
\\pagestyle{{empty}}

\\definecolor{{Accent}}{{HTML}}{{7A3B2E}}
\\definecolor{{Muted}}{{HTML}}{{6B6B6B}}
\\definecolor{{Rule}}{{HTML}}{{D7DCE6}}

\\begin{{document}}
\\vspace*{{\\fill}}
\\begin{{center}}
{{\\Huge\\sffamily\\bfseries\\color{{Accent}} {title}}}\\\\[1.1em]
{{\\Large\\sffamily Booklet {booklet_idx} of {booklet_total}}}\\\\[0.55em]
{{\\normalsize\\sffamily\\color{{Muted}} {range_text}}}\\\\[2.2em]
{{\\color{{Rule}}\\rule{{0.62\\linewidth}}{{0.7pt}}}}\\\\[1.0em]
{{\\small\\sffamily\\color{{Muted}} Staple this booklet separately}}
\\end{{center}}
\\vspace*{{\\fill}}
\\end{{document}}
"""


def write_stapled_sections(
    pdf_path: Path,
    outdir: Path,
    basename: str,
    paper: str,
    section_max_pages: int,
    title: str,
) -> list[Path]:
    if section_max_pages < 2:
        raise ValueError("section_max_pages must be at least 2 to include a cover page.")

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    content_pages_per_section = max(1, section_max_pages - 1)
    section_total = max(1, math.ceil(total_pages / content_pages_per_section))
    outputs: list[Path] = []

    with TemporaryDirectory(prefix="elegant-print-covers-") as tmp:
        tmpdir = Path(tmp)
        for i in range(section_total):
            start = i * content_pages_per_section
            end = min((i + 1) * content_pages_per_section, total_pages)

            cover_tex = booklet_cover_tex(
                title=title,
                booklet_idx=i + 1,
                booklet_total=section_total,
                content_start=start + 1,
                content_end=end,
                paper=paper,
            )
            cover_tex_path = tmpdir / f"cover-{i + 1:02d}.tex"
            cover_tex_path.write_text(cover_tex, encoding="utf-8")
            subprocess.run(["tectonic", "-X", "compile", str(cover_tex_path), "--outdir", str(tmpdir)], check=True)
            cover_pdf_path = tmpdir / f"cover-{i + 1:02d}.pdf"

            cover_reader = PdfReader(str(cover_pdf_path))
            writer = PdfWriter()
            writer.add_page(cover_reader.pages[0])

            for page_idx in range(start, end):
                writer.add_page(reader.pages[page_idx])

            section_path = outdir / f"{basename}-section-{i + 1:02d}-of-{section_total:02d}.pdf"
            with section_path.open("wb") as f:
                writer.write(f)
            outputs.append(section_path)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate elegant print-ready PDFs from web pages or CSVs.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    web = sub.add_parser("web", help="Render a web page to a print-ready PDF")
    web.add_argument("url", help="URL to render")
    web.add_argument("--outdir", default=".", help="Output directory")
    web.add_argument("--columns", type=int, choices=[1, 2], default=1, help="Column count")
    web.add_argument("--paper", choices=["letter", "7x10"], default="letter", help="Paper size")
    web.add_argument(
        "--hybrid",
        action="store_true",
        help="Keep rich examples full width while packing long prose into selective two-column blocks",
    )
    web.add_argument(
        "--section-max-pages",
        type=int,
        default=0,
        help="If set, also emit stapled booklet PDFs with cover pages and at most N pages each",
    )
    web.add_argument(
        "--section-title",
        default="",
        help="Optional title override used on booklet cover pages",
    )
    web.add_argument("--open", action="store_true", help="Open PDF after render")

    csvp = sub.add_parser("csv", help="Render a CSV to a print-ready PDF")
    csvp.add_argument("csv_path", help="Path to CSV")
    csvp.add_argument("--outdir", default=".", help="Output directory")
    csvp.add_argument("--columns", type=int, choices=[1, 2], default=1, help="Column count")
    csvp.add_argument("--paper", choices=["letter", "7x10"], default="letter", help="Paper size")
    csvp.add_argument("--open", action="store_true", help="Open PDF after render")

    args = parser.parse_args()
    outdir = Path(args.outdir).expanduser().resolve()

    if args.cmd == "web":
        columns = args.columns
        if args.hybrid and columns == 2:
            # Hybrid mode is one-column base layout with selective two-column prose clusters.
            columns = 1
        tex, doc_title = build_web_tex(args.url, columns, args.paper, outdir, hybrid=args.hybrid)
        pdf = write_and_compile(tex, outdir, "elegant-print", args.open)
        print(f"Wrote {pdf}")
        if args.section_max_pages:
            section_title = args.section_title.strip() or doc_title
            sections = write_stapled_sections(
                pdf_path=pdf,
                outdir=outdir,
                basename="elegant-print",
                paper=args.paper,
                section_max_pages=args.section_max_pages,
                title=section_title,
            )
            print(f"Wrote {len(sections)} stapled sections:")
            for p in sections:
                print(f" - {p}")
    elif args.cmd == "csv":
        csv_path = Path(args.csv_path).expanduser().resolve()
        tex = build_csv_tex(csv_path, args.columns, args.paper)
        pdf = write_and_compile(tex, outdir, "elegant-print", args.open)
        print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()
