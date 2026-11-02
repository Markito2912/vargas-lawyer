"""Fase 1 de conversion: un solo telefono clicable, WhatsApp prellenado,
flotante donde falta, barra fija movil y schema de paginas de ciudad.

Idempotente: re-ejecutarlo no cambia nada. Uso: python scripts/conversion_fase1.py
"""
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
WA = "https://wa.me/593985899525"
TEL = "tel:+593985899525"
PHONE = "+593 98 589 9525"
STICKY_MARK = "<!-- barra-movil -->"
SKIP = {"404.html"}

AREAS = {
    "familia.html": "familia",
    "laboral.html": "laboral",
    "civil.html": "civil",
    "societario.html": "societario",
    "constitucional.html": "constitucional",
    "inquilinato.html": "inquilinato",
    "notarial.html": "notarial",
    "propiedad-intelectual.html": "propiedad intelectual",
    "abogados-en-santo-domingo.html": "Santo Domingo",
    "abogados-en-la-concordia.html": "La Concordia",
    "abogados-en-el-carmen.html": "El Carmen",
    "calculadora-liquidacion.html": "liquidación laboral",
    "cobro-de-deudas-santo-domingo.html": "cobro de deudas",
    "legalizacion-terrenos-santo-domingo.html": "legalización de terrenos",
    "herencias-posesion-efectiva-santo-domingo.html": "herencias",
    "contratos-arriendos-santo-domingo.html": "contratos y arriendos",
}
SANTO_DOMINGO_GEO = ("-0.252000", "-79.174000")

ICON_PHONE = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
              '<path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 0 0-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83'
              'l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99'
              ' 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/></svg>')


def h1_text(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    if not m:
        return ""
    text = re.sub(r"<[^>]+>", "", m.group(1))
    return re.sub(r"\s+", " ", text).strip()


def message_for(rel, html):
    name = Path(rel).name
    if name in AREAS:
        return f"Hola, vengo de vargaslawyer.com ({AREAS[name]}). Mi caso es: "
    if rel.startswith("blog/posts/") or (name.startswith("blog-") and name != "blog.html"):
        topic = h1_text(html)[:90]
        if topic:
            return f"Hola, leí su guía «{topic}» en vargaslawyer.com y quiero consultar mi caso: "
    return "Hola, vengo de vargaslawyer.com. Mi caso es: "


def wa_url(msg):
    return f"{WA}?text={quote(msg)}"


def fix_phones(html):
    # Numero secundario retirado: solo queda el oficial.
    html = re.sub(r"\+593 98 589 9525\s*<br>\s*\+593 98 993 8769", PHONE, html)
    html = html.replace("+593 98 993 8769", PHONE).replace("+593989938769", "+593985899525")
    # Telefono como texto (fuera de un enlace) -> tel: clicable.
    return re.sub(
        r"(<(?!a\b)[a-z0-9]+\b[^>]*>)(\s*(?:📱 )?)\+593 98 589 9525(\s*</)",
        rf'\1\2<a href="{TEL}">{PHONE}</a>\3',
        html,
    )


def prefill_whatsapp(html, msg):
    return html.replace(f'href="{WA}"', f'href="{wa_url(msg)}"')


def float_block(template, msg):
    return re.sub(r'href="[^"]*"', f'href="{wa_url(msg)}"', template, count=1)


def sticky_bar(msg):
    return (f'\n    {STICKY_MARK}\n'
            f'    <nav class="mobile-sticky-bar" aria-label="Contacto rápido">\n'
            f'        <a href="{TEL}" class="sticky-bar-btn call-btn" data-cta="sticky">{ICON_PHONE}<span>Llamar</span></a>\n'
            f'        <a href="{wa_url(msg)}" class="sticky-bar-btn whatsapp-btn" target="_blank" rel="noopener" data-cta="sticky">'
            f'<span>WhatsApp</span></a>\n'
            f'    </nav>\n')


def fix_city_schema(html, name):
    def edit(block):
        block = re.sub(r',\s*"aggregateRating"\s*:\s*\{[^{}]*\}', "", block)
        if name in ("abogados-en-la-concordia.html", "abogados-en-el-carmen.html"):
            block = re.sub(r'("latitude"\s*:\s*")[^"]*"', rf'\g<1>{SANTO_DOMINGO_GEO[0]}"', block)
            block = re.sub(r'("longitude"\s*:\s*")[^"]*"', rf'\g<1>{SANTO_DOMINGO_GEO[1]}"', block)
        json.loads(block)  # falla en voz alta si el JSON-LD queda roto
        return block

    return re.sub(
        r'(<script type="application/ld\+json">)(.*?)(</script>)',
        lambda m: m.group(1) + edit(m.group(2)) + m.group(3),
        html,
        flags=re.S,
    )


OG_IMAGE = "https://vargaslawyer.com/og-vargas-lawyers.jpg"
BASE = "https://vargaslawyer.com/"


def fix_og_image(html):
    # Al compartir en redes se veia solo el logo: foto real del equipo 1200x630.
    return re.sub(r'(<meta\s+(?:property="og:image"|name="twitter:image")\s+content=")'
                  r'https://vargaslawyer\.com/vargas-logo(?:-full)?\.png(")',
                  rf"\g<1>{OG_IMAGE}\2", html)


def add_breadcrumb(html, rel):
    # Migas de pan para Google en las paginas que no las tienen.
    if "BreadcrumbList" in html or rel == "index.html":
        return html
    canon = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
    if not canon:
        return html
    name = h1_text(html) or re.split(r"\s[|-]\s", re.search(r"<title>(.*?)</title>", html, re.S).group(1))[0]
    items = [("Inicio", BASE)]
    if rel.startswith("blog/posts/") or (rel.startswith("blog-") and rel != "blog.html"):
        items.append(("Blog", BASE + "blog.html"))
    items.append((name.strip(), canon.group(1)))
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(items, 1)]}
    tag = ('    <script type="application/ld+json">\n    '
           + json.dumps(data, ensure_ascii=False, indent=4).replace("\n", "\n    ")
           + "\n    </script>\n")
    return html.replace("</head>", tag + "</head>", 1)


CALC_CTA = ('\n                    <a href="{url}" class="btn btn-primary calc-cta" target="_blank" rel="noopener" '
            'data-cta="calculadora">¿Te despidieron? Revisamos tu liquidación por WhatsApp</a>')


def main():
    template = re.search(r'<a [^>]*class="whatsapp-float"[\s\S]*?</a>',
                         (ROOT / "familia.html").read_text(encoding="utf-8")).group(0)
    changed = 0
    pages = [p for p in ROOT.glob("*.html")] + list((ROOT / "blog" / "posts").glob("*.html"))
    for path in pages:
        rel = path.relative_to(ROOT).as_posix()
        if path.name in SKIP:
            continue
        # bytes -> str para conservar los finales de linea originales (CRLF/LF)
        html = original = path.read_bytes().decode("utf-8")
        msg = message_for(rel, html)

        html = fix_phones(html)
        html = prefill_whatsapp(html, msg)
        if 'class="whatsapp-float' not in html and "whatsapp-float" not in html:
            html = html.replace("</body>", f"    {float_block(template, msg)}\n</body>", 1)
        if STICKY_MARK not in html:
            html = html.replace("</body>", sticky_bar(msg) + "</body>", 1)
        html = fix_og_image(html)
        html = add_breadcrumb(html, rel)
        if path.name.startswith("abogados-en-"):
            html = fix_city_schema(html, path.name)
        if path.name == "calculadora-liquidacion.html" and "calc-cta" not in html:
            html = re.sub(r'(<p class="result-disclaimer">[\s\S]*?</p>)',
                          lambda m: m.group(1) + CALC_CTA.format(url=wa_url(msg)), html, count=1)

        if html != original:
            path.write_bytes(html.encode("utf-8"))
            changed += 1
    print(f"{changed} paginas modificadas")


if __name__ == "__main__":
    main()
