"""Genera las paginas de servicio civil por caso a partir de la plantilla civil.html.

Cada pagina conserva cabecera, menu, pie, estilos y GTM de civil.html y cambia
metadatos, hero, tarjetas, lista, preguntas frecuentes y guias relacionadas.
Idempotente: reescribe las paginas completas en cada corrida.

Uso: python scripts/crear_paginas_civiles.py
"""
import html as H
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://vargaslawyer.com/"
WA = "https://wa.me/593985899525?text="

PAGINAS = [
    {
        "archivo": "cobro-de-deudas-santo-domingo.html",
        "area": "cobro de deudas",
        "title": "Cobro de Deudas, Pagarés y Letras de Cambio en Santo Domingo",
        "desc": "¿Le deben con pagaré, letra de cambio o cheque? Revisamos sus documentos y la solvencia del deudor y reclamamos el pago por vía judicial en Santo Domingo.",
        "keywords": "cobro de deudas santo domingo, juicio ejecutivo, cobrar pagaré, letra de cambio, abogado civil santo domingo",
        "servicio": "Cobro judicial de deudas",
        "badge": "Derecho Civil · Cobranzas",
        "h1": ("Cobro de Deudas en Santo Domingo:", "Pagarés, Letras y Cheques"),
        "sub": "Si tiene un documento que prueba la deuda, la ley le da un camino directo para cobrar. Revisamos su caso y le decimos con claridad si conviene demandar.",
        "cta": "Consultar mi deuda",
        "tarjetas_titulo": ("Cómo recuperamos su dinero", "Elegimos la vía según el documento que tenga"),
        "tarjetas": [
            ("Juicio ejecutivo", "Para pagarés, letras de cambio, cheques y otros títulos ejecutivos. Es la vía más directa para exigir el pago."),
            ("Procedimiento monitorio", "Para deudas sin título ejecutivo, como facturas o cánones impagos, cuando existe un documento que respalde lo que le deben."),
            ("Medidas cautelares", "Pedimos al juez retener bienes o prohibir su venta para asegurar que, al final del proceso, haya con qué pagarle."),
        ],
        "lista_titulo": "¿Qué necesita para empezar?",
        "lista_intro": "En el cobro de deudas el tiempo cuenta. Mientras antes revisemos su caso, más opciones hay. Tenga a mano:",
        "lista_h3": "Documentos para la consulta",
        "lista": ["El documento original de la deuda (pagaré, letra, cheque o contrato)",
                  "Nombre, cédula y domicilio actual del deudor",
                  "Comprobantes de abonos o pagos parciales, si los hubo",
                  "Bienes que conozca del deudor (vehículos, inmuebles, cuentas)"],
        "caja_titulo": "Antes de demandar",
        "caja_texto": "Revisamos si el documento cumple los requisitos y si la deuda no ha prescrito, porque cada documento tiene un plazo para cobrarse. Si no hay forma real de cobrar, se lo decimos.",
        "caja_cta": "Revisar mi documento",
        "faq": [
            ("¿Qué documentos sirven para un juicio ejecutivo?",
             "Entre otros, el pagaré a la orden, la letra de cambio, el cheque protestado y los demás documentos que la ley reconoce como títulos ejecutivos. Si su documento no lo es, puede haber otra vía, como el procedimiento monitorio."),
            ("¿Una deuda puede prescribir?",
             "Sí. Las acciones de cobro tienen plazos de prescripción que dependen del tipo de documento. Por eso conviene revisar las fechas cuanto antes y no dejar pasar el tiempo."),
            ("¿Y si el deudor no tiene bienes a su nombre?",
             "Antes de demandar revisamos qué bienes tiene. Si no hay nada que embargar, se lo decimos con honestidad para que no invierta en un juicio que no le devolverá su dinero."),
        ],
        "guias": ["blog-cobro-letra-cambio-pagare.html",
                  "blog/posts/2026-03-19-prescripcion-deudas-ecuador.html",
                  "blog/posts/2026-06-11-prestamo-entre-particulares-documento-legal-ecuador.html"],
    },
    {
        "archivo": "legalizacion-terrenos-santo-domingo.html",
        "area": "legalización de terrenos",
        "title": "Legalizar un Terreno en Santo Domingo | Usucapión y Escrituras",
        "desc": "¿Lleva años en un terreno sin escrituras? Le ayudamos a legalizarlo por prescripción adquisitiva (usucapión) e inscribirlo en el Registro de la Propiedad.",
        "keywords": "legalizar terreno santo domingo, usucapión, prescripción adquisitiva de dominio, escrituras terreno, abogado civil santo domingo",
        "servicio": "Legalización de terrenos y prescripción adquisitiva",
        "badge": "Derecho Civil · Inmuebles",
        "h1": ("Legalización de Terrenos", "en Santo Domingo"),
        "sub": "Si ha poseído un terreno o una finca durante años como dueño, la ley le permite pedir que se le reconozca la propiedad. Le explicamos si su caso califica y qué pruebas hacen falta.",
        "cta": "Consultar mi terreno",
        "tarjetas_titulo": ("Del terreno sin papeles a la escritura", "Le acompañamos en todo el proceso"),
        "tarjetas": [
            ("Prescripción adquisitiva", "Demanda para que un juez le declare propietario por haber poseído el inmueble el tiempo que exige la ley, de forma pública, pacífica y continua."),
            ("Revisión de títulos", "Analizamos los certificados del Registro de la Propiedad y del catastro municipal para saber quién figura como dueño y qué gravámenes hay."),
            ("Inscripción", "Con la sentencia o la escritura, la inscribimos en el Registro de la Propiedad para que el terreno quede legalmente a su nombre."),
        ],
        "lista_titulo": "¿Qué pruebas se necesitan?",
        "lista_intro": "En la usucapión hay que demostrar la posesión. Estas pruebas suelen ser las más importantes:",
        "lista_h3": "Pruebas de la posesión",
        "lista": ["Pagos del impuesto predial, de servicios o de mejoras hechas en el terreno",
                  "Vecinos o testigos que conozcan su posesión durante esos años",
                  "Certificado del Registro de la Propiedad del inmueble",
                  "Planos o levantamiento del terreno, si los tiene"],
        "caja_titulo": "Antes de demandar",
        "caja_texto": "Verificamos cuántos años de posesión puede probar y contra quién hay que dirigir la demanda. Un error en ese punto puede hacer perder años de trámite.",
        "caja_cta": "Revisar mi caso",
        "faq": [
            ("¿Cuántos años necesito para la usucapión?",
             "Depende del tipo de prescripción. La extraordinaria exige 15 años de posesión. La ordinaria exige 5 años para inmuebles, pero además requiere justo título y buena fe."),
            ("¿Sirve para fincas y terrenos rurales?",
             "Sí. La prescripción adquisitiva aplica tanto a inmuebles urbanos como rurales, siempre que se cumplan los requisitos de posesión que exige la ley."),
            ("¿Qué pasa si el dueño que figura en el registro ya falleció?",
             "La demanda se dirige contra sus herederos. Le ayudamos a identificarlos y a citarlos conforme a la ley."),
        ],
        "guias": ["blog/posts/2026-04-03-usucapion-prescripcion-adquisitiva-ecuador.html",
                  "blog/posts/2026-05-12-compraventa-inmueble-ecuador-escritura-publica.html"],
    },
    {
        "archivo": "herencias-posesion-efectiva-santo-domingo.html",
        "area": "herencias",
        "title": "Herencias y Posesión Efectiva en Santo Domingo | Abogados",
        "desc": "Posesión efectiva, partición de bienes y testamentos en Santo Domingo. Le guiamos para que los bienes queden a nombre de los herederos y sin conflictos.",
        "keywords": "posesión efectiva santo domingo, herencias santo domingo, partición de bienes, testamento, abogado civil santo domingo",
        "servicio": "Herencias y posesión efectiva",
        "badge": "Derecho Civil · Sucesiones",
        "h1": ("Herencias y Posesión Efectiva", "en Santo Domingo"),
        "sub": "Cuando fallece un familiar, los bienes no pasan solos a los herederos. Le acompañamos en cada trámite para que la herencia quede en orden y sin conflictos.",
        "cta": "Consultar mi herencia",
        "tarjetas_titulo": ("Trámites de herencia", "Del fallecimiento a los bienes a su nombre"),
        "tarjetas": [
            ("Posesión efectiva", "Trámite que reconoce a los herederos y les permite disponer de los bienes. Si no hay conflicto entre ellos, puede hacerse en notaría."),
            ("Partición de bienes", "Si los herederos están de acuerdo, la partición puede hacerse ante notario. Si no, se resuelve en juicio. Le asesoramos en ambos casos."),
            ("Testamentos", "Redacción y revisión de testamentos para que su voluntad se cumpla y evitar disputas entre familiares."),
        ],
        "lista_titulo": "¿Qué documentos se necesitan?",
        "lista_intro": "Para iniciar la posesión efectiva suelen pedirse estos documentos:",
        "lista_h3": "Documentos para la consulta",
        "lista": ["Partida de defunción del fallecido",
                  "Partidas de nacimiento o matrimonio que prueben el parentesco",
                  "Cédulas de los herederos",
                  "Certificados del Registro de la Propiedad de los inmuebles, si los hay"],
        "caja_titulo": "Después de la posesión efectiva",
        "caja_texto": "Hay obligaciones tributarias y de inscripción en el Registro de la Propiedad que conviene cumplir a tiempo. Le decimos cuáles aplican a su caso.",
        "caja_cta": "Revisar mi caso",
        "faq": [
            ("¿La posesión efectiva se hace en notaría o en juzgado?",
             "Si no hay controversia entre los herederos, puede hacerse en una notaría, que suele ser la vía más rápida. Si hay desacuerdo o dudas sobre quiénes son los herederos, se tramita judicialmente."),
            ("¿Qué pasa si un heredero no quiere vender ni repartir?",
             "Cualquiera de los herederos puede pedir la partición judicial. Antes intentamos un acuerdo, porque suele ser más rápido y menos costoso para la familia."),
            ("¿Hace falta posesión efectiva aunque haya testamento?",
             "Sí. Aunque exista testamento, los herederos necesitan la posesión efectiva para poder disponer de los bienes."),
        ],
        "guias": ["blog-herencias-posesion-efectiva.html",
                  "blog-herencias-testamentos-ecuador.html"],
    },
    {
        "archivo": "contratos-arriendos-santo-domingo.html",
        "area": "contratos y arriendos",
        "title": "Contratos y Arriendo de Locales en Santo Domingo | Abogados",
        "desc": "Redacción y revisión de contratos de arriendo de locales, compraventa y servicios en Santo Domingo. Reclamos por incumplimiento y cobro de arriendos.",
        "keywords": "abogado contratos santo domingo, arriendo local comercial, contrato de arrendamiento, incumplimiento de contrato, abogado civil santo domingo",
        "servicio": "Contratos civiles y arrendamientos",
        "badge": "Derecho Civil · Contratos",
        "h1": ("Contratos y Arriendos", "en Santo Domingo"),
        "sub": "Un contrato bien hecho evita juicios. Redactamos y revisamos sus contratos, y si la otra parte incumple, reclamamos lo que le corresponde.",
        "cta": "Consultar mi contrato",
        "tarjetas_titulo": ("Contratos que le protegen", "Antes de firmar y cuando hay incumplimiento"),
        "tarjetas": [
            ("Arriendo de locales", "Contratos que protegen al arrendador y al arrendatario: plazo, garantía, mejoras, renovación y terminación anticipada."),
            ("Compraventas y promesas", "Revisión de promesas de compraventa y contratos de inmuebles y vehículos antes de firmar, para evitar sorpresas."),
            ("Incumplimiento", "Si la otra parte no cumple, reclamamos el cumplimiento o la terminación del contrato con indemnización de daños y perjuicios."),
        ],
        "lista_titulo": "Antes de firmar, revise",
        "lista_intro": "La mayoría de los conflictos que llegan a juicio empiezan con un contrato mal redactado. Fíjese en esto:",
        "lista_h3": "Puntos clave de un contrato",
        "lista": ["Quién firma y si tiene facultades para hacerlo (por ejemplo, el representante legal)",
                  "Plazo, precio y forma de pago escritos con claridad",
                  "Garantías y multas por incumplimiento",
                  "Cómo se termina el contrato y quién asume cada gasto"],
        "caja_titulo": "Revisión antes de firmar",
        "caja_texto": "Envíenos el borrador por WhatsApp y le indicamos qué cláusulas le ponen en riesgo y cómo corregirlas.",
        "caja_cta": "Enviar mi contrato",
        "faq": [
            ("¿El contrato de arriendo tiene que estar por escrito?",
             "Siempre es lo recomendable: un contrato escrito deja claras las condiciones y facilita reclamar si hay incumplimiento. Según el caso, la ley exige además requisitos de forma que revisamos con usted."),
            ("¿Qué hago si el inquilino de mi local no paga?",
             "Se pueden reclamar los arriendos atrasados y, según el contrato y la ley, pedir la terminación del arriendo y la desocupación del local."),
            ("¿Pueden revisar un contrato que ya firmé?",
             "Sí. Le explicamos qué obligaciones asumió, qué riesgos tiene y qué opciones hay si la otra parte incumple."),
        ],
        "guias": ["blog/posts/2026-06-23-arrendamiento-local-comercial-ecuador-clausulas.html",
                  "blog/posts/2026-03-05-contrato-arriendo-ecuador-clausulas.html",
                  "blog/posts/2026-03-16-incumplimiento-contrato-ecuador-pruebas.html"],
    },
]

FAQ_ICON = ('<svg class="faq-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">\n'
            '                            <path d="M19 9L12 16L5 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"\n'
            '                                stroke-linejoin="round" />\n'
            '                        </svg>')


def e(t):
    return H.escape(t, quote=True)


def h1_de(rel):
    s = (ROOT / rel).read_text(encoding="utf-8")
    t = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def meta(s, attr, val):
    pat = re.compile(r'(<meta\s+(?:name|property)="%s"\s+content=")[^"]*(")' % re.escape(attr))
    assert pat.search(s), attr
    return pat.sub(lambda m: m.group(1) + e(val) + m.group(2), s, count=1)


def construir(tpl, p):
    url = BASE + p["archivo"]
    wa = WA + quote(f"Hola, vengo de vargaslawyer.com ({p['area']}). Mi caso es: ")
    s = tpl
    # --- head
    s = meta(s, "description", p["desc"])
    s = meta(s, "keywords", p["keywords"])
    s = meta(s, "og:url", url)
    s = meta(s, "og:title", p["title"])
    s = meta(s, "og:description", p["desc"])
    s = meta(s, "twitter:title", p["title"])
    s = meta(s, "twitter:description", p["desc"])
    s = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{url}"', s, count=1)
    s = re.sub(r"<title>.*?</title>", lambda m: f"<title>{e(p['title'])}</title>", s, count=1, flags=re.S)
    servicio = {"@context": "https://schema.org", "@type": "Service", "serviceType": p["servicio"],
                "provider": {"@type": "LegalService", "name": "VARGAS LAWYERS S.A.S.",
                             "image": "https://vargaslawyer.com/vargas-logo.png",
                             "telephone": "+593985899525", "url": BASE,
                             "address": {"@type": "PostalAddress", "addressLocality": "Santo Domingo",
                                         "addressRegion": "Santo Domingo de los Tsáchilas", "addressCountry": "EC"}},
                "areaServed": [{"@type": "City", "name": n} for n in ("Santo Domingo", "La Concordia", "El Carmen")],
                "description": p["desc"]}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]}
    ld = lambda d: ('<script type="application/ld+json">\n    '
                    + json.dumps(d, ensure_ascii=False, indent=4).replace("\n", "\n    ") + "\n    </script>")
    bloques = list(re.finditer(r'<script type="application/ld\+json">.*?</script>', s, re.S))
    # el primero es el Service de la plantilla; el BreadcrumbList lo regenera conversion_fase1
    for b in reversed(bloques[1:]):
        if "BreadcrumbList" in b.group(0):
            s = s[:b.start()] + s[b.end():]
    b = re.search(r'<script type="application/ld\+json">.*?</script>', s, re.S)
    s = s[:b.start()] + ld(servicio) + "\n    " + ld(faq) + s[b.end():]
    # --- hero
    s = re.sub(r'(<span class="hero-badge">).*?(</span>)', lambda m: m.group(1) + e(p["badge"]) + m.group(2), s, count=1, flags=re.S)
    s = re.sub(r'(<h1 class="hero-title"[^>]*>).*?(</h1>)',
               lambda m: f'{m.group(1)}\n                    {e(p["h1"][0])}<br>\n                    <span class="gradient-text">{e(p["h1"][1])}</span>\n                {m.group(2)}',
               s, count=1, flags=re.S)
    s = re.sub(r'(<p class="hero-subtitle">).*?(</p>)', lambda m: f"{m.group(1)}\n                    {e(p['sub'])}\n                {m.group(2)}", s, count=1, flags=re.S)
    s = re.sub(r'(<div class="hero-cta">\s*<a [^>]*>\s*<span>).*?(</span>)', lambda m: m.group(1) + e(p["cta"]) + m.group(2), s, count=1, flags=re.S)
    # --- tarjetas (se conservan los iconos de la plantilla)
    sec = re.search(r'<section class="services" style="padding-top: 80px;">.*?</section>', s, re.S)
    t = sec.group(0)
    t = re.sub(r'(<h2 class="section-title">).*?(</h2>)', lambda m: m.group(1) + e(p["tarjetas_titulo"][0]) + m.group(2), t, count=1, flags=re.S)
    t = re.sub(r'(<p class="section-subtitle">).*?(</p>)', lambda m: m.group(1) + e(p["tarjetas_titulo"][1]) + m.group(2), t, count=1, flags=re.S)
    it = iter(p["tarjetas"])
    def tarjeta(m):
        tit, txt = next(it)
        return f'{m.group(1)}{e(tit)}{m.group(2)}{m.group(3)}\n                        {e(txt)}\n                    {m.group(4)}'
    t = re.sub(r'(<h3 class="service-title">).*?(</h3>)(\s*<p class="service-description">).*?(</p>)', tarjeta, t, flags=re.S)
    s = s[:sec.start()] + t + s[sec.end():]
    # --- lista y caja
    sec = re.search(r'<section style="padding: 80px 0; background: var\(--color-background\);">.*?</section>', s, re.S)
    t = sec.group(0)
    t = re.sub(r'(<h2 class="section-title">).*?(</h2>)', lambda m: m.group(1) + e(p["lista_titulo"]) + m.group(2), t, count=1, flags=re.S)
    t = re.sub(r'(<p class="contact-description">).*?(</p>)', lambda m: f"{m.group(1)}\n                        {e(p['lista_intro'])}\n                    {m.group(2)}", t, count=1, flags=re.S)
    t = re.sub(r'(<div class="checklist-container"[^>]*>\s*<h3[^>]*>).*?(</h3>)', lambda m: m.group(1) + e(p["lista_h3"]) + m.group(2), t, count=1, flags=re.S)
    items = "".join(
        f'\n                            <li style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">\n'
        f'                                <span style="color: var(--color-primary); font-weight: bold;">✓</span> {e(x)}\n'
        f'                            </li>' for x in p["lista"])
    t = re.sub(r'(<ul style="list-style: none; padding: 0; color: #000000;">).*?(\s*</ul>)', lambda m: m.group(1) + items + m.group(2), t, count=1, flags=re.S)
    t = re.sub(r'(<div class="contact-form"[^>]*>\s*<h3[^>]*>).*?(</h3>)', lambda m: m.group(1) + e(p["caja_titulo"]) + m.group(2), t, count=1, flags=re.S)
    t = re.sub(r'(<p style="color: var\(--color-text-muted\); margin-bottom: 30px;">).*?(</p>)', lambda m: f"{m.group(1)}\n                        {e(p['caja_texto'])}\n                    {m.group(2)}", t, count=1, flags=re.S)
    t = re.sub(r'(class="btn btn-primary btn-full">\s*<span>).*?(</span>)', lambda m: m.group(1) + e(p["caja_cta"]) + m.group(2), t, count=1, flags=re.S)
    s = s[:sec.start()] + t + s[sec.end():]
    # --- preguntas frecuentes
    faqs = "".join(
        f'\n                <div class="faq-item">\n                    <button class="faq-question">\n'
        f'                        <span>{e(q)}</span>\n                        {FAQ_ICON}\n                    </button>\n'
        f'                    <div class="faq-answer">\n                        <p>{e(a)}</p>\n                    </div>\n                </div>\n'
        for q, a in p["faq"])
    s = re.sub(r'(<div class="faq-container">).*?(\n\s*</div>\s*</div>\s*</section>)', lambda m: m.group(1) + faqs + m.group(2), s, count=1, flags=re.S)
    # --- guias relacionadas
    cards = "\n".join(
        f'                <article class="service-card">\n'
        f'                    <p style="margin:0 0 12px;font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--color-primary)">Derecho Civil</p>\n'
        f'                    <h3 class="service-title"><a href="{g}" style="color:inherit">{e(h1_de(g))}</a></h3>\n'
        f'                    <a class="service-link" href="{g}">Leer la guía <span aria-hidden="true">&rarr;</span></a>\n'
        f'                </article>\n' for g in p["guias"])
    s = re.sub(r'(<section id="articulos-relacionados"[^>]*>.*?<div class="services-grid">).*?(</div>\s*<p style="text-align:center)',
               lambda m: m.group(1) + "\n" + cards + "            " + m.group(2), s, count=1, flags=re.S)
    # --- todos los WhatsApp de la pagina con el mensaje de este caso
    s = re.sub(r'https://wa\.me/593985899525\?text=[^"]*', wa, s)
    return s


def main():
    tpl = (ROOT / "civil.html").read_bytes().decode("utf-8")
    for p in PAGINAS:
        out = construir(tpl, p)
        assert out.count("<h1") == 1 and p["archivo"] in out
        (ROOT / p["archivo"]).write_bytes(out.encode("utf-8"))
        print("ok", p["archivo"])


if __name__ == "__main__":
    main()
