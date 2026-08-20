# -*- coding: utf-8 -*-
"""Auditoria SEO on-page. Correr ANTES de cada push.

Salida vacia = todo en regla. Cada bloque que aparece es algo a corregir.

Uso:  python scripts/auditoria_seo.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://vargaslawyer.com'
IGNORAR = {'services-clean.html', 'services-section.html'}
# copia de la home: redirige 301 a "/" en vercel.json, por eso no se audita
REDIRIGIDAS = {'vargas-lawyers.html'}

MAX_TITLE, MIN_DESC, MAX_DESC = 65, 70, 165


def paginas():
    todas = list(ROOT.glob('*.html')) + list((ROOT / 'blog' / 'posts').glob('*.html'))
    return sorted(p for p in todas
                  if p.name not in IGNORAR
                  and p.relative_to(ROOT).as_posix() not in REDIRIGIDAS)


def uno(pat, s):
    m = re.search(pat, s, re.I | re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else None


def main() -> int:
    filas = []
    titles, descs, canons = collections.Counter(), collections.Counter(), collections.Counter()

    for p in paginas():
        s = p.read_text(encoding='utf-8', errors='replace')
        rel = p.relative_to(ROOT).as_posix()
        esperado = BASE + '/' + ('' if p.name == 'index.html' else rel)

        ld_roto = []
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(b)
            except Exception as e:
                ld_roto.append(str(e)[:60])

        f = {
            'rel': rel,
            'title': uno(r'<title[^>]*>(.*?)</title>', s),
            'desc': uno(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', s),
            'canon': uno(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']', s),
            'esperado': esperado,
            'robots': uno(r'<meta\s+name=["\']robots["\']\s+content=["\'](.*?)["\']', s),
            'h1': len(re.findall(r'<h1[^>]*>', s, re.I)),
            'og': [k for k in ('og:type', 'og:url', 'og:title', 'og:description',
                               'og:image', 'og:locale', 'og:site_name')
                   if not re.search(re.escape(k), s, re.I)],
            'tw': bool(re.search(r'name=["\']twitter:card["\']', s, re.I)),
            'tw_mal': bool(re.search(r'property=["\']twitter:', s, re.I)),
            'ld': s.count('application/ld+json'),
            'ld_roto': ld_roto,
            'noalt': len([i for i in re.findall(r'<img\b[^>]*>', s, re.I)
                          if not re.search(r'\balt\s*=', i, re.I)]),
        }
        filas.append(f)
        for clave, cont in (('title', titles), ('desc', descs), ('canon', canons)):
            if f[clave]:
                cont[f[clave]] += 1

    problemas = 0

    def bloque(titulo, items):
        nonlocal problemas
        if items:
            problemas += len(items)
            print('\n### %s (%d)' % (titulo, len(items)))
            for i in items:
                print('   ', i)

    es404 = lambda f: f['rel'] == '404.html'

    bloque('SIN <title>', [f['rel'] for f in filas if not f['title']])
    bloque('TITLE > %d caracteres' % MAX_TITLE,
           ['%3d  %s' % (len(f['title']), f['rel']) for f in filas
            if f['title'] and len(f['title']) > MAX_TITLE])
    bloque('TITLE duplicado', ['x%d  %s' % (c, t[:70]) for t, c in titles.items() if c > 1])
    bloque('SIN meta description', [f['rel'] for f in filas if not f['desc'] and not es404(f)])
    bloque('DESCRIPTION fuera de %d-%d' % (MIN_DESC, MAX_DESC),
           ['%3d  %s' % (len(f['desc']), f['rel']) for f in filas
            if f['desc'] and not (MIN_DESC <= len(f['desc']) <= MAX_DESC)])
    bloque('DESCRIPTION duplicada', ['x%d  %s' % (c, d[:70]) for d, c in descs.items() if c > 1])
    bloque('SIN canonical', [f['rel'] for f in filas if not f['canon'] and not es404(f)])
    bloque('CANONICAL que no apunta a su propia URL',
           ['%s\n        -> %s' % (f['rel'], f['canon']) for f in filas
            if f['canon'] and f['canon'].rstrip('/') != f['esperado'].rstrip('/')])
    bloque('CANONICAL duplicado (canibalizacion)',
           ['x%d  %s' % (c, u) for u, c in canons.items() if c > 1])
    bloque('H1 distinto de 1', ['h1=%d  %s' % (f['h1'], f['rel']) for f in filas if f['h1'] != 1])
    bloque('OPEN GRAPH incompleto',
           ['%s  faltan: %s' % (f['rel'], ', '.join(f['og'])) for f in filas if f['og']])
    bloque('SIN twitter:card', [f['rel'] for f in filas if not f['tw']])
    bloque('twitter con property= en vez de name=', [f['rel'] for f in filas if f['tw_mal']])
    bloque('SIN meta robots', [f['rel'] for f in filas if not f['robots']])
    bloque('404.html deberia ser noindex',
           [f['rel'] for f in filas if es404(f) and 'noindex' not in (f['robots'] or '')])
    bloque('SIN JSON-LD', [f['rel'] for f in filas if not f['ld'] and not es404(f)])
    bloque('JSON-LD QUE NO PARSEA (Google lo descarta entero)',
           ['%s  %s' % (f['rel'], f['ld_roto'][0]) for f in filas if f['ld_roto']])
    bloque('IMGs sin alt', ['%d imgs  %s' % (f['noalt'], f['rel']) for f in filas if f['noalt']])

    # sitemap
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    locs = re.findall(r'<loc>([^<]+)</loc>', sm)
    lastmods = re.findall(r'<lastmod>([^<]+)</lastmod>', sm)
    import datetime as dt
    hoy = dt.date.today().isoformat()
    bloque('SITEMAP: archivo inexistente',
           [u for u in locs
            if not (ROOT / (u.replace(BASE + '/', '') or 'index.html')).is_file()])
    bloque('SITEMAP: lastmod en el futuro', [d for d in lastmods if d > hoy])
    bloque('SITEMAP: URL duplicada',
           ['x%d  %s' % (c, u) for u, c in collections.Counter(locs).items() if c > 1])
    bloque('SITEMAP: pagina redirigida incluida',
           [u for u in locs if u.replace(BASE + '/', '') in REDIRIGIDAS])

    print('\n%d paginas auditadas | sitemap con %d URLs' % (len(filas), len(locs)))
    if problemas:
        print('%d problemas -> NO deployar hasta corregirlos' % problemas)
        return 1
    print('Sin problemas. Listo para push.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
