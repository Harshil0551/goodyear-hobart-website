# Goodyear Auto Care Hobart – website

Source for **https://goodyearautocarehobart.com**

Owner: Antilia Capital Pty Ltd (ACN 698 318 544, ABN 64 698 318 544) trading as
Boost Auto Hub, a licensed Goodyear Auto Care workshop at 94–96 Brisbane St,
Hobart TAS 7000.

## Where it's hosted

| | |
|---|---|
| Host | Netlify, project `goodyear-hobart` |
| Netlify site id | `7e5f8ead-7864-47ea-9608-bbb4b7c7e7ea` |
| Domain | goodyearautocarehobart.com (www redirects to it) |
| Forms | `booking` and `enquiry` (Netlify Forms, honeypot `bot-field`) |

## What's in this repo

```
site/                    <- the only folder Netlify publishes (see netlify.toml)
  index.html             <- the whole site: one self-contained page, images embedded
  _headers               <- security headers (CSP, X-Frame-Options, etc.)
  .well-known/security.txt
data/goodyear.json       <- facts for the "Goodyear deals & warranties" section
data/goodyear_snapshot.json <- last copy of Goodyear's pages (for spotting changes)
tools/check_goodyear.py  <- daily: compares goodyear.com.au with the last snapshot
tools/build_goodyear.py  <- rebuilds that section of site/index.html from data/goodyear.json
tests/check_live.py      <- post-deploy check (Playwright)
netlify.toml             <- publish = "site"
```

## Making a change

1. Edit `site/index.html` (or `_headers`).
2. Keep these working, they are load-bearing:
   - the two forms: `name="booking"` / `name="enquiry"`, `data-netlify="true"`,
     `netlify-honeypot="bot-field"`, and their field names (Netlify stores
     submissions by field name; renaming one starts a new column);
   - the legal footer (`<p class="flegal">`) and the Website terms section
     (`<details id="t-website">`) – update "Last updated" if the terms change;
   - everything is self-hosted. If you add anything loaded from another site
     (fonts, scripts, images, a video or map embed), add that site to the
     matching line of the Content-Security-Policy in `site/_headers`, or the
     browser will block it.
3. Commit and push to `main`.
4. Deploy: Netlify connector → `deploy-site` with the site id above, then run the
   command it returns **from the repo root** (netlify.toml makes it publish `site/`).
5. Check: `python3 tests/check_live.py` should print `RESULT: OK`, and
   `curl -sI https://goodyearautocarehobart.com/` should show the security headers.

## Goodyear deals & warranties (updated daily)

1. `python3 tools/check_goodyear.py` - prints what changed on goodyear.com.au
   (exit code 10 = something changed).
2. If a promotion is running, add it to `promotions` in `data/goodyear.json` with the
   exact dates, conditions and Goodyear's terms link. Ended ones drop off by themselves.
   If a warranty number changed, update it there too. Update `checked` to today.
3. `python3 tools/build_goodyear.py`, then deploy and check as above.

Never invent or round a deal, date or number: copy what Goodyear publishes.
The store takes part in Goodyear's national promotions and offers the Tyre
Protection Plan (confirmed by Harshil, 24 Nov 2026).

## Dates to remember

- Workshop end-of-year deals end 31 Dec 2026 (the page hides them by itself after that).
- `security.txt` expires **2027-11-22** – renew the `Expires:` line before then.
- Domain renewal: keep auto-renew on at the registrar.

The legal wording on the site is general information, not legal advice.
