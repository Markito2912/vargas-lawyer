#!/usr/bin/env python3
"""Regenera sitemap.xml desde los archivos que EXISTEN y YA estan publicados.

Reglas (las tres causas de los 404 de Search Console):
1. Solo entran URLs cuyo archivo existe en disco -> nunca un 404 en el sitemap.
2. Solo entran posts cuyo data-publish-datetime en blog.html ya paso -> no se
   anuncia a Google contenido que el sitio todavia oculta.
3. lastmod nunca es fecha futura -> Google descarta un sitemap con lastmod futuro.

Uso:  python scripts/generate_sitemap.py
Correr SIEMPRE despues de publicar posts (o dejarlo en el post-deploy), porque
el sitemap crece solo a medida que las fechas programadas van venciendo.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://vargaslawyer.com"
NOW = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5)))  # hora Ecuador
TODAY = NOW.date().isoformat()

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
    # vargas-lawyers.html NO va: es copia de la home (mismo title y canonical)
    # y vercel.json la redirige 301 a "/". Meterla seria contenido duplicado.
    ("calculadora-liquidacion.html", "monthly", "0.7"),
    ("blog.html", "weekly", "0.8"),
    # politica-privacidad.html NO va: lleva <meta robots="noindex">. Anunciarla
    # en el sitemap y bloquearla en la pagina es contradictorio y Search Console
    # lo reporta como "Excluida por la etiqueta noindex".
]

SLUG_DATE = re.compile(r"blog/posts/(\d{4}-\d{2}-\d{2})-")


def schedule() -> dict[str, str]:
    """{ruta relativa del post: data-publish-datetime} leido de blog.html."""
    html = (ROOT / "blog.html").read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for when, body in re.findall(
        r'data-publish-datetime="([^"]+)"(.*?)</article>', html, re.S
    ):
        m = re.search(r'href="(blog[^"]+\.html)"', body)
        if m:
            out[m.group(1)] = when
    return out


def publicado(rel: str, agenda: dict[str, str]) -> bool:
    """Un post sin fecha programada se considera ya publicado (los antiguos)."""
    when = agenda.get(rel)
    if not when:
        return True
    try:
        return dt.datetime.fromisoformat(when) <= NOW
    except ValueError:
        return True


def file_date(path: Path) -> str:
    # Fecha del ultimo commit que toco el archivo: en GitHub Actions el checkout
    # deja todos los mtime en "hoy" y el lastmod mentiria. Si el archivo tiene
    # cambios sin commitear (trabajo local), manda el mtime.
    import subprocess
    try:
        sucio = subprocess.run(['git', 'status', '--porcelain', '--', str(path)], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        if not sucio:
            fecha = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', str(path)], cwd=ROOT,
                                   capture_output=True, text=True, check=True).stdout.strip()
            if fecha:
                return min(fecha, TODAY)
    except (OSError, subprocess.CalledProcessError):
        pass
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
    agenda = schedule()
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
    ]
    seen: set[str] = set()
    ausentes: list[str] = []
    programados: list[tuple[str, str]] = []

    out.append("  <!-- PAGINAS PRINCIPALES -->\n")
    for rel, freq, prio in STATIC:
        path = ROOT / (rel or "index.html")
        if not path.is_file():
            ausentes.append(rel or "index.html")
            continue
        out.append(entry(f"{BASE}/{rel}", file_date(path), freq, prio))
        seen.add(f"{BASE}/{rel}")

    meta = {
        p["url"].replace(f"{BASE}/", ""): p
        for p in json.loads((ROOT / "blog" / "posts.json").read_text(encoding="utf-8"))
    }

    legacy = sorted(ROOT.glob("blog-*.html"))
    dated = sorted((ROOT / "blog" / "posts").glob("*.html"), key=lambda p: p.name)

    out.append("\n  <!-- ARTICULOS DE BLOG PUBLICADOS -->\n")
    for path in legacy + dated:
        rel = path.relative_to(ROOT).as_posix()
        loc = f"{BASE}/{rel}"
        if loc in seen:
            continue
        if not publicado(rel, agenda):
            programados.append((agenda[rel][:10], rel))
            continue
        m = SLUG_DATE.match(rel)
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

    print(f"sitemap.xml: {len(seen)} URLs publicadas y verificadas en disco")
    if programados:
        programados.sort()
        print(f"\nFUERA del sitemap por estar programados a futuro ({len(programados)}):")
        for when, rel in programados:
            print(f"  {when}  {rel}")
        print("  -> entran solos al volver a correr este script tras cada publicacion")
    fantasmas = sorted(r for r in meta if not (ROOT / r).is_file())
    if fantasmas:
        print(f"\nAVISO - posts.json apunta a archivos inexistentes ({len(fantasmas)}):")
        for r in fantasmas:
            print(f"  - {r}")
    if ausentes:
        print(f"\nAVISO - paginas estaticas ausentes: {ausentes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
