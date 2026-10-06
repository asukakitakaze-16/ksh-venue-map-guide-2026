import html
import json
import re
from pathlib import Path


OUTPUT = Path(__file__).with_name("solution-data.js")

CATEGORIES = {
    "staffing": {
        "title": "人手不足・省人化を解決する出展者",
        "lead": "省人化、業務効率化、現場負担の軽減につながる製品・サービスを紹介する出展者です。",
        "color": "#c64040",
        "sources": [
            ("人手不足", Path("/tmp/ksh-guide-hospitality-人手不足.html")),
            ("省人化", Path("/tmp/ksh-guide-hospitality-省人化.html")),
        ],
    },
    "renovation": {
        "title": "改修・リノベーションに役立つ出展者",
        "lead": "家具、内装、ベッド、改装など、施設の価値向上や差別化につながる出展者です。",
        "color": "#2874a8",
        "sources": [
            ("家具", Path("/tmp/ksh-guide-hospitality-家具.html")),
            ("内装", Path("/tmp/ksh-guide-hospitality-内装.html")),
            ("ベッド", Path("/tmp/ksh-guide-hospitality-ベッド.html")),
            ("改装", Path("/tmp/ksh-guide-hospitality-改装.html")),
        ],
    },
    "inbound": {
        "title": "インバウンド対応に役立つ出展者",
        "lead": "多言語対応、海外旅行者の受け入れ、訪日客向けサービスに関連する出展者です。",
        "color": "#d97528",
        "sources": [
            ("インバウンド", Path("/tmp/ksh-guide-hospitality-インバウンド.html")),
        ],
    },
}


def clean(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    return re.sub(r"\s+", " ", fragment).strip()


def extract(source: Path, matched_term: str):
    text = source.read_text(encoding="utf-8")
    cards = re.findall(
        r'<a href="([^"]+)" class="guide-card-link">(.*?)</a>',
        text,
        flags=re.S,
    )
    results = []
    for url, card in cards:
        name_match = re.search(r"<h2>(.*?)</h2>", card, flags=re.S)
        if not name_match:
            continue
        booth_match = re.search(r'<div class="booth-no">(.*?)</div>', card, flags=re.S)
        expo_match = re.search(r'<div class="exhibition-ribbon">(.*?)</div>', card, flags=re.S)
        image_match = re.search(r'<div class="guide-logo-area">.*?<img src="([^"]+)"', card, flags=re.S)
        summary_match = re.search(
            r'<h3>ブースのみどころ</h3>\s*<p>(.*?)</p>',
            card,
            flags=re.S,
        )
        feature_matches = re.findall(r'<span class="feature-badge[^>]*>(.*?)</span>', card, flags=re.S)
        summary = clean(summary_match.group(1)) if summary_match else ""
        if len(summary) > 190:
            summary = summary[:187].rstrip() + "…"
        results.append(
            {
                "name": clean(name_match.group(1)),
                "url": url,
                "booth": clean(booth_match.group(1)).replace("ブースNo.", "").strip() if booth_match else "-",
                "exhibition": clean(expo_match.group(1)) if expo_match else "",
                "image": image_match.group(1) if image_match else "",
                "summary": summary,
                "features": [clean(item) for item in feature_matches],
                "matchedTerms": [matched_term],
            }
        )
    return results


payload = {}
for key, config in CATEGORIES.items():
    merged = {}
    for term, source in config["sources"]:
        for item in extract(source, term):
            if item["url"] in merged:
                merged[item["url"]]["matchedTerms"].append(term)
            else:
                merged[item["url"]] = item

    companies = sorted(
        merged.values(),
        key=lambda item: (item["booth"] == "-", item["booth"], item["name"]),
    )
    payload[key] = {
        "title": config["title"],
        "lead": config["lead"],
        "color": config["color"],
        "companies": companies,
    }

OUTPUT.write_text(
    "window.KSH_SOLUTION_DATA = "
    + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    + ";\n",
    encoding="utf-8",
)

for key, value in payload.items():
    print(f"{key}: {len(value['companies'])} companies")
