# GSC Post-Deploy Helper

This helper automates your post-deploy Search Console workflow:

1. Submit sitemap.
2. Inspect important URLs.
3. Print direct inspection links so you can click **Request indexing**.

## Why manual click is still required

Google Search Console API does not provide a public endpoint to trigger
"Request indexing" for normal web pages. URL Inspection API is inspect-only.

## One-time setup

1. In Google Cloud, enable:
   - Search Console API
2. Create OAuth Client ID credentials (Desktop app).
3. Download the JSON and save it as:
   - `scripts/client_secret.json`

## Run (PowerShell)

```powershell
cd C:\Users\MARK\.openclaw\workspace\vargas-lawyer\scripts
.\run_gsc_post_deploy.ps1 -OpenLinks
```

## Run (Python directly)

```powershell
cd C:\Users\MARK\.openclaw\workspace\vargas-lawyer\scripts
python -m pip install -r .\requirements-gsc.txt
python .\gsc_post_deploy.py --open-links
```

## Default targets

- Property: `sc-domain:vargaslawyer.com`
- Sitemap: `https://vargaslawyer.com/sitemap.xml`
- URLs:
  - `https://vargaslawyer.com/abogados-en-santo-domingo.html`
  - `https://vargaslawyer.com/`

## Custom URLs

```powershell
python .\gsc_post_deploy.py `
  --inspect-url https://vargaslawyer.com/abogados-en-santo-domingo.html `
  --inspect-url https://vargaslawyer.com/
```
