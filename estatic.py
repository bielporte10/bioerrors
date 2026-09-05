"""
Genera tot el que fa que el catàleg es pugui trobar buscant.

El problema que resol. El 2026-09-05 el catàleg sencer vivia dins del
`<script>`: 2.053 caràcters de HTML visible contra 40.552 de JavaScript. Cap
signatura d'error existia com a text llegible. Qui googleja el seu error no
podia arribar aquí, que és exactament el canal amb què es va justificar el
projecte.

La primera versió d'aquest script ho va arreglar a mitges: va publicar les 44
fitxes en una sola pàgina. Però **una pàgina no pot posicionar per 44 errors
diferents**. Competint alhora per "NegativeArraySizeException", "bash\\r: No
such file or directory" i "sort: invalid option -- '@'", no surt bé per cap.

Per això ara genera tres coses:

  e/<error>.html   una pàgina per signatura, amb títol i descripció propis.
                   És la que ha de sortir quan algú busca aquell error concret.
  index.html       la portada passa a ser un índex: etiqueta, una línia i
                   enllaç. Sense duplicar el text de les fitxes, que a Google
                   li compta com a contingut repetit.
  sitemap.xml      les 45 pàgines, per enviar-lo a Search Console.
  robots.txt       obert i apuntant al sitemap.

La font de veritat segueix sent l'array CATALOGUE del JavaScript d'index.html.
Tot això se'n deriva, i es pot tornar a executar tantes vegades com calgui.

Us:
    python estatic.py
"""

import html
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

AQUI = Path(__file__).parent
PAGINA = AQUI / "index.html"
FITXES = AQUI / "e"
BASE = "https://bielporte10.github.io/bioerrors/"
INICI = "<!-- CATALEG-ESTATIC:INICI -->"
FI = "<!-- CATALEG-ESTATIC:FI -->"

AREES = {
    # La pagina es en angles: aquests titols hi surten, no son comentaris.
    "nextflow": "Nextflow", "snakemake": "Snakemake",
    "conda": "conda and environments", "docker": "Containers",
    "data": "Files and formats", "r": "R and Bioconductor",
    "java": "Java", "python": "Python", "cluster": "HPC and schedulers",
    "shell": "Shell", "align": "Aligners", "net": "Network and downloads",
    "perl": "Perl",
}


# ------------------------------------------------------------------- lectura

def llegeix_catalog(text):
    """Treu les entrades de l'array CATALOGUE del JavaScript.

    No és JSON: hi ha expressions regulars a `sig:`. N'hi ha prou amb llegir
    els camps de text, que són els únics que es publiquen.
    """
    inici = text.index("var CATALOGUE = [")
    fi = text.index("\n  ];", inici)
    cos = text[inici:fi]

    entrades = []
    for bloc in re.findall(r"\n    \{(.*?)\n    \}", cos, re.S):
        camps = dict(
            (k, v) for k, v in re.findall(r'(\w+):"((?:[^"\\]|\\.)*)"', bloc)
        )
        if camps.get("title"):
            entrades.append(camps)
    return entrades


def clau(etiqueta):
    net = unicodedata.normalize("NFKD", etiqueta).encode("ascii", "ignore").decode()
    net = re.sub(r"[^a-zA-Z0-9]+", "-", net).strip("-").lower()
    return net[:60] or "entrada"


def sense_html(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def tipografies(text):
    """Els mateixos <link> de font que la portada, perquè les fitxes no es
    vegin d'una altra web."""
    cap = text[text.index("<head"):text.index("</head>")]
    trobats = re.findall(r'<link[^>]*fonts\.(?:googleapis|gstatic)[^>]*>', cap)
    return "\n".join(trobats)


def paleta(text):
    """Reaprofita els colors i les tipografies de la portada, perquè les
    fitxes no semblin d'una altra web."""
    m = re.search(r":root\{[^}]*\}", text)
    return m.group(0) if m else ":root{--ink:#111;--ink-faint:#666;--line:#ddd;}"


# --------------------------------------------------------- pàgines per fitxa

CSS_FITXA = """
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:16px;line-height:1.6;}
.wrap{max-width:720px;margin:0 auto;padding:40px 20px 80px;}
nav{font-size:13px;color:var(--ink-faint);margin-bottom:28px;}
nav a{color:var(--ink-faint);}
h1{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:20px;line-height:1.35;margin:0 0 10px;word-break:break-word;}
.what{font-size:18px;font-weight:600;margin:0 0 28px;}
h2{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
  letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);
  margin:26px 0 6px;}
p{margin:0 0 14px;}
code{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.9em;background:#f4f4f2;padding:1px 4px;border-radius:3px;
  word-break:break-word;}
.src{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
  color:var(--ink-faint);margin-top:26px;padding-top:14px;
  border-top:1px solid var(--line);}
.back{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);
  font-size:14px;}
.back a{color:var(--ink);}
"""


def pagina_fitxa(e, arrel_css, fonts):
    etiqueta = e.get("label", "")
    titol_pla = sense_html(e["title"])
    desc = html.escape(titol_pla[:180], quote=True)
    url = BASE + "e/" + clau(etiqueta) + ".html"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(etiqueta)} — what it actually means</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
{fonts}
<style>{arrel_css}{CSS_FITXA}</style>
</head>
<body>
<div class="wrap">
  <nav><a href="../index.html">BioErrors</a> / {html.escape(AREES.get(e.get("cat", ""), e.get("cat", "")))}</nav>
  <h1>{html.escape(etiqueta)}</h1>
  <p class="what">{e["title"]}</p>
  <h2>why</h2>
  <p>{e.get("cause", "")}</p>
  <h2>what to do</h2>
  <p>{e.get("fix", "")}</p>
  <div class="src">{html.escape(e.get("src", ""))}</div>
  <div class="back">
    This is one entry from <a href="../index.html">BioErrors</a>, a catalogue of
    bioinformatics error messages that point at the wrong thing. Every entry was
    traced to its real cause before it was written down.<br>
    If your error is not in it, <a href="../index.html">paste it there</a> and it
    gets traced and added.
  </div>
</div>
</body>
</html>
"""


# ----------------------------------------------------------- índex i sitemap

def bloc_index(entrades):
    """La portada llista, no repeteix.

    Si la portada porta el text sencer de cada fitxa i la fitxa també, Google
    ho llegeix com a contingut duplicat i decideix ell quina ensenyar. Aquí la
    portada dona etiqueta, una línia i enllaç; el text sencer viu a la fitxa.
    """
    per_area = {}
    for e in entrades:
        per_area.setdefault(e.get("cat", "altres"), []).append(e)

    seccions = []
    for c, llista in sorted(per_area.items(), key=lambda x: -len(x[1])):
        files = "\n".join(
            f'<li><a href="e/{clau(x.get("label",""))}.html">'
            f'<code>{html.escape(x.get("label",""))}</code></a> '
            f'<span>{html.escape(sense_html(x["title"]))}</span></li>'
            for x in llista
        )
        seccions.append(
            f'<h3 class="area">{html.escape(AREES.get(c, c.title()))} '
            f'<span>{len(llista)}</span></h3>\n<ul class="idx">\n{files}\n</ul>'
        )

    return (
        f'{INICI}\n<section id="catalogue">\n'
        f'<h2>The full catalogue — {len(entrades)} signatures</h2>\n'
        f'<p class="lede">Every signature in the catalogue, so you can read the '
        f'list without pasting anything. Each one opens the entry, with the cause '
        f'and where the diagnosis came from.</p>\n'
        + "\n".join(seccions)
        + f'\n</section>\n{FI}'
    )


CSS_INDEX = """
  #catalogue{margin-top:52px;border-top:1px solid var(--line);padding-top:28px;}
  #catalogue h2{font-size:19px;margin:0 0 8px;}
  #catalogue .lede{color:var(--ink-faint);margin:0 0 26px;max-width:62ch;}
  #catalogue h3.area{font-family:"IBM Plex Mono",monospace;font-size:12px;
    letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);
    margin:34px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px;}
  #catalogue h3.area span{float:right;}
  #catalogue ul.idx{list-style:none;margin:0;padding:0;}
  #catalogue ul.idx li{margin:0 0 12px;}
  #catalogue ul.idx code{font-size:13px;word-break:break-word;}
  #catalogue ul.idx span{display:block;color:var(--ink-faint);font-size:14px;}
"""


def sitemap(entrades):
    avui = date.today().isoformat()
    urls = [BASE] + [BASE + "e/" + clau(e.get("label", "")) + ".html"
                     for e in entrades]
    cos = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{avui}</lastmod></url>" for u in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{cos}\n</urlset>\n")


# --------------------------------------------------------------------- main

def main():
    text = PAGINA.read_text(encoding="utf-8")
    entrades = llegeix_catalog(text)
    if not entrades:
        sys.exit("No he sabut llegir cap entrada del CATALOGUE.")

    claus = [clau(e.get("label", "")) for e in entrades]
    duplicats = {k for k in claus if claus.count(k) > 1}
    if duplicats:
        sys.exit(f"Adreces repetides, dues fitxes escriurien el mateix fitxer: "
                 f"{sorted(duplicats)}")

    arrel_css = paleta(text)
    fonts = tipografies(text)

    # No s'esborra la carpeta sencera: a Windows falla si algú la té oberta,
    # i a sobre no cal. S'escriuen les que toquen i es treuen només les que
    # han desaparegut del catàleg, perquè no quedin pàgines penjades.
    FITXES.mkdir(exist_ok=True)
    vigents = set()
    for e in entrades:
        nom = clau(e.get("label", "")) + ".html"
        vigents.add(nom)
        (FITXES / nom).write_text(
            pagina_fitxa(e, arrel_css, fonts), encoding="utf-8"
        )
    for antic in FITXES.glob("*.html"):
        if antic.name not in vigents:
            antic.unlink()
            print(f"   retirada: e/{antic.name}")

    bloc = bloc_index(entrades)
    if INICI in text and FI in text:
        text = re.sub(re.escape(INICI) + ".*?" + re.escape(FI),
                      lambda _: bloc, text, flags=re.S)
    else:
        text = text.replace("  <footer>", bloc + "\n\n  <footer>", 1)

    text = re.sub(r"\n  #catalogue\{.*?color:var\(--ink-faint\);margin-top:8px;\}\n",
                  "\n", text, flags=re.S)
    if "#catalogue{" not in text:
        text = text.replace("  footer{font-family:",
                            CSS_INDEX + "  footer{font-family:", 1)

    PAGINA.write_text(text, encoding="utf-8")
    (AQUI / "sitemap.xml").write_text(sitemap(entrades), encoding="utf-8")
    (AQUI / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8"
    )

    visible = text[text.index("<body"):text.index("<script>")]
    print(f">> {len(entrades)} fitxes a e/, sitemap i robots escrits")
    print(f"   portada: índex enllaçat, {len(visible):,} caràcters visibles")
    print(f"   sitemap: {len(entrades) + 1} adreces")


if __name__ == "__main__":
    main()
