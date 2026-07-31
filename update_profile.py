"""Regenerate dark_mode.svg / light_mode.svg from ascii.txt.

Runs daily via GitHub Actions. Stdlib only, no dependencies.
"""
import html
import os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ascii.txt"), encoding="utf-8") as f:
    ART = f.read().replace("\r\n", "\n").strip("\n")

W = 763
H = 1143
FONT = 13
LINE_H = 15
X = 22
Y0 = 37

PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "fg": "#8b949e"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "fg": "#24292f"},
}


def render(mode):
    p = PALETTES[mode]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg"',
        f' width="{W}" height="{H}" viewBox="0 0 {W} {H}"',
        ' font-family="Consolas, Menlo, Monaco, \'Liberation Mono\', monospace"',
        f' font-size="{FONT}px">',
        f'  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>',
        f'  <g fill="{p["fg"]}">',
    ]
    for i, line in enumerate(ART.split("\n")):
        out.append(f'<text x="{X}" y="{Y0 + i * LINE_H}" xml:space="preserve">{html.escape(line)}</text>')
    out.extend(["  </g>", "</svg>"])
    return "\n".join(out)


if __name__ == "__main__":
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode))
    print("wrote dark_mode.svg, light_mode.svg")
