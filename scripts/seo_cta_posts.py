# -*- coding: utf-8 -*-
"""Anade a cada post un bloque de cierre que enlaza a su pagina de servicio.

Por que: 30 de los 59 posts no enlazaban a ninguna pagina de servicio. Solo
apuntaban a blog.html. Eso desperdicia el enlazado interno (el cluster tematico
no se cierra) y tambien la conversion: el lector termina el articulo y no tiene
a donde ir.

Es idempotente: borra el bloque anterior y lo vuelve a escribir en cada corrida.

Uso:  python scripts/seo_cta_posts.py
"""

from __future__ import annotations

import io
import pathlib
import re
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARCA = 'cta-servicio'

# (pagina de servicio, etiqueta, claves de slug)
SERVICIOS = [
    # Paginas civiles por caso (nov 2026). Van primero porque gana la primera
    # clave: 'usucapion-prescripcion' debe caer en terrenos, no en cobro.
    ('legalizacion-terrenos-santo-domingo.html', 'Legalización de Terrenos',
     ['usucapion']),
    ('cobro-de-deudas-santo-domingo.html', 'Cobro de Deudas',
     ['prescripcion-deudas', 'juicio-ejecutivo', 'letra-cambio', 'prestamo']),
    ('herencias-posesion-efectiva-santo-domingo.html', 'Herencias y Posesión Efectiva',
     ['herencias']),
    ('contratos-arriendos-santo-domingo.html', 'Contratos y Arriendos',
     ['contrato-arriendo', 'arrendamiento', 'incumplimiento', 'nulidad']),
    ('laboral.html', 'Derecho Laboral',
     ['despido', 'finiquito', 'horas-extra', 'vacaciones', 'acoso-laboral',
      'trabajador-domestico', 'contrato-prueba', 'jubilacion-patronal', 'decimo',
      'maternidad', 'liquidacion-laboral', 'pymes-blindaje',
      'prestacion-servicios-profesionales']),
    ('familia.html', 'Derecho de Familia',
     ['pension-alimenticia', 'divorcio', 'tenencia', 'sociedad-conyugal',
      'union-de-hecho', 'reconocimiento-hijo', 'violencia-intrafamiliar',
      'adopcion', 'salida-menor']),
    ('societario.html', 'Derecho Societario',
     ['constituir-empresa', 'junta-general', 'estatutos', 'representante-legal',
      'disolver-empresa', 'liquidacion-companias', 'sas-constitucion']),
    ('propiedad-intelectual.html', 'Propiedad Intelectual',
     ['patente', 'derechos-autor', 'marca-comercial', 'registro-marca', 'senadi']),
    ('constitucional.html', 'Derecho Constitucional',
     ['habeas-corpus', 'habeas-data', 'accion-proteccion']),
    ('inquilinato.html', 'Inquilinato y Arrendamiento',
     ['contrato-arriendo', 'arrendamiento', 'inquilinato']),
    ('notarial.html', 'Servicios Notariales',
     ['testamento', 'herencias', 'divorcio-notarial', 'compraventa-inmueble',
      'permiso-notarial']),
    ('civil.html', 'Derecho Civil',
     ['prescripcion', 'incumplimiento', 'nulidad', 'prestamo', 'dano-moral',
      'usucapion', 'compraventa', 'juicio-ejecutivo', 'letra-cambio', 'consumidor',
      'mediacion', 'responsabilidad-medica', 'civil']),
]

FRASE = {
    'legalizacion-terrenos-santo-domingo.html': 'Si tienes un terreno sin escrituras, revisamos si procede la prescripción y cómo inscribirlo.',
    'cobro-de-deudas-santo-domingo.html': 'Si te deben dinero, revisamos tus documentos y te decimos si conviene demandar.',
    'herencias-posesion-efectiva-santo-domingo.html': 'Si hay una herencia por resolver, te guiamos en la posesión efectiva y la partición.',
    'contratos-arriendos-santo-domingo.html': 'Si el problema es un contrato o un arriendo, lo revisamos y te decimos qué puedes exigir.',
    'laboral.html': 'Si tu caso es laboral, revisamos tu situación y te decimos qué te corresponde.',
    'familia.html': 'Si tu caso es de familia, te acompañamos en el proceso de principio a fin.',
    'societario.html': 'Si es un tema de tu empresa, lo resolvemos con respaldo jurídico completo.',
    'propiedad-intelectual.html': 'Si necesitas proteger tu marca, invento u obra, nos encargamos del trámite.',
    'constitucional.html': 'Si hay derechos vulnerados, actuamos con las garantías que da la Constitución.',
    'inquilinato.html': 'Si el conflicto es de arriendo, lo resolvemos sea que arriendes o seas propietario.',
    'notarial.html': 'Si necesitas el trámite notarial, te decimos exactamente qué documentos hacen falta.',
    'civil.html': 'Si es un conflicto civil o una deuda por cobrar, evaluamos tu caso sin costo.',
}


def servicio_de(rel):
    bajo = rel.lower()
    for pagina, etiqueta, claves in SERVICIOS:
        if any(k in bajo for k in claves):
            return pagina, etiqueta
    return None, None


def bloque(prefijo, pagina, etiqueta, rel):
    """prefijo: '' para posts en la raiz, '../../' para blog/posts/."""
    # El tema del mensaje de WhatsApp sale del H1 del post (con tildes, legible).
    html = (ROOT / rel).read_bytes().decode('utf-8')
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    tema = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h1.group(1))).strip()[:90] if h1 else etiqueta

    whatsapp_message = f"Hola, leí su guía «{tema}» en vargaslawyer.com y quiero consultar mi caso: "
    whatsapp_url = 'https://wa.me/593985899525?text=' + quote(whatsapp_message)

    return (
        '\n    <section class="%s" style="padding:64px 0;background:#0d1420">\n'
        '        <div class="container" style="max-width:820px">\n'
        '            <p style="margin:0 0 12px;font-size:.75rem;font-weight:700;'
        'letter-spacing:.08em;text-transform:uppercase;color:var(--color-primary,#3ea8f4)">'
        '¿Necesitas ayuda con esto?</p>\n'
        '            <h2 style="font-family:var(--font-heading);font-size:1.75rem;'
        'margin:0 0 16px">%s en Santo Domingo</h2>\n'
        '            <p style="margin:0 0 24px;line-height:1.7;opacity:.85">%s</p>\n'
        '            <p style="margin:0"><a class="service-link" href="%s" target="_blank" '
        'data-cta="post" data-area="%s" style="font-weight:600">'
        'Consultar por WhatsApp <span aria-hidden="true">&rarr;</span></a>'
        '<span style="opacity:.4;margin:0 14px">·</span>'
        '<a class="service-link" href="%s%s" style="font-weight:600">Ver %s <span aria-hidden="true">&rarr;</span></a></p>\n'
        '        </div>\n'
        '    </section>\n'
    ) % (MARCA, etiqueta, FRASE[pagina], whatsapp_url, etiqueta, prefijo, pagina, etiqueta.lower())


def main() -> int:
    posts = sorted(list((ROOT / 'blog' / 'posts').glob('*.html'))
                   + list(ROOT.glob('blog-*.html')))
    puestos = []
    sin_match = []

    for p in posts:
        rel = p.relative_to(ROOT).as_posix()
        pagina, etiqueta = servicio_de(rel)
        if not pagina:
            sin_match.append(rel)
            continue

        s = original = p.read_text(encoding='utf-8', errors='replace')
        # regenerable: fuera el bloque anterior
        # el bloque trae su propio \n inicial y final: reemplazar por '' (no por '\n')
        # para no sumar una linea en blanco en cada corrida
        s = re.sub(r'\n\s*<section class="%s".*?</section>\n' % MARCA, '', s, flags=re.S)

        prefijo = '../../' if rel.startswith('blog/posts/') else ''
        m = re.search(r'\n\s*<footer', s, re.I)
        if not m:
            continue
        s = s[:m.start()] + bloque(prefijo, pagina, etiqueta, rel) + s[m.start():]

        if s != original:
            io.open(p, 'w', encoding='utf-8', newline='').write(s)
            puestos.append((rel, pagina))

    print('%d posts con bloque de cierre hacia su servicio' % len(puestos))
    from collections import Counter
    for pagina, n in Counter(v for _, v in puestos).most_common():
        print('   %-28s %d posts' % (pagina, n))
    if sin_match:
        print('\nsin servicio asignado (%d): %s' % (len(sin_match), ', '.join(sin_match[:8])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
