# -*- coding: utf-8 -*-
"""Mantenimiento SEO: JSON-LD faltante + articulos relacionados (regenerables).

Solo enlaza posts YA publicados (respeta data-publish-datetime de blog.html).
"""
import re
import io
import json
import datetime as dt
import pathlib

ROOT = pathlib.Path('.')
BASE = 'https://vargaslawyer.com'
NOW = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5)))

ORG = {
    "@type": "LegalService",
    "name": "VARGAS LAWYERS S.A.S.",
    "url": BASE + "/",
    "image": BASE + "/vargas-logo-full.png",
    "telephone": "+593",
    "priceRange": "$$",
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Santo Domingo de los Tsáchilas",
        "addressCountry": "EC",
    },
}

# --- servicios que no tenian JSON-LD: (archivo, serviceType, descripcion) ---
SERVICIOS = {
    'constitucional.html': (
        "Derecho Constitucional",
        "Acciones de protección, hábeas corpus y hábeas data ante jueces "
        "constitucionales en Santo Domingo y todo Ecuador."),
    'inquilinato.html': (
        "Inquilinato y Arrendamiento",
        "Desalojos, contratos de arriendo, cobro de cánones y juicios de "
        "inquilinato para propietarios y arrendatarios en Ecuador."),
    'notarial.html': (
        "Trámites Notariales",
        "Divorcio por mutuo consentimiento, testamentos, poderes, permisos de "
        "salida de menores y escrituras públicas en Santo Domingo."),
    'propiedad-intelectual.html': (
        "Propiedad Intelectual",
        "Registro de marcas y patentes en SENADI, derechos de autor y defensa "
        "ante infracciones en Ecuador."),
}

# --- servicio -> fragmentos de slug de posts relacionados ---
RELACIONADOS = {
    'laboral.html': ['despido-intempestivo', 'acta-finiquito', 'horas-extra',
                     'vacaciones-no-pagadas', 'acoso-laboral', 'trabajador-domestico',
                     'contrato-prueba', 'jubilacion-patronal', 'decimo-cuarto',
                     'licencia-maternidad'],
    'familia.html': ['pension-alimenticia', 'divorcio', 'tenencia', 'sociedad-conyugal',
                     'union-de-hecho', 'reconocimiento-hijo', 'violencia-intrafamiliar',
                     'adopcion', 'salida-menor'],
    'civil.html': ['prescripcion-deudas', 'incumplimiento-contrato', 'nulidad-contrato',
                   'prestamo-entre-particulares', 'dano-moral', 'usucapion',
                   'compraventa-inmueble', 'juicio-ejecutivo', 'compraventa-vehiculo',
                   'cobro-letra-cambio'],
    'societario.html': ['constituir-empresa', 'junta-general-accionistas',
                        'modificar-estatutos', 'representante-legal', 'disolver-empresa',
                        'liquidacion-companias', 'sas-constitucion', 'pymes-blindaje'],
    'constitucional.html': ['habeas-corpus', 'habeas-data', 'accion-proteccion'],
    'inquilinato.html': ['contrato-arriendo', 'arrendamiento-local-comercial',
                         'inquilinato-desalojo'],
    'notarial.html': ['testamento', 'salida-menor', 'compraventa-inmueble',
                      'divorcio-notarial', 'herencias-posesion-efectiva'],
    'propiedad-intelectual.html': ['patente-invento', 'derechos-autor', 'marca-comercial',
                                   'registro-marca-senadi'],
}


def agenda():
    """{ruta post: fecha programada} desde blog.html."""
    html = (ROOT / 'blog.html').read_text(encoding='utf-8', errors='replace')
    out = {}
    for when, body in re.findall(r'data-publish-datetime="([^"]+)"(.*?)</article>', html, re.S):
        m = re.search(r'href="(blog[^"]+\.html)"', body)
        if m:
            out[m.group(1)] = when
    return out


AGENDA = agenda()


def publicado(rel):
    w = AGENDA.get(rel)
    if not w:
        return True
    try:
        return dt.datetime.fromisoformat(w) <= NOW
    except ValueError:
        return True


def titulo_de(p):
    s = p.read_text(encoding='utf-8', errors='replace')
    m = re.search(r'<title[^>]*>(.*?)</title>', s, re.I | re.S)
    t = re.sub(r'\s+', ' ', m.group(1)).strip() if m else p.stem
    return re.sub(r'\s*\|\s*Vargas Lawyers.*$', '', t, flags=re.I)


POSTS = {}
for p in sorted(list((ROOT / 'blog' / 'posts').glob('*.html')) + list(ROOT.glob('blog-*.html'))):
    rel = p.as_posix()
    if publicado(rel):
        POSTS[rel] = titulo_de(p)


def ld(obj):
    return ('\n    <script type="application/ld+json">\n    '
            + json.dumps(obj, ensure_ascii=False, indent=4).replace('\n', '\n    ')
            + '\n    </script>')


def breadcrumb(*pares):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                for i, (n, u) in enumerate(pares)]}


def inserta_ld(s, bloques):
    anchor = re.search(r'</head>', s, re.I)
    txt = ''.join(ld(b) for b in bloques) + '\n'
    return s[:anchor.start()] + txt + s[anchor.start():]


cambios = []

# ---------- 1. JSON-LD faltante ----------
JSONLD = {}

JSONLD['blog.html'] = [
    {"@context": "https://schema.org", "@type": "Blog",
     "@id": BASE + "/blog.html", "name": "Blog Legal | VARGAS LAWYERS",
     "description": "Guías prácticas de derecho ecuatoriano: laboral, familia, civil, "
                    "societario, inquilinato y propiedad intelectual.",
     "inLanguage": "es-EC", "publisher": ORG},
    breadcrumb(("Inicio", BASE + "/"), ("Blog", BASE + "/blog.html")),
]

JSONLD['calculadora-liquidacion.html'] = [
    {"@context": "https://schema.org", "@type": "WebApplication",
     "name": "Calculadora de Liquidación Laboral Ecuador",
     "url": BASE + "/calculadora-liquidacion.html",
     "applicationCategory": "FinanceApplication",
     "operatingSystem": "Web",
     "inLanguage": "es-EC",
     "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
     "description": "Calcula gratis tu liquidación por despido intempestivo o "
                    "desahucio según el Código del Trabajo ecuatoriano.",
     "provider": ORG},
    breadcrumb(("Inicio", BASE + "/"),
               ("Calculadora de Liquidación", BASE + "/calculadora-liquidacion.html")),
]

JSONLD['politica-privacidad.html'] = [
    {"@context": "https://schema.org", "@type": "WebPage",
     "name": "Política de Privacidad", "url": BASE + "/politica-privacidad.html",
     "inLanguage": "es-EC", "publisher": ORG},
    breadcrumb(("Inicio", BASE + "/"),
               ("Política de Privacidad", BASE + "/politica-privacidad.html")),
]

for f, (stype, desc) in SERVICIOS.items():
    JSONLD[f] = [
        {"@context": "https://schema.org", "@type": "Service",
         "serviceType": stype, "description": desc, "provider": ORG,
         "areaServed": [{"@type": "City", "name": "Santo Domingo de los Tsáchilas"},
                        {"@type": "Country", "name": "Ecuador"}]},
        breadcrumb(("Inicio", BASE + "/"), (stype, BASE + "/" + f)),
    ]

POST_NUEVO = 'blog/posts/2026-07-30-disolver-empresa-ecuador-liquidacion-cierre-superintendencia.html'
JSONLD[POST_NUEVO] = [
    {"@context": "https://schema.org", "@type": "Article",
     "headline": "Disolver y Liquidar una Empresa en Ecuador: Proceso Completo",
     "mainEntityOfPage": {"@type": "WebPage", "@id": BASE + "/" + POST_NUEVO},
     "datePublished": "2026-12-03", "dateModified": "2026-12-03",
     "inLanguage": "es-EC",
     "author": {"@type": "Organization", "name": "VARGAS LAWYERS S.A.S."},
     "publisher": ORG,
     "image": BASE + "/vargas-logo-full.png"},
    breadcrumb(("Inicio", BASE + "/"), ("Blog", BASE + "/blog.html"),
               ("Disolver y Liquidar Empresa", BASE + "/" + POST_NUEVO)),
]

for rel, bloques in JSONLD.items():
    p = ROOT / rel
    s = p.read_text(encoding='utf-8', errors='replace')
    if 'application/ld+json' in s:
        cambios.append(('ld-omitido-ya-tiene', rel))
        continue
    io.open(p, 'w', encoding='utf-8', newline='').write(inserta_ld(s, bloques))
    cambios.append(('json-ld', rel))

# ---------- 2. Bloque de articulos relacionados ----------
CSS = ('margin:0 0 12px;font-size:1rem;font-weight:600;'
       'color:var(--color-primary,#0b2545)')

for f, claves in RELACIONADOS.items():
    p = ROOT / f
    s = p.read_text(encoding='utf-8', errors='replace')
    # se regenera en cada corrida: primero se quita el bloque anterior
    s = re.sub(r'\n\s*<section id="articulos-relacionados".*?</section>\n', '\n',
               s, flags=re.S)
    elegidos = []
    for k in claves:
        for rel, tit in POSTS.items():
            if k in rel and rel not in [e[0] for e in elegidos]:
                elegidos.append((rel, tit))
                break
    if not elegidos:
        cambios.append(('sin-posts-publicados', f))
        continue
    lis = '\n'.join(
        '                    <li style="margin:0 0 10px"><a href="%s" style="color:inherit;text-decoration:none;border-bottom:1px solid currentColor">%s</a></li>'
        % (rel, tit) for rel, tit in elegidos)
    bloque = (
        '\n    <section id="articulos-relacionados" style="padding:64px 0;background:var(--color-surface,#f6f8fa)">\n'
        '        <div class="container">\n'
        '            <div class="section-header">\n'
        '                <h2 class="section-title">Guías relacionadas</h2>\n'
        '                <p class="section-subtitle">Artículos prácticos sobre este tema, escritos por nuestro equipo.</p>\n'
        '            </div>\n'
        '            <nav aria-label="Artículos relacionados">\n'
        '                <ul style="list-style:none;padding:0;margin:0;columns:2;column-gap:48px">\n'
        + lis + '\n'
        '                </ul>\n'
        '            </nav>\n'
        '            <p style="margin-top:24px"><a href="blog.html" style="font-weight:600">Ver todo el blog legal &rarr;</a></p>\n'
        '        </div>\n'
        '    </section>\n')
    m = re.search(r'\n\s*<footer', s, re.I)
    if not m:
        cambios.append(('sin-footer', f))
        continue
    s = s[:m.start()] + bloque + s[m.start():]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    cambios.append(('relacionados+%d' % len(elegidos), f))

# ---------- 3. index.html: twitter property -> name ----------
p = ROOT / 'index.html'
s = p.read_text(encoding='utf-8', errors='replace')
n = s.count('property="twitter:')
if n:
    s = s.replace('property="twitter:', 'name="twitter:')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    cambios.append(('twitter-name x%d' % n, 'index.html'))

print('%d cambios' % len(cambios))
for tipo, f in cambios:
    print('   %-24s %s' % (tipo, f))
