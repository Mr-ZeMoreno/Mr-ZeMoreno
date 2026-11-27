"""Genera las tarjetas SVG del README en cards/ (solo librería estándar).

    GH_TOKEN=... python scripts/render_cards.py

Sin token se omiten las tarjetas de contribuciones (se conservan las que ya existan).
"""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
USER = "Mr-ZeMoreno"

BG, SURFACE, BORDER = "#0c0f10", "#14191b", "#262e31"
TEXT, MUTED, DIM = "#d9e1df", "#8a9e9c", "#5a6a6c"
# paleta apagada: metal gastado, pared verde agua sucia, naranja de seguridad, azul y verde de spray
CRIMSON, CORAL, ROSE, RED = "#c4561a", "#d97a35", "#3d7fae", "#a52a2a"
SPRAY = ["#d9e1df", "#c4561a", "#3d7fae", "#4f9a6a", "#a52a2a"]  # blanco, naranja, azul, verde, rojo

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'JetBrains Mono',SFMono-Regular,Consolas,Menlo,monospace"
MONTHS = "Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic".split()

STYLE = f"""
.s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
.rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
.fade{{animation:fade .6s ease both}}
.pulse{{animation:pulse 1.6s ease-in-out infinite}}
.nudge{{animation:nudge 1.8s ease-in-out infinite}}
.grow{{animation:grow .9s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:bottom}}
.sheen{{animation:sheen 6s ease-in-out infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pulse{{50%{{opacity:.25}}}}
@keyframes nudge{{50%{{transform:translateX(5px)}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:none}}}}
@keyframes sheen{{0%,55%{{transform:translateX(-500px)}}100%{{transform:translateX(1100px)}}}}
.tag{{font-family:'Marker Felt','Permanent Marker','Comic Sans MS',cursive;font-weight:700}}
.spray{{animation:fade 1.2s ease both}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.sheen{{display:none}}}}
"""


def text(x, y, value, size=14, fill=TEXT, cls="s", extra=""):
    return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" {extra}>'
            f"{escape(str(value))}</text>")


def anim(cls, delay, body):
    return f'<g class="{cls}" style="animation-delay:{delay:.2f}s">{body}</g>'


WALL = {}  # nombre de tarjeta -> grafitis (se llenan en main)


def tag(x, y, value, color, size=40, rot=-6, opacity=.5, drips=()):
    """Tag de spray: texto con borde áspero y chorreados (drips = [(dx, largo), ...])."""
    out = (f'<g transform="rotate({rot} {x} {y})" opacity="{opacity}" filter="url(#rough)">'
           + text(x, y, value, size, color, "tag", f'stroke="{color}" stroke-width="1.2"'))
    for dx, length in drips:
        out += (f'<path d="M{x + dx} {y + 2}v{length}" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>'
                f'<circle cx="{x + dx}" cy="{y + 3 + length}" r="2.4" fill="{color}"/>')
    return f'<g class="spray">{out}</g></g>'


def scrawl(d, color, opacity=.45, width=2.4):
    """Trazo a mano alzada (flechas, tachones, coronas...)."""
    return (f'<path class="spray" d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}" filter="url(#rough)"/>')


def save(name, width, height, title, body, fill=BG):
    """Tarjeta con margen transparente de 4px para que se puedan juntar en el README."""
    w, h = width - 8, height - 8
    grime = (f'<rect x="4" y="4" width="{w}" height="{h}" filter="url(#noise)" opacity=".35"/>'
             f'<rect x="4" y="4" width="{w}" height="{h}" fill="url(#vig)"/>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{STYLE}</style>"
        f'<defs><clipPath id="c"><rect x="4" y="4" width="{w}" height="{h}" rx="14"/></clipPath>'
        '<filter id="noise" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" '
        'baseFrequency=".85" numOctaves="2" seed="7"/><feColorMatrix values="0 0 0 0 .55 0 0 0 0 .62 '
        '0 0 0 0 .6 0 0 0 1.6 -.95"/></filter>'
        '<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="2" seed="3"/>'
        '<feDisplacementMap in="SourceGraphic" scale="3.5"/></filter>'
        '<radialGradient id="vig" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient></defs>'
        f'<g clip-path="url(#c)"><rect x="4" y="4" width="{w}" height="{h}" fill="{fill}"/>'
        f'{WALL.get(name, "")}{body}{grime}</g>'
        f'<rect x="4.5" y="4.5" width="{w - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{BORDER}"/>'
        "</svg>"
    )
    (CARDS / f"{name}.svg").write_text(svg, encoding="utf-8")


def glow(gid, cx, cy, r, color, opacity=0.12):
    return (f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>')


def hero():
    b = glow("g1", 690, 200, 300, RED) + glow("g2", 60, 20, 320, CRIMSON)
    b += anim("fade", .1,
              f'<rect class="pulse" x="40" y="62" width="9" height="9" fill="{CORAL}"/>'
              + text(60, 71, "BACKEND · INFRAESTRUCTURA INDUSTRIAL", 12, MUTED, "m",
                     'letter-spacing="1.2"'))
    heavy = 'font-weight="800" letter-spacing="-3"'
    b += anim("rise", .2, text(36, 164, "JoseCarlos", 84, TEXT, "s", heavy))
    b += anim("rise", .32, text(36, 250, "Vidal", 84, CRIMSON, "s", heavy))
    b += anim("rise", .5,
              text(40, 300, "Co-fundador de Coworkers.cl", 18, "#b9c6c4")
              + text(40, 326, "Ingeniería Informática · Concepción, Chile", 15, DIM))
    b += anim("fade", .8,
              text(40, 376, "mr-zemoreno.dev", 13, TEXT, "m")
              + f'<g class="nudge">{text(172, 376, "→", 15, CORAL, "m")}</g>')

    portrait = ROOT / "data" / "portrait.json"
    if portrait.exists():  # retrato ASCII generado por scripts/portrait.py
        rows = json.loads(portrait.read_text(encoding="utf-8"))
        cols = len("".join(t for _, t in rows[0]))
        x, y, width, line = 478, 28, 372, 7.7
        for i, runs in enumerate(rows):
            spans = "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for c, t in runs)
            b += anim("fade", .25 + i * .03,
                      f'<text x="{x}" y="{y + i * line:.1f}" class="m" font-size="7.9" font-weight="700" '
                      f'xml:space="preserve" textLength="{width}" lengthAdjust="spacingAndGlyphs" '
                      f'data-cols="{cols}">{spans}</text>')
        save("hero", 880, 408,
             "JoseCarlos Vidal, backend e infraestructura industrial. Co-fundador de Coworkers.cl.", b)
        return

    # sin retrato: terminal industrial gastada, cada línea aparece en orden
    x, y, w, h = 492, 44, 356, 318
    W, O, B, G, R = SPRAY
    hazard = "".join(f'<path d="M{x + i * 18} {y + 30}l14-30h9l-14 30z" fill="#e0a526"/>'
                     for i in range(-1, w // 18 + 2))
    b += (f'<clipPath id="term"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/></clipPath>'
          f'<g clip-path="url(#term)"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#101416"/>'
          f'<rect x="{x}" y="{y}" width="{w}" height="30" fill="#1b1b18"/><g opacity=".55">{hazard}</g>'
          # placa con el prompt sobre las franjas
          f'<rect x="{x + 12}" y="{y + 7}" width="168" height="17" rx="3" fill="#0c0f10" stroke="#2c3336"/>'
          + text(x + 20, y + 19.5, "zm@coworkers: ~/fábrica", 10.5, MUTED, "m")
          # rayones del metal
          + "".join(f'<path d="M{x + a} {y + c}l{d} {e}" stroke="#fff" stroke-width=".6" opacity=".07"/>'
                    for a, c, d, e in ((40, 250, 90, -18), (210, 80, 120, 30), (260, 300, 70, -10), (20, 140, 40, 6)))
          + "</g>"
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="#2c3336" stroke-width="1.5"/>'
          # remaches en las esquinas de abajo
          + "".join(f'<circle cx="{cx}" cy="{y + h - 10}" r="2.6" fill="#3a4447" stroke="#0c0f10"/>'
                    for cx in (x + 10, x + w - 10)))
    prompt = [("zm", O), (":", DIM), ("~", B), ("$ ", DIM)]
    lines = [
        prompt + [("whoami", TEXT)],
        [("backend", O), (" + ", DIM), ("infra", B), (" para sistemas industriales", MUTED)],
        prompt + [("cat stack.txt", TEXT)],
        [("FastAPI", G), (" · ", DIM), ("PostgreSQL", B), (" · ", DIM), ("Docker", B)],
        [("Python", G), (" · ", DIM), ("C", O), (" · ", DIM), ("Rust", O), (" · ", DIM), ("WebSockets", W)],
        prompt + [("ls proyectos/", TEXT)],
        [("usm-vpn", B), ("/  ", DIM), ("node-latex-parser", B), ("/", DIM)],
        [("astro-markdown-runtime", B), ("/  ", DIM), ("lebu-ifm", B), ("/", DIM)],
        prompt,
    ]
    for i, runs in enumerate(lines):
        spans = "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for t, c in runs)
        b += anim("fade", .4 + i * .18,
                  f'<text x="{x + 20}" y="{y + 66 + i * 27}" class="m" font-size="12.5" xml:space="preserve">{spans}</text>')
    b += anim("fade", .4 + len(lines) * .18,
              f'<rect class="pulse" x="{x + 75}" y="{y + 56 + (len(lines) - 1) * 27}" width="8" height="14" fill="{O}"/>')
    # grafiti encima del panel: subrayado de spray, cinta adhesiva y pegatina
    b += scrawl(f"M{x + 18} {y + 98}c60 4 140-3 210 2", O, .55, 2)
    b += (f'<g class="spray" transform="rotate(32 {x + w - 22} {y + 40})" opacity=".8">'
          f'<rect x="{x + w - 62}" y="{y + 30}" width="84" height="20" fill="#8e8a7c" opacity=".55"/>'
          f'<path d="M{x + w - 62} {y + 30}v20m84-20v20" stroke="#0c0f10" stroke-dasharray="2 2" opacity=".5"/></g>')
    b += (f'<g class="spray" transform="rotate(-14 {x + w - 46} {y + h - 50})">'
          f'<circle cx="{x + w - 46}" cy="{y + h - 50}" r="26" fill="{R}" opacity=".85" stroke="{W}" stroke-width="2.5"/>'
          + text(x + w - 46, y + h - 43, "ZM", 20, W, "tag", 'text-anchor="middle"') + "</g>")
    save("hero", 880, 408,
         "JoseCarlos Vidal, backend e infraestructura industrial. Co-fundador de Coworkers.cl.", b)


def pillar(name, x_label, big, unit, lines, color, delay):
    w, h = 440, 212
    b = glow("g", 390, 190, 220, color, .18)
    b += f'<rect x="4" y="4" width="432" height="3" fill="{color}"/>'
    b += (f'<g class="sheen"><path d="M0 0H60L-10 212H-70Z" fill="#fff" opacity=".03"/></g>')
    b += text(24, 40, x_label, 12, color, "m", 'letter-spacing="1.4"')
    b += f'<g class="nudge">{text(398, 40, "→", 15, color, "m")}</g>'
    b += anim("rise", delay,
              f'<text x="22" y="100" class="s" fill="{TEXT}"><tspan font-size="44" font-weight="800">{escape(big)}</tspan>'
              f'<tspan font-size="17" fill="{MUTED}" dx="8">{escape(unit)}</tspan></text>')
    for i, row in enumerate(lines):
        b += anim("rise", delay + .15 + i * .08, text(24, 138 + i * 22, row, 13.5, "#b9c6c4"))
    save(name, w, h, f"{x_label}: {big} {unit}. {' '.join(lines)}", b, SURFACE)


def section_title(name, label, color):
    b = (f'<rect class="pulse" x="26" y="27" width="9" height="9" fill="{color}"/>'
         + anim("rise", .1, text(48, 39, label, 22, TEXT, "s", 'font-weight="700"')))
    save(name, 880, 64, label, b)


def stack():
    groups = [
        ("BACKEND", ["Python", "FastAPI", "PostgreSQL", "WebSockets"], CRIMSON),
        ("SISTEMAS", ["C", "C++", "Rust", "Linux"], CORAL),
        ("WEB", ["Astro", "TypeScript"], ROSE),
        ("TOOLS", ["Docker", "Git", "GitHub", "OpenVPN"], RED),
    ]
    b, n = "", 0
    for row, (label, items, color) in enumerate(groups):
        y = 28 + row * 48
        b += text(32, y + 20, label, 12, color, "m", 'letter-spacing="1.4"')
        x = 200
        for item in items:
            w = len(item) * 8 + 36
            b += anim("rise", .1 + n * .04,
                      f'<rect x="{x}" y="{y}" width="{w}" height="31" rx="15.5" fill="{SURFACE}" stroke="{BORDER}"/>'
                      f'<circle cx="{x + 15}" cy="{y + 15.5}" r="3.5" fill="{color}"/>'
                      + text(x + 25, y + 20, item, 12.5, TEXT, "m",
                             f'textLength="{len(item) * 7.2:.0f}" lengthAdjust="spacingAndGlyphs"'))
            x += w + 10
            n += 1
    save("stack", 880, 232, "Stack: " + ", ".join(i for g in groups for i in g[1]), b)


def fetch_calendar(token):
    query = ("query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{"
             "totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def heatmap(calendar):
    colors = {"NONE": "#1a2023", "FIRST_QUARTILE": "#3b2416", "SECOND_QUARTILE": "#6e3415",
              "THIRD_QUARTILE": "#b0501a", "FOURTH_QUARTILE": "#d97a35"}
    total = calendar["totalContributions"]
    b = text(32, 40, f"{total} contribuciones en el último año", 15, TEXT, "s", 'font-weight="700"')
    weeks = calendar["weeks"][-53:]
    step, left, top = 15.4, 32, 76
    last_month, last_x = None, -99
    for i, week in enumerate(weeks):
        x = left + i * step
        month = int(week["contributionDays"][0]["date"][5:7])
        if month != last_month and x - last_x > 32 and x < 820:
            b += text(f"{x:.1f}", 66, MONTHS[month - 1], 11, DIM, "m")
            last_x = x
        last_month = month
        cells = ""
        for day in week["contributionDays"]:
            weekday = dt.date.fromisoformat(day["date"]).isoweekday() % 7
            cells += (f'<rect x="{x:.1f}" y="{top + weekday * step:.1f}" width="12" height="12" rx="3" '
                      f'fill="{colors[day["contributionLevel"]]}"/>')
        b += anim("fade", i * .018, cells)
    # grafiti encima de las celdas vacías: lo que no se ve es privado
    b += tag(250, 140, "el resto es \"privado\"", SPRAY[0], 34, -4, .7, [(40, 14), (190, 9)])
    b += tag(300, 172, "(eso me dijo microsoft)", SPRAY[2], 17, -4, .75)
    save("heatmap", 880, 204, f"{total} contribuciones en GitHub durante el último año", b)


def activity(calendar):
    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["contributionCount"]
    months = list(months.items())[-12:]
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    best = max(days, key=lambda d: d["contributionCount"])
    active = sum(1 for d in days if d["contributionCount"])
    best_date = dt.date.fromisoformat(best["date"])
    stats = [
        (active, "días activos", CRIMSON),
        (longest, "días de racha máxima", CORAL),
        (best["contributionCount"], f"mejor día · {best_date.day} {MONTHS[best_date.month - 1]}", ROSE),
    ]
    b = ""
    for i, (value, label, color) in enumerate(stats):
        y = 56 + i * 62
        b += anim("rise", .15 + i * .15,
                  text(32, y, value, 30, color, "s", 'font-weight="800"')
                  + text(32, y + 18, label, 12, MUTED))
    peak = max(v for _, v in months) or 1
    for i, (key, value) in enumerate(months):
        x, h = 250 + i * 50.5, max(3, value / peak * 130)
        b += (f'<rect class="grow" style="animation-delay:{.2 + i * .06:.2f}s" x="{x}" y="{178 - h:.1f}" '
              f'width="34" height="{h:.1f}" rx="5" fill="url(#bar)"/>')
        b += text(x + 17, f"{170 - h:.1f}", value, 11, MUTED, "m", 'text-anchor="middle"')
        b += text(x + 17, 202, MONTHS[int(key[5:]) - 1], 11, DIM, "m", 'text-anchor="middle"')
    b = (f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CORAL}"/>'
         f'<stop offset="1" stop-color="{CRIMSON}"/></linearGradient>') + b
    save("activity", 880, 224,
         f"Actividad mensual: {active} días activos, racha máxima de {longest} días", b)


def main():
    CARDS.mkdir(exist_ok=True)
    W, O, B, G, R = SPRAY
    WALL.update({
        "hero": tag(150, 120, "MORENO", W, 110, -8, .07)
        + tag(230, 384, "hecho a mano?", B, 22, -3, .55, [(18, 9), (96, 14)])
        + scrawl("M150 192l10-22 12 14 10-18 10 18 12-14 10 22z", O, .6)  # corona sobre Vidal
        + scrawl("M410 40l12 10m0-10l-12 10", G, .55)
        + tag(395, 280, "<3", R, 30, 12, .5)
        + scrawl("M430 368c20-12 34 6 22 14s-30-2-8-16", W, .3),
        "heatmap": tag(640, 38, "commit o muere", O, 22, -4, .5, [(30, 10), (120, 7)])
        + tag(345, 36, "¿de qué color era el cielo?", B, 17, 3, .55, [(150, 8)])
        + scrawl("M830 30v20m6-20v20m6-20v20m6-20v20m-26 16l32-24", W, .35, 2),
        "activity": tag(700, 60, "¡boom!", B, 28, -10, .6, [(20, 12)])
        + scrawl("M790 70c20 5 30 18 26 40m0 0l-8-8m8 8l8-9", B, .6),
        "backend": tag(250, 196, "200 OK", G, 26, -8, .5, [(14, 8), (70, 13)])
        + scrawl("M360 60l8 8m0-8l-8 8", W, .4),
        "infra": tag(270, 196, "sudo", O, 30, -6, .5, [(24, 11)])
        + scrawl("M380 150a22 22 0 1 0 1 0", B, .35)
        + scrawl("M30 186h40l-8-6m8 6l-8 6", W, .35),
        "title-stack": tag(680, 44, "no tocar", R, 22, -3, .55, [(40, 6)]),
        "stack": tag(690, 210, "ZM", O, 46, -12, .35, [(12, 12), (40, 7)])
        + scrawl("M780 28l14 14m0-14l-14 14", G, .45)
        + tag(560, 140, "solo sé que nada sé", W, 24, -5, .55, [(60, 12), (170, 8)]),
    })
    hero()
    pillar("backend", "BACKEND", "APIs", "en tiempo real", ["Servicios con FastAPI y PostgreSQL,",
           "WebSockets y despliegue con Docker."], CORAL, .2)
    pillar("infra", "INFRAESTRUCTURA", "Industria", "sistemas y redes", ["Software para automatización industrial,",
           "C, Linux y redes (VPN, OpenVPN)."], CRIMSON, .35)
    section_title("title-stack", "Stack", CORAL)
    stack()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        calendar = fetch_calendar(token)
        heatmap(calendar)
        activity(calendar)
    else:
        print("Sin GH_TOKEN: no se actualizan heatmap.svg ni activity.svg")


if __name__ == "__main__":
    main()
