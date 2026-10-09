import html, pathlib, re

import feedparser
import requests

BLOGS = ["https://nathanpinotti.com.br", "https://entraidbrasil.com.br"]
YT_CHANNEL_ID = "COLOQUE_O_CHANNEL_ID"  # UC...


def clean(t, n=200):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or ""))
    t = re.sub(r"\s+", " ", t).replace("|", "/").strip()
    return t[:n].rstrip() + ("…" if len(t) > n else "")


def wp_posts(site):
    page = 1
    while True:
        r = requests.get(
            f"{site}/wp-json/wp/v2/posts",
            params={"per_page": 100, "page": page, "_fields": "date,link,title,excerpt"},
            timeout=30,
        )
        if r.status_code != 200:
            break
        for p in r.json():
            yield p["date"][:10], clean(p["title"]["rendered"], 150), p["link"], clean(p["excerpt"]["rendered"])
        page += 1


def yt_videos():
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_CHANNEL_ID}")
    for e in feed.entries:
        yield e.published[:10], clean(e.title, 150), e.link, clean(e.get("summary", ""))


def update(path, title, rows):
    p = pathlib.Path(path)
    p.parent.mkdir(exist_ok=True)
    header = [f"# {title}", "", "| Data | Título | URL | Descrição |", "|---|---|---|---|"]
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else header
    body = lines[4:]
    known = "\n".join(body)
    new = sorted({r for r in rows if r[2] not in known}, reverse=True)
    if not new:
        return
    new_lines = [f"| {d} | {t} | {u} | {desc} |" for d, t, u, desc in new]
    p.write_text("\n".join(lines[:4] + new_lines + body) + "\n", encoding="utf-8")


for site in BLOGS:
    name = site.split("//")[1]
    update(f"contributions/{name}.md", f"Artigos - {name}", list(wp_posts(site)))

update("contributions/youtube.md", "Vídeos - YouTube", list(yt_videos()))
