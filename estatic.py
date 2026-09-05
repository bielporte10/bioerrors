"""
Publica el catàleg també com a HTML estàtic dins d'index.html.

Per què cal. Tot el catàleg viu dins del `<script>`: el 2026-09-05 el HTML
visible de la pàgina eren 2.053 caràcters i el JavaScript 40.552. Cap signatura
d'error — `bash\\r`, `NegativeArraySizeException`, `.vmoptions`, `-Xmx` — existia
com a text llegible, i només apareixia després que algú enganxés un error i
cliqués un botó.

Això vol dir que **qui googleja el seu error exacte no pot arribar mai aquí**,
que és precisament el canal amb què es va justificar el projecte: la gent ja
enganxa errors de bioinformàtica a Google. La caixa interactiva es queda; a
sota s'hi afegeix el catàleg sencer en HTML pla, que és el que un cercador pot
indexar i el que algú pot llegir sense haver d'enganxar res.

Cada entrada té àncora pròpia (`#s-...`), per poder enllaçar una fitxa concreta
des d'una resposta a Biostars.

La font de veritat segueix sent l'array CATALOGUE del JavaScript. Aquest script
el llegeix i regenera el bloc estàtic entre dues marques, o sigui que es pot
tornar a executar tantes vegades com calgui.

Us:
    python estatic.py
"""

import html
import re
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

AQUI = Path(__file__).parent
PAGINA = AQUI / "index.html"
INICI = "<!-- CATALEG-ESTATIC:INICI -->"
FI = "<!-- CATALEG-ESTATIC:FI -->"

AREES = {
    "nextflow": "Nextflow", "snakemake": "Snakemake", "conda": "conda i entorns",
    "docker": "Contenidors", "file": "Fitxers i formats", "r": "R i Bioconductor",
    "java": "Java", "python": "Python", "cluster": "HPC i cues",
    "shell": "Shell", "perl": "Perl",
}


def llegeix_catalog(text):
    """Treu les entrades de l'array CATALOGUE del JavaScript.

    No fa servir un parser de JSON perquè això no és JSON: hi ha expressions
    regulars a `sig:`. N'hi ha prou amb llegir els camps de text, que són els
    únics que es publiquen.
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


def ancora(etiqueta):
    net = unicodedata.normalize("NFKD", etiqueta).encode("ascii", "ignore").decode()
    net = re.sub(r"[^a-zA-Z0-9]+", "-", net).strip("-").lower()
    return "s-" + (net[:60] or "entrada")


def fitxa(e):
    return (
        f'<article class="entry" id="{ancora(e.get("label", e["title"]))}">\n'
        f'  <h3>{html.escape(e.get("label", ""))}</h3>\n'
        f'  <p class="what">{e["title"]}</p>\n'
        f'  <dl><dt>why</dt><dd>{e.get("cause", "")}</dd>\n'
        f'  <dt>next</dt><dd>{e.get("fix", "")}</dd></dl>\n'
        f'  <div class="src">{html.escape(e.get("src", ""))}</div>\n'
        f'</article>'
    )


def construeix(entrades):
    per_area = {}
    for e in entrades:
        per_area.setdefault(e.get("cat", "altres"), []).append(e)

    seccions = []
    for clau, llista in sorted(per_area.items(), key=lambda x: -len(x[1])):
        titol = AREES.get(clau, clau.title())
        seccions.append(
            f'<h3 class="area">{html.escape(titol)} '
            f'<span>{len(llista)}</span></h3>\n'
            + "\n".join(fitxa(e) for e in llista)
        )

    return (
        f'{INICI}\n'
        f'<section id="catalogue">\n'
        f'<h2>The full catalogue — {len(entrades)} signatures</h2>\n'
        f'<p class="lede">Every entry, as plain text, so you can read the whole '
        f'thing without pasting anything — and so it can be found by searching '
        f'for the error itself. Each one says where the diagnosis came from.</p>\n'
        + "\n".join(seccions)
        + f'\n</section>\n{FI}'
    )


CSS = """
  #catalogue{margin-top:52px;border-top:1px solid var(--line);padding-top:28px;}
  #catalogue h2{font-size:19px;margin:0 0 8px;}
  #catalogue .lede{color:var(--ink-faint);margin:0 0 26px;max-width:62ch;}
  #catalogue h3.area{font-family:"IBM Plex Mono",monospace;font-size:12px;
    letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);
    margin:34px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px;}
  #catalogue h3.area span{float:right;}
  #catalogue .entry{margin:0 0 22px;}
  #catalogue .entry h3{font-family:"IBM Plex Mono",monospace;font-size:13px;
    margin:0 0 4px;word-break:break-word;}
  #catalogue .entry .what{margin:0 0 8px;font-weight:600;}
  #catalogue .entry dl{margin:0;}
  #catalogue .entry dt{font-family:"IBM Plex Mono",monospace;font-size:11px;
    letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint);margin-top:6px;}
  #catalogue .entry dd{margin:2px 0 0;}
  #catalogue .entry .src{font-family:"IBM Plex Mono",monospace;font-size:11px;
    color:var(--ink-faint);margin-top:8px;}
"""


def main():
    text = PAGINA.read_text(encoding="utf-8")
    entrades = llegeix_catalog(text)
    if not entrades:
        sys.exit("No he sabut llegir cap entrada del CATALOGUE.")

    bloc = construeix(entrades)

    if INICI in text and FI in text:
        text = re.sub(re.escape(INICI) + ".*?" + re.escape(FI), lambda _: bloc,
                      text, flags=re.S)
    else:
        text = text.replace("  <footer>", bloc + "\n\n  <footer>", 1)

    if "#catalogue{" not in text:
        text = text.replace("  footer{font-family:", CSS + "  footer{font-family:", 1)

    PAGINA.write_text(text, encoding="utf-8")

    visible = text[text.index("<body"):text.index("<script>")]
    print(f">> {len(entrades)} entrades publicades com a HTML estàtic")
    print(f"   HTML visible: {len(visible):,} caràcters "
          f"(abans de fer-ho eren ~2.053)")


if __name__ == "__main__":
    main()
