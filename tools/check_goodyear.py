"""Daily check of goodyear.com.au for changes that affect our website.

Loads Goodyear Australia's promotions page (including the promotion iframe),
the warranty pages and our store's listing in a headless browser, saves the
visible text to data/goodyear_snapshot.json and prints what changed since the
last run. It changes nothing on the website itself: a person (or Claude)
reads the report, updates data/goodyear.json, then runs build_goodyear.py.

Usage:  python3 tools/check_goodyear.py
Exit code 0 = nothing changed, 10 = something changed (read the report).
"""
import asyncio
import datetime as dt
import difflib
import hashlib
import json
import pathlib
import sys

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "goodyear_snapshot.json"
BASE = "https://www.goodyear.com.au"
PAGES = {
    "promotions": "/promotions",
    "warranty": "/warranty",
    "tyre-protection-plan": "/warranty/tyre-protection-plan",
    "warranty-and-guarantee-policy": "/warranty/warranty-and-guarantee-policy",
    "duraplus-2-mileage": "/warranty/assurance-duraplus-2-mileage-warranty",
    "maxguard-mileage": "/warranty/goodyear-assurance-maxguard-goodyear-assurance-maxguard-suv",
    "wrangler-at-adventure-mileage": "/warranty/wrangler-at-adventure-mileage-warranty",
    "store-hobart": "/store-locator/goodyear-autocare-hobart",
}
# Site chrome that appears on every page and is not worth diffing.
NOISE = ("Promotions", "Contact Us", "Tyres", "Join Our Network", "About Us", "FIND MY STORE",
         "FIND MY TYRES", "Search", "Have questions?", "CONTACT US", "COMPANY", "Corporate",
         "Careers", "Goodyear Brand", "Goodyear Blimp", "FOR CUSTOMERS", "Tyre Warranties",
         "FOR DEALERS", "SUPPORT", "Find a Store", "Accessibility", "Privacy Policy",
         "Intellectual Property", "Terms & Conditions of Trade", "Site Map", "Manage Cookie Preferences")


def clean(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line in NOISE or "cookies" in line.lower() or line.startswith("©"):
            continue
        out.append(line)
    return "\n".join(out)


async def grab(page, url):
    await page.goto(url, wait_until="networkidle", timeout=90000)
    await page.wait_for_timeout(3000)
    for _ in range(6):
        await page.mouse.wheel(0, 2500)
        await page.wait_for_timeout(300)
    parts = []
    for f in page.frames:
        if f.url.startswith(("about:", "chrome-error:")) or "recaptcha" in f.url:
            continue
        try:
            t = await f.evaluate("document.body ? document.body.innerText : ''")
        except Exception:
            continue
        if t.strip():
            parts.append(("" if f == page.main_frame else f"[frame {f.url.split('?')[0]}]\n") + t)
    return clean("\n".join(parts))


async def main():
    old = json.loads(SNAP.read_text()) if SNAP.exists() else {"pages": {}}
    new = {"taken": dt.datetime.now().isoformat(timespec="minutes"), "pages": {}}
    changed = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1366, "height": 900},
                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36")
        for key, path in PAGES.items():
            try:
                text = await grab(page, BASE + path)
            except Exception as ex:  # keep going; report the failure
                print(f"!! {key}: could not load ({ex})")
                text = old["pages"].get(key, {}).get("text", "")
            h = hashlib.sha256(text.encode()).hexdigest()[:16]
            new["pages"][key] = {"url": BASE + path, "hash": h, "text": text}
            prev = old["pages"].get(key)
            if prev and prev["hash"] != h:
                changed.append(key)
                diff = difflib.unified_diff(prev["text"].splitlines(), text.splitlines(), "before", "now", n=1, lineterm="")
                print(f"\n=== CHANGED: {key} ({BASE + path})")
                print("\n".join(list(diff)[:80]))
            elif not prev:
                print(f"(first snapshot of {key})")
        await b.close()
    promo = new["pages"]["promotions"]["text"]
    print("\n=== Promotions page now says:")
    print(promo[:1500] or "(empty)")
    print("\nPromotion status:", "CLOSED / none running" if ("Promotion Closed" in promo or not promo.strip()) else "POSSIBLY ACTIVE - read it")
    SNAP.write_text(json.dumps(new, indent=1, ensure_ascii=False))
    print("\nChanged pages:", changed or "none")
    sys.exit(10 if changed else 0)


asyncio.run(main())
