"""
Einfacher, echter Webcrawler, der das exakte Datenformat erzeugt,
das src/loaders/website_loader.py erwartet:

<website_dir>/pages/<n>/
    raw.html            -> gespeicherter HTML-Quelltext
    screenshot.png      -> gerenderter Screenshot (Playwright, optional)
    links.json          -> Liste von {"href": ..., "text": ...}
    forms.json          -> Liste von {"action": ..., "method": ..., "fields": n}
    media.json          -> Liste von {"type": "img"/"video"/..., "src": ...}
    visible_text.json   -> {"url": ..., "text": "..."}
    dom.json            -> {"tag": "html", "children": [...]}  (rekursiv)
<website_dir>/
    portal_meta.json    -> Start-URL, Seitenzahl
    asset_index.json    -> Asset-URL -> Typ, referenzierende Seiten, Shared-Flag
    shared_assets/      -> Downloads der Assets, die mehrere Seiten nutzen

Nutzung:
    python3 mini_crawler.py <start_url> <output_dir> [max_pages] [--no-screenshots] [--no-asset-download]

Crawlt nur Seiten innerhalb derselben Domain, respektiert robots.txt (Disallow),
Screenshots via Playwright/Chromium (fallback: ohne Screenshots, wenn Playwright
nicht installiert ist).
"""
import sys
import json
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit, parse_qsl, urlencode
import requests
from bs4 import BeautifulSoup

MAX_ASSET_DOWNLOADS = 20      # Obergrenze für shared_assets/-Downloads
MAX_ASSET_BYTES = 5 * 1024 * 1024  # 5 MB pro Asset


def normalize_url(url):
    """Kanonische Form für De-duplizierung: Fragment entfernt, Query-
    Parameter sortiert (a=1&b=2 == b=2&a=1), leerer Pfad → '/'."""
    parts = urlsplit(url)
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, query, ""))


def same_domain(url, root_domain):
    try:
        return urlparse(url).netloc == root_domain
    except Exception:
        return False


def load_robots_disallow(root_url, headers):
    """Minimal robots.txt parser: returns list of Disallow path prefixes for User-agent: *."""
    disallow = []
    try:
        r = requests.get(urljoin(root_url, "/robots.txt"), headers=headers, timeout=10)
        if r.status_code != 200:
            return disallow
        applies = False
        for line in r.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                applies = (agent == "*")
            elif applies and line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallow.append(path)
    except Exception:
        pass
    return disallow


def is_disallowed(url, disallow_prefixes):
    path = urlparse(url).path or "/"
    return any(path.startswith(p) for p in disallow_prefixes)


def build_dom_tree(node, depth=0, max_depth=60):
    """Rekursiv: bs4-Tag -> {"tag": ..., "children": [...]}, wie von
    src/feature_engineering/web_features.py._dom_depth/_dom_node_count erwartet."""
    if depth > max_depth:
        return {"tag": str(getattr(node, "name", "text")), "children": []}
    children = []
    for child in getattr(node, "children", []):
        if getattr(child, "name", None):  # nur echte Tags, keine reinen Text-Nodes
            children.append(build_dom_tree(child, depth + 1, max_depth))
    return {"tag": node.name, "children": children}


def extract_links(soup, base_url):
    out = []
    for a in soup.find_all("a", href=True):
        out.append({"href": urljoin(base_url, a["href"]), "text": a.get_text(strip=True)[:200]})
    return out


def extract_forms(soup):
    out = []
    for form in soup.find_all("form"):
        out.append({
            "action": form.get("action", ""),
            "method": form.get("method", "get"),
            "fields": len(form.find_all(["input", "select", "textarea"])),
        })
    return out


def extract_media(soup, base_url):
    out = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            out.append({"type": "img", "src": urljoin(base_url, src)})
    for tag in soup.find_all(["video", "audio"]):
        src = tag.get("src")
        if src:
            out.append({"type": tag.name, "src": urljoin(base_url, src)})
        for source in tag.find_all("source", src=True):
            out.append({"type": tag.name, "src": urljoin(base_url, source["src"])})
    return out


def extract_asset_urls(soup, base_url):
    """Alle Asset-Referenzen einer Seite: Medien, Stylesheets, Skripte, Icons."""
    urls = []
    for m in extract_media(soup, base_url):
        urls.append((m["type"], m["src"]))
    for link in soup.find_all("link", href=True):
        rel = (link.get("rel") or [])
        if "stylesheet" in rel or "icon" in rel:
            urls.append(("icon" if "icon" in rel else "stylesheet", urljoin(base_url, link["href"])))
    for script in soup.find_all("script", src=True):
        urls.append(("script", urljoin(base_url, script["src"])))
    return urls


def build_asset_index(asset_refs, page_numbers):
    """
    asset_refs: {url: {"type": str, "pages": set[int]}} (mutiert während des Crawls)
    page_numbers: Mapping page_num -> url (für die Seitenliste im Index)
    """
    entries = {}
    for url, info in sorted(asset_refs.items()):
        entries[url] = {
            "type": info["type"],
            "pages": sorted(info["pages"]),
            "shared": len(info["pages"]) >= 2,
        }
    return {
        "n_pages": len(page_numbers),
        "n_assets": len(entries),
        "n_shared": sum(1 for e in entries.values() if e["shared"]),
        "assets": entries,
    }


def download_shared_assets(asset_index, out_dir, headers):
    """Lädt Assets, die von >= 2 Seiten referenziert werden, nach shared_assets/.
    Gibt das Mapping url -> lokaler Pfad zurück (nur erfolgreiche Downloads)."""
    shared_dir = Path(out_dir) / "shared_assets"
    shared_dir.mkdir(parents=True, exist_ok=True)
    local_paths = {}
    downloaded = 0
    for url, entry in asset_index["assets"].items():
        if not entry["shared"] or downloaded >= MAX_ASSET_DOWNLOADS:
            if downloaded >= MAX_ASSET_DOWNLOADS:
                print(f"  … weitere Shared-Assets übersprungen (Limit {MAX_ASSET_DOWNLOADS})")
                break
            continue
        try:
            suffix = Path(urlparse(url).path).suffix or ".bin"
            digest = hashlib.sha1(url.encode()).hexdigest()[:12]
            dest = shared_dir / f"{digest}{suffix}"
            with requests.get(url, headers=headers, timeout=10, stream=True) as r:
                r.raise_for_status()
                size = int(r.headers.get("Content-Length", 0))
                if size > MAX_ASSET_BYTES:
                    print(f"  SKIP Asset >5MB: {url}")
                    continue
                with open(dest, "wb") as fh:
                    total = 0
                    for chunk in r.iter_content(chunk_size=65536):
                        total += len(chunk)
                        if total > MAX_ASSET_BYTES:
                            raise ValueError("überschreitet Größenlimit")
                        fh.write(chunk)
            local_paths[url] = str(dest)
            downloaded += 1
        except Exception as ex:
            print(f"  SKIP Asset-Download {url}: {ex}")
    return local_paths


class ScreenshotTaker:
    """Hält einen Playwright-Browser-Kontext offen; degeneriert graceful,
    wenn Playwright nicht installiert oder der Start fehlschlägt."""

    def __init__(self):
        self._playwright = None
        self._context = None
        self.available = False

    def start(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  Hinweis: playwright nicht installiert — keine Screenshots. (pip install playwright && playwright install chromium)")
            return False
        try:
            self._playwright = sync_playwright().start()
            browser = self._playwright.chromium.launch(headless=True)
            self._context = browser.new_context(viewport={"width": 1280, "height": 800})
            self.available = True
            return True
        except Exception as ex:
            print(f"  Hinweis: Chromium-Start fehlgeschlagen ({ex}) — keine Screenshots.")
            return False

    def take(self, url, dest_path):
        if not self.available:
            return False
        try:
            page = self._context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(1500)  # Layout/Bilder kurz settle lassen
                page.screenshot(path=str(dest_path))
            finally:
                page.close()
            return True
        except Exception as ex:
            print(f"  Screenshot fehlgeschlagen für {url}: {ex}")
            return False

    def stop(self):
        try:
            if self._context:
                self._context.browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass


def crawl(start_url, output_dir, max_pages=25, delay=1.0,
          screenshots=True, asset_download=True):
    root_domain = urlparse(start_url).netloc
    out = Path(output_dir)
    pages_dir = out / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    visited = set()
    queue = [normalize_url(start_url)]
    page_num = 0
    results = []
    asset_refs = {}       # url -> {"type": ..., "pages": set()}
    page_numbers = {}     # page_num -> url

    headers = {"User-Agent": "Mozilla/5.0 (Educational-Research-Crawler; +academic-use)"}
    disallow_prefixes = load_robots_disallow(start_url, headers)
    if disallow_prefixes:
        print(f"  robots.txt Disallow-Pfade respektiert: {disallow_prefixes}")

    shooter = ScreenshotTaker()
    if screenshots:
        shooter.start()

    try:
        while queue and page_num < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            if is_disallowed(url, disallow_prefixes):
                print(f"  SKIP (robots.txt disallow): {url}")
                continue

            try:
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                if "text/html" not in resp.headers.get("Content-Type", ""):
                    continue
            except Exception as ex:
                print(f"  SKIP {url}: {ex}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            page_num += 1
            page_dir = pages_dir / str(page_num)
            page_dir.mkdir(parents=True, exist_ok=True)
            page_numbers[page_num] = url

            links = extract_links(soup, url)
            forms = extract_forms(soup)
            media = extract_media(soup, url)
            text = soup.get_text(separator=" ", strip=True)
            html_root = soup.find("html") or soup
            dom_tree = build_dom_tree(html_root)

            # Asset-Referenzen dieser Seite im Index vermerken
            for a_type, a_url in extract_asset_urls(soup, url):
                entry = asset_refs.setdefault(a_url, {"type": a_type, "pages": set()})
                entry["pages"].add(page_num)

            if shooter.available:
                shooter.take(url, page_dir / "screenshot.png")

            (page_dir / "links.json").write_text(json.dumps(links, ensure_ascii=False, indent=2))
            (page_dir / "forms.json").write_text(json.dumps(forms, ensure_ascii=False, indent=2))
            (page_dir / "media.json").write_text(json.dumps(media, ensure_ascii=False, indent=2))
            (page_dir / "visible_text.json").write_text(json.dumps({"url": url, "text": text}, ensure_ascii=False, indent=2))
            (page_dir / "dom.json").write_text(json.dumps(dom_tree, ensure_ascii=False, indent=2))
            (page_dir / "raw.html").write_text(resp.text, encoding="utf-8")

            results.append({"page": page_num, "url": url, "link_count": len(links), "form_count": len(forms), "media_count": len(media), "text_length": len(text)})
            print(f"  [{page_num}] {url}  links={len(links)} forms={len(forms)} media={len(media)} text={len(text)}")

            for l in links:
                href = normalize_url(l["href"])
                if same_domain(href, root_domain) and href not in visited and href not in queue:
                    queue.append(href)

            time.sleep(delay)
    finally:
        shooter.stop()

    # Asset-Index schreiben, Shared-Assets herunterladen
    asset_index = build_asset_index(asset_refs, page_numbers)
    if asset_download and asset_index["n_shared"] > 0:
        local_paths = download_shared_assets(asset_index, out, headers)
        for url, path in local_paths.items():
            asset_index["assets"][url]["local_path"] = path
    (out / "asset_index.json").write_text(json.dumps(asset_index, ensure_ascii=False, indent=2))

    (out / "portal_meta.json").write_text(json.dumps({
        "start_url": start_url,
        "page_count": page_num,
        "screenshots": shooter.available,
    }, indent=2))
    print(f"\nFertig: {page_num} Seiten gecrawlt, {asset_index['n_assets']} Assets indexiert "
          f"({asset_index['n_shared']} shared) -> {out}")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Nutzung: python3 mini_crawler.py <start_url> <output_dir> [max_pages] [--no-screenshots] [--no-asset-download]")
        sys.exit(1)
    start_url = sys.argv[1]
    output_dir = sys.argv[2]
    args = [a for a in sys.argv[3:] if not a.startswith("--")]
    max_pages = int(args[0]) if args else 25
    crawl(start_url, output_dir, max_pages=max_pages,
          screenshots="--no-screenshots" not in sys.argv,
          asset_download="--no-asset-download" not in sys.argv)
