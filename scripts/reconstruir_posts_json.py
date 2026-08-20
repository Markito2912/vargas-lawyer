# -*- coding: utf-8 -*-
"""Completa blog/posts.json con los posts que existen en disco pero faltaban.

Lee title, description, fecha y categoria del propio HTML de cada post — nada
inventado. Respeta las entradas que ya estaban (no las sobreescribe) y ordena
por fecha. La fecha de publicacion sale, en este orden:
  1. data-publish-datetime de blog.html (la agenda real, manda)
  2. datePublished del JSON-LD del post
  3. la fecha del slug del archivo

Uso:  python scripts/reconstruir_posts_json.py
"""

from __future__ import annotations

import io
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://vargaslawyer.com'
JSON = ROOT / 'blog' / 'posts.json'

CATEGORIAS = [
    ('Derecho Laboral', ['despido', 'finiquito', 'horas-extra', 'vacaciones', 'acoso-laboral',
                         'trabajador-domestico', 'contrato-prueba', 'jubilacion-patronal',
                         'decimo', 'maternidad', 'liquidacion-laboral', 'pymes']),
    ('Derecho de Familia', ['pension-alimenticia', 'divorcio', 'tenencia', 'sociedad-conyugal',
                            'union-de-hecho', 'reconocimiento-hijo', 'violencia-intrafamiliar',
                            'adopcion', 'salida-menor', 'herencias', 'testamento']),
    ('Derecho Societario', ['constituir-empresa', 'junta-general', 'estatutos',
                            'representante-legal', 'disolver-empresa', 'liquidacion-companias',
                            'sas']),
    ('Propiedad Intelectual', ['patente', 'derechos-autor', 'marca', 'senadi']),
    ('Derecho Constitucional', ['habeas-corpus', 'habeas-data', 'accion-proteccion']),
    ('Inquilinato', ['arriendo', 'arrendamiento', 'inquilinato']),
    ('Derecho Civil', ['prescripcion', 'incumplimiento', 'nulidad', 'prestamo', 'dano-moral',
                       'usucapion', 'compraventa', 'juicio-ejecutivo', 'letra-cambio',
                       'consumidor', 'mediacion', 'responsabilidad-medica', 'civil']),
]


def limpia(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()


def uno(pat, s):
    m = re.search(pat, s, re.I | re.S)
    return limpia(m.group(1)) if m else None


def agenda():
    html = (ROOT / 'blog.html').read_text(encoding='utf-8', errors='replace')
    out = {}
    for when, body in re.findall(r'data-publish-datetime="([^"]+)"(.*?)</article>', html, re.S):
        m = re.search(r'href="(blog[^"]+\.html)"', body)
        if m:
            out[m.group(1)] = when[:10]
    return out


def categoria(rel):
    bajo = rel.lower()
    for nombre, claves in CATEGORIAS:
        if any(k in bajo for k in claves):
            return nombre
    return 'Legal'


def main() -> int:
    AGENDA = agenda()
    existentes = json.loads(JSON.read_text(encoding='utf-8'))
    por_url = {e['url']: e for e in existentes}

    archivos = sorted(list(ROOT.glob('blog-*.html'))
                      + list((ROOT / 'blog' / 'posts').glob('*.html')))

    nuevos = []
    for p in archivos:
        rel = p.relative_to(ROOT).as_posix()
        url = '%s/%s' % (BASE, rel)
        if url in por_url:
            continue

        s = p.read_text(encoding='utf-8', errors='replace')
        title = uno(r'<title[^>]*>(.*?)</title>', s) or p.stem
        title = re.sub(r'\s*[-|]\s*(VARGAS LAWYERS|Vargas Lawyers).*$', '', title).strip()

        desc = uno(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', s) or ''

        fecha = AGENDA.get(rel)
        if not fecha:
            fecha = uno(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', s)
        if not fecha:
            m = re.match(r'blog/posts/(\d{4}-\d{2}-\d{2})-', rel)
            fecha = m.group(1) if m else ''

        kw = uno(r'<meta\s+name=["\']keywords["\']\s+content=["\'](.*?)["\']', s) or ''

        slug = (re.sub(r'^\d{4}-\d{2}-\d{2}-', '', p.stem)
                if rel.startswith('blog/posts/') else re.sub(r'^blog-', '', p.stem))

        nuevos.append({
            'title': title,
            'date': fecha,
            'slug': slug,
            'excerpt': desc,
            'url': url,
            'keyword': kw.split(',')[0].strip() if kw else slug.replace('-', ' '),
            'category': categoria(rel),
        })

    # fantasmas: entradas que apuntan a archivos que no existen
    fantasmas = [e for e in existentes
                 if not (ROOT / e['url'].replace(BASE + '/', '')).is_file()]

    todos = existentes + nuevos
    todos.sort(key=lambda e: (e.get('date') or '', e.get('slug') or ''))

    io.open(JSON, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(todos, ensure_ascii=False, indent=2) + '\n')

    print('posts.json: %d -> %d entradas (+%d)' % (len(existentes), len(todos), len(nuevos)))
    for e in nuevos:
        print('   + %s  %-22s %s' % (e['date'] or '????-??-??', e['category'], e['title'][:52]))
    if fantasmas:
        print('\nAVISO - entradas que apuntan a archivos inexistentes (%d):' % len(fantasmas))
        for e in fantasmas:
            print('   - %s' % e['url'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
