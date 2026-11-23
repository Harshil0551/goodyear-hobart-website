"""Quick check of the live website after a deploy.

Usage:  python3 tests/check_live.py [url]
Loads the page at desktop and phone width with Playwright (Chromium) and
prints the HTTP status, any console errors, any Content-Security-Policy
violations, and the start of the legal footer.
"""
import asyncio
import sys

from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://goodyearautocarehobart.com/"


async def main():
    ok = True
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for width, height in [(1366, 800), (390, 844)]:
            page = await browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            await page.add_init_script(
                "window.__v=[];document.addEventListener('securitypolicyviolation',"
                "e=>window.__v.push(e.violatedDirective+' '+e.blockedURI))"
            )
            resp = await page.goto(URL, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2000)
            violations = await page.evaluate("window.__v")
            footer = await page.evaluate(
                "document.querySelector('.flegal') ? "
                "document.querySelector('.flegal').innerText.slice(0,100) : 'NO LEGAL FOOTER'"
            )
            print(f"{width}px  status={resp.status}  csp_violations={violations}  errors={errors[:5]}")
            print(f"   footer: {footer}")
            if resp.status != 200 or violations or errors or footer == "NO LEGAL FOOTER":
                ok = False
        await browser.close()
    print("RESULT:", "OK" if ok else "PROBLEMS FOUND")
    sys.exit(0 if ok else 1)


asyncio.run(main())
