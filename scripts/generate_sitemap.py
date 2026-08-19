#!/usr/bin/env python3
"""Regenera sitemap.xml desde los archivos que EXISTEN en disco.

Reglas:
- Solo entran URLs cuyo archivo existe (no se inventan URLs -> no mas 404 en GSC).
- lastmod nunca puede ser fecha futura (Google descarta el sitemap si lo es).
- Para blog/posts/, lastmod = fecha de publicacion del slug.
- posts.json se usa solo como metadata; la fuente de verdad es el disco.

Uso:  python scripts/generate_sitemap.py
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://vargaslawyer.com"
TODAY = dt.date.today().isoformat()

# (ruta, changefreq, priority) — este orden es el orden del sitemap
STATIC = [
    ("", "weekly", "1.0"),
    ("societario.html", "monthly", "0.9"),
    ("laboral.html", "monthly", "0.9"),
    ("civil.html", "monthly", "0.9"),
    ("familia.html", "monthly", "0.9"),
    ("constitucional.html", "monthly", "0.9"),
    ("propiedad-intelectual.html", "monthly", "0.9"),
    ("inquilinato.html", "monthly", "0.9"),
    ("notarial.html", "monthly", "0.9"),
    ("abogados-en-santo-domingo.html", "weekly", "0.95"),
    ("abogados-en-la-concordia.html", "monthly", "0.8"),
    ("abogados-en-el-carmen.html", "monthly", "0.8"),
    ("vargas-lawyers.html", "monthly", "0.7"),
    ("calculadora-liquidacion.html", "monthly", "0.7"),
    ("blog.html", "weekly", "0.8"),
    ("politica-privacidad.html", "yearly", "0.3"),
]

DATE_RE = re.compile(r"blog/posts/(\d{4}-\d{2}-\d{2})-")


def file_date(path: Path) -> str:
    """Fecha de modificacion del archivo, topada a hoy."""
    return min(dt.date.fromtimestamp(path.stat().st_mtime).isoformat(), TODAY)


def entry(loc: str, lastmod: str, changefreq: str, priority: str) -> str:
    return (
        "  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        "  </url>\n"
    )


def main() -> int:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
    ]
    seen: set[str] = set()
    skipped: list[str] = []

    out.append("  <!-- PAGINAS PRINCIPALES -->\n")
    for rel, freq, prio in STATIC:
        path = ROOT / (rel or "index.html")
        if not path.is_file():
            skipped.append(rel or "index.html")
            continue
        loc = f"{BASE}/{rel}"
        out.append(entry(loc, file_date(path), freq, prio))
        seen.add(loc)

    meta = {
        p["url"].replace(f"{BASE}/", ""): p
        for p in json.loads((ROOT / "blog" / "posts.json").read_text(encoding="utf-8"))
    }

    legacy = sorted(ROOT.glob("blog-*.html"))
    dated = sorted((ROOT / "blog" / "posts").glob("*.html"), key=lambda p: p.name)

    out.append("\n  <!-- ARTICULOS DE BLOG -->\n")
    for path in legacy + dated:
        rel = path.relative_to(ROOT).as_posix()
        loc = f"{BASE}/{rel}"
        if loc in seen:
            continue
        m = DATE_RE.match(rel)
        if m:
            lastmod = min(m.group(1), TODAY)
        elif rel in meta and meta[rel].get("date"):
            lastmod = min(meta[rel]["date"], TODAY)
        else:
            lastmod = file_date(path)
        out.append(entry(loc, lastmod, "monthly", "0.7"))
        seen.add(loc)

    out.append("</urlset>\n")
    (ROOT / "sitemap.xml").write_text("".join(out), encoding="utf-8")

    print(f"sitemap.xml: {len(seen)} URLs (todas verificadas en disco)")

    fantasmas = sorted(r for r in meta if not (ROOT / r).is_file())
    if fantasmas:
        print(f"AVISO - posts.json apunta a archivos inexistentes ({len(fantasmas)}):")
        for r in fantasmas:
            print(f"  - {r}")
    if skipped:
        print(f"AVISO - paginas estaticas ausentes ({len(skipped)}): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
