import html, pathlib, re

import feedparser
import requests

BLOGS = ["https://nathanpinotti.com.br", "https://entraidbrasil.com.br"]
YT_CHANNEL_ID = "UCUaOb2eE8qvNxNMtzL1D2aQ"  # UC...


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
        print(site, page, r.status_code, r.text[:150])
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
    all_rows = {}
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.startswith("| 20"):
                r = tuple(l[2:-2].split(" | "))
                all_rows[r[2]] = r
    for r in rows:
        all_rows.setdefault(r[2], r)
    out = [f"# {title}", ""]
    for year in sorted({r[0][:4] for r in all_rows.values()}, reverse=True):
        out += [f"## {year}", "", "| Data | Título | URL | Descrição |", "|---|---|---|---|"]
        out += [f"| {d} | {t} | {u} | {x} |" for d, t, u, x in sorted((r for r in all_rows.values() if r[0][:4] == year), reverse=True)]
        out.append("")
    p.write_text("\n".join(out), encoding="utf-8")


for site in BLOGS:
    name = site.split("//")[1]
    update(f"contributions/{name}.md", f"Artigos - {name}", list(wp_posts(site)))

update("contributions/youtube.md", "Vídeos - YouTube", list(yt_videos()))
