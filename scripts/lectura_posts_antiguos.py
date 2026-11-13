"""Pasa los posts antiguos al diseno de lectura (.post-lectura de styles-v2.css).

Por que: Marco vio los posts como "una plana de texto dificil de leer". Los 24
posts programados (dic 2026 - feb 2027) ya nacen con ese diseno; este script
adapta los anteriores sin reescribir su contenido.

Que hace, solo en el cuerpo del articulo:
- <article> pasa a class="container post-lectura" (sin estilo en linea).
- Quita el style en linea de los parrafos, titulos y listas del nivel del texto
  (no toca recuadros, tablas, preguntas frecuentes ni el bloque de cierre).
- Parte los parrafos de mas de 70 palabras por la frase mas cercana a la mitad.
- Pone id a cada h2 y un indice "En este articulo" antes del primero.
- Aviso de WhatsApp antes de la cuarta seccion si hay cinco o mas.
- El h1 se ajusta al ancho del movil.

Idempotente: un post que ya tiene post-lectura se salta.
"""
import io
import pathlib
import re
import sys
import unicodedata
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAG = re.compile(r'<(/?)([a-zA-Z0-9]+)\b([^>]*?)(/?)>')
CONT = {'div', 'table', 'details', 'blockquote', 'form', 'aside', 'figure', 'nav'}
TEXTO = {'p', 'h2', 'h3', 'ul', 'ol'}
ABREV = re.compile(r'(?:\b(?:art|arts|núm|num|inc|lit|Ab|Dr|Dra|Sr|Sra|Ud|etc|ej|S\.A|S\.A\.S)|\b[A-ZÁÉÍÓÚ])\.$')
MOVIL = ("        <script>if (window.innerWidth < 768) "
         "document.currentScript.previousElementSibling.removeAttribute('open');</script>\n")


def plano(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


def slug_id(t):
    t = unicodedata.normalize('NFKD', plano(t)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:60]


def sin_style(attrs):
    return re.sub(r'\s+style\s*=\s*("[^"]*"|\'[^\']*\')', '', attrs)


def partir(p_html, max_pal=70):
    if '<br' in p_html or len(plano(p_html).split()) <= max_pal:
        return [p_html]
    cortes = []
    for m in re.finditer(r'(?<=[.?:])\s+(?=[A-ZÁÉÍÓÚÑ¿])', p_html):
        antes = p_html[:m.start()]
        if antes.count('<') != antes.count('>'):
            continue
        if any(antes.count(f'<{t}') != antes.count(f'</{t}>') for t in ('strong', 'a ', 'em', 'b>')):
            continue
        if ABREV.search(antes):
            continue
        cortes.append(m)
    if not cortes:
        return [p_html]
    m = min(cortes, key=lambda c: abs(c.start() - len(p_html) / 2))
    a, b = p_html[:m.start()].strip(), p_html[m.end():].strip()
    if min(len(plano(a).split()), len(plano(b).split())) < 15:
        return [p_html]
    return partir(a, max_pal) + partir(b, max_pal)


def wa(h1):
    msg = f"Hola, leí su guía «{h1[:90]}» en vargaslawyer.com y quiero consultar mi caso: "
    return 'https://wa.me/593985899525?text=' + quote(msg)


def adaptar(s):
    a0 = s.index('<article')
    a_open_end = s.index('>', a0) + 1
    a1 = s.index('</article>', a0)
    inner = s[a_open_end:a1]

    # 1) arbol minimo: a que contenedor pertenece cada etiqueta de texto
    toks = list(TAG.finditer(inner))
    pila = [-1]            # -1 = el propio <article>
    padre = {}             # indice de token -> contenedor
    cierre = {}            # indice de token de apertura -> indice de su cierre
    abiertos = {}          # nombre -> pila de indices abiertos (texto)
    credito = {}
    for i, m in enumerate(toks):
        cl, name = m.group(1), m.group(2).lower()
        if name in CONT:
            if cl:
                if len(pila) > 1:
                    pila.pop()
            else:
                padre[i] = pila[-1]
                pila.append(i)
            continue
        if name in TEXTO or name == 'li':
            if not cl:
                padre[i] = pila[-1]
                abiertos.setdefault(name, []).append(i)
                if name in ('p', 'h2'):
                    credito[pila[-1]] = credito.get(pila[-1], 0) + 1
            elif abiertos.get(name):
                cierre[abiertos[name].pop()] = i
    raiz = max(credito, key=credito.get) if credito else -1

    # 2) ediciones sobre los elementos de texto hijos directos de la raiz
    ed = []                # (inicio, fin, texto nuevo) en coordenadas de inner
    h2s = []
    li_padres = []
    for i, m in enumerate(toks):
        cl, name = m.group(1), m.group(2).lower()
        if cl or name not in TEXTO or padre.get(i) != raiz:
            continue
        attrs = sin_style(m.group(3))
        if name == 'h2':
            fin = cierre.get(i)
            texto = inner[m.end():toks[fin].start()] if fin is not None else ''
            if 'id=' not in attrs:
                hid = slug_id(texto) or f's{len(h2s)}'
                attrs += f' id="{hid}"'
            else:
                hid = re.search(r'id="([^"]+)"', attrs).group(1)
            h2s.append((m.start(), hid, plano(texto)))
        if name == 'p' and i in cierre:
            fin = toks[cierre[i]]
            trozos = partir(inner[m.end():fin.start()].strip())
            if len(trozos) > 1:
                sangria = re.search(r'[ \t]*$', inner[:m.start()]).group(0)
                nuevo = f'\n{sangria}'.join(f'<p{attrs}>{t}</p>' for t in trozos)
                ed.append((m.start(), fin.end(), nuevo))
                continue
        ed.append((m.start(), m.end(), f'<{m.group(2)}{attrs}>'))
        if name in ('ul', 'ol') and i in cierre:
            li_padres.append((m.end(), toks[cierre[i]].start()))
    for ini, fin in li_padres:
        for m in re.finditer(r'<li\b([^>]*)>', inner[ini:fin]):
            if 'style' in m.group(1):
                ed.append((ini + m.start(), ini + m.end(), f'<li{sin_style(m.group(1))}>'))

    # 3) indice y aviso
    h1 = plano(re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S).group(1))
    if len(h2s) >= 3:
        items = ''.join(f'\n                <li><a href="#{hid}">{t}</a></li>' for _, hid, t in h2s)
        indice = ('<details class="post-indice" open>\n'
                  '            <summary>En este artículo</summary>\n'
                  f'            <ol>{items}\n            </ol>\n'
                  '        </details>\n' + MOVIL + '\n        ')
        ed.append((h2s[0][0], h2s[0][0], indice))
    if len(h2s) >= 5:
        aviso = ('<div class="post-aviso">\n'
                 '            <p>¿Tu caso se parece a esto? Cuéntanoslo por WhatsApp y te decimos qué opciones tienes.</p>\n'
                 f'            <a href="{wa(h1)}" target="_blank" rel="noopener" data-cta="post-medio">Escribir por WhatsApp</a>\n'
                 '        </div>\n\n        ')
        ed.append((h2s[3][0], h2s[3][0], aviso))

    # aplicar de atras hacia delante (las inserciones van antes del reemplazo en la misma posicion)
    ed.sort(key=lambda e: (e[0], 0 if e[0] == e[1] else 1), reverse=True)
    nuevo = inner
    for ini, fin, txt in sorted(ed, key=lambda e: (e[0], e[0] != e[1]), reverse=True):
        nuevo = nuevo[:ini] + txt + nuevo[fin:]

    art = sin_style(s[a0 + len('<article'):a_open_end - 1])
    art = re.sub(r'class="([^"]*)"', lambda mm: f'class="{mm.group(1)} post-lectura"', art) \
        if 'class=' in art else art + ' class="container post-lectura"'
    s = s[:a0] + f'<article{art}>' + nuevo + s[a1:]

    # h1 ajustado al movil
    s = re.sub(r'(<h1\b[^>]*style="[^"]*?)font-size:\s*[^;"]+',
               r'\1font-size:clamp(1.65rem,6vw,2.5rem)', s, count=1)
    return s, len(h2s)


def main():
    posts = sorted(list((ROOT / 'blog' / 'posts').glob('*.html')) + list(ROOT.glob('blog-*.html')))
    hechos = []
    for p in posts:
        raw = p.read_bytes().decode('utf-8')
        crlf = '\r\n' in raw
        s = raw.replace('\r\n', '\n')
        m = re.search(r'<article\b[^>]*>', s)
        if not m or 'post-lectura' in m.group(0):
            continue
        s, n = adaptar(s)
        if crlf:
            s = s.replace('\n', '\r\n')
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        hechos.append((p.relative_to(ROOT).as_posix(), n))
    for rel, n in hechos:
        print(f'   {n:2d} secciones  {rel}')
    print(f'{len(hechos)} posts adaptados al diseno de lectura')
    return 0


if __name__ == '__main__':
    sys.exit(main())
