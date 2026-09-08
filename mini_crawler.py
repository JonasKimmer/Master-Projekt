"""
Einfacher, echter Webcrawler, der das exakte Datenformat erzeugt,
das src/loaders/website_loader.py erwartet:

<website_dir>/pages/<n>/
    links.json        -> Liste von {"href": ..., "text": ...}
    forms.json         -> Liste von {"action": ..., "method": ..., "fields": n}
    media.json         -> Liste von {"type": "img"/"video"/..., "src": ...}
    visible_text.json  -> {"url": ..., "text": "..."}
    dom.json            -> {"tag": "html", "children": [...]}  (rekursiv)

Nutzung:
    python3 mini_crawler.py <start_url> <output_dir> [max_pages]

Crawlt nur Seiten innerhalb derselben Domain, respektiert einfache Same-Origin-Regel,
kein JS-Rendering (wie im Original-Tool: "statische HTML-Snapshots").
"""
import sys
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


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


def crawl(start_url, output_dir, max_pages=25, delay=1.0):
    root_domain = urlparse(start_url).netloc
    out = Path(output_dir)
    pages_dir = out / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    visited = set()
    queue = [start_url]
    page_num = 0
    results = []

    headers = {"User-Agent": "Mozilla/5.0 (Educational-Research-Crawler; +academic-use)"}
    disallow_prefixes = load_robots_disallow(start_url, headers)
    if disallow_prefixes:
        print(f"  robots.txt Disallow-Pfade respektiert: {disallow_prefixes}")

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

        links = extract_links(soup, url)
        forms = extract_forms(soup)
        media = extract_media(soup, url)
        text = soup.get_text(separator=" ", strip=True)
        html_root = soup.find("html") or soup
        dom_tree = build_dom_tree(html_root)

        (page_dir / "links.json").write_text(json.dumps(links, ensure_ascii=False, indent=2))
        (page_dir / "forms.json").write_text(json.dumps(forms, ensure_ascii=False, indent=2))
        (page_dir / "media.json").write_text(json.dumps(media, ensure_ascii=False, indent=2))
        (page_dir / "visible_text.json").write_text(json.dumps({"url": url, "text": text}, ensure_ascii=False, indent=2))
        (page_dir / "dom.json").write_text(json.dumps(dom_tree, ensure_ascii=False, indent=2))
        (page_dir / "raw.html").write_text(resp.text, encoding="utf-8")

        results.append({"page": page_num, "url": url, "link_count": len(links), "form_count": len(forms), "media_count": len(media), "text_length": len(text)})
        print(f"  [{page_num}] {url}  links={len(links)} forms={len(forms)} media={len(media)} text={len(text)}")

        for l in links:
            href = l["href"]
            if same_domain(href, root_domain) and href not in visited and href not in queue:
                # keep it simple: strip fragments/query for de-dup
                clean = href.split("#")[0]
                if clean not in visited and clean not in queue:
                    queue.append(clean)

        time.sleep(delay)

    (out / "portal_meta.json").write_text(json.dumps({"start_url": start_url, "page_count": page_num}, indent=2))
    print(f"\nFertig: {page_num} Seiten gecrawlt -> {out}")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Nutzung: python3 mini_crawler.py <start_url> <output_dir> [max_pages]")
        sys.exit(1)
    start_url = sys.argv[1]
    output_dir = sys.argv[2]
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    crawl(start_url, output_dir, max_pages=max_pages)
