"""Regenerate dark_mode.svg / light_mode.svg with live GitHub stats.

Runs daily via GitHub Actions. Stdlib only, no dependencies.
"""
import calendar
import html
import json
import os
import urllib.request
from datetime import date, datetime, timezone

USER = "IBRHUB"
START = date(2009, 1, 7)
JOINED_YEAR = 2022  # account creation year, for contributions history
EMAIL = "me@ibrhub.net"
HOST = "IBRHUB"
KERNEL = "Windows & Web Developer"
IDE = "Neovim, Cursor"
LANG_PROG = "PowerShell, C#, C++, C, YAML"
LANG_REAL = "Arabic, English"
HOBBIES = "Windows Tuning"

ART_FONT = 11
ART_LINE = 13
ART_X = 22
ART_Y0 = 37

INFO_FONT = 14
INFO_LINE = 31
INFO_W = 54
INFO_PAD_X = 24
INFO_PAD_Y = 28
PANEL_GAP = 32

ART_CHAR_W = 0.60 * ART_FONT
INFO_CHAR_W = 0.60 * INFO_FONT

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ascii.txt"), encoding="utf-8") as f:
    ART = f.read().replace("\r\n", "\n").strip("\n")

TOKEN = os.environ.get("GITHUB_TOKEN") or ""


def gh(url, payload=None, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {token or TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read() or "{}")


def graphql(query, variables=None, token=None):
    _, resp = gh("https://api.github.com/graphql", {"query": query, "variables": variables or {}}, token)
    if resp.get("errors"):
        raise RuntimeError(resp["errors"])
    return resp["data"]


def age(b, t):
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    months = (t.month - b.month - (t.day < b.day)) % 12
    if t.day >= b.day:
        days = t.day - b.day
    else:
        pm_year, pm = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
        days = calendar.monthrange(pm_year, pm)[1] - b.day + t.day
    return years, months, days


def fetch_stats():
    yr_aliases = "\n".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
        " { totalCommitContributions restrictedContributionsCount }"
        for y in range(JOINED_YEAR, datetime.now(timezone.utc).year + 1)
    )
    contrib = graphql(f'query {{ user(login: "{USER}") {{ {yr_aliases} }} }}')["user"]
    commits = sum(
        v["totalCommitContributions"]
        for v in contrib.values()
    )
    u = graphql(f"""
    query {{
      user(login: "{USER}") {{
        id
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {{
          totalCount
          nodes {{ name stargazerCount isFork }}
        }}
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{
          totalCount
        }}
      }}
    }}""")["user"]
    stats = {
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "commits": commits,
    }
    stats.update(loc([n["name"] for n in u["repositories"]["nodes"] if not n["isFork"]], u["id"]))
    return stats


LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { additions deletions }
      }
    } } }
  }
}"""


def loc(repo_names, user_id):
    add = rem = 0
    for name in repo_names:
        cursor = None
        try:
            while True:
                ref = graphql(LOC_QUERY, {"owner": USER, "name": name, "id": user_id, "cursor": cursor})["repository"]["defaultBranchRef"]
                if ref is None:
                    break
                h = ref["target"]["history"]
                add += sum(n["additions"] for n in h["nodes"])
                rem += sum(n["deletions"] for n in h["nodes"])
                if not h["pageInfo"]["hasNextPage"]:
                    break
                cursor = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"loc {name}: {e}")
    return {"loc_add": add, "loc_del": rem, "loc": add - rem}


PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "art": "#8b949e", "h": "#58a6ff",
             "k": "#ffa657", "v": "#c9d1d9", "d": "#484f58", "g": "#3fb950", "r": "#f85149"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "art": "#57606a", "h": "#0969da",
              "k": "#953800", "v": "#24292f", "d": "#afb8c1", "g": "#1a7f37", "r": "#cf222e"},
}


def kv(key, val, width=INFO_W):
    dots = "." * max(width - len(key) - len(str(val)) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (str(val), "v")]


def kv2(k1, v1, k2, v2):
    return kv(k1, v1, 29) + [(" | ", "d")] + kv(k2, v2, 22)


def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * (INFO_W - len(label)), "d")]


def info_lines(s):
    y, m, d = age(START, date.today())
    n = lambda x: f"{x:,}"
    return [
        [(f"{USER.lower()}@github ", "h"), ("─" * (INFO_W - len(USER) - 8), "d")],
        [],
        kv("OS", "Windows, Linux"),
        kv("Uptime", f"{y} years, {m} months (since {START.year})"),
        kv("Host", HOST),
        kv("Kernel", KERNEL),
        kv("IDE", IDE),
        [],
        kv("Languages.Programming", LANG_PROG),
        kv("Languages.Real", LANG_REAL),
        kv("Hobbies", HOBBIES),
        [],
        rule("Contact"),
        kv("Email", EMAIL),
        [],
        rule("GitHub Stats"),
        kv2("Repos", f"{s['repos']} {{Contributed: {s['contributed']}}}", "Stars", n(s["stars"])),
        kv2("Commits", n(s["commits"]), "Followers", n(s["followers"])),
        [("Lines of Code: ", "k"), (n(s["loc"]), "v"), (" ( ", "d"),
         (n(s["loc_add"]) + "++", "g"), (", ", "d"), (n(s["loc_del"]) + "--", "r"), (" )", "d")],
    ]


def render(mode, stats):
    p = PALETTES[mode]
    art = ART.split("\n")
    rows = info_lines(stats)

    art_w = max(len(line) for line in art) * ART_CHAR_W
    info_x = int(ART_X + art_w + PANEL_GAP)
    box_w = int(INFO_W * INFO_CHAR_W + INFO_PAD_X * 2)

    box_h = int(
        INFO_PAD_Y * 2
        + max(len(rows) - 1, 0) * INFO_LINE
        + INFO_FONT
    )

    art_h = ART_Y0 + len(art) * ART_LINE + 25
    svg_h = max(art_h, box_h + 40)
    svg_w = int(info_x + box_w + 15)

    box_y = max((svg_h - box_h) // 2, 15)

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg"',
        f' width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}"',
        ' font-family="Consolas, Menlo, Monaco, \'Liberation Mono\', monospace"',
        f'<rect x="0.5" y="0.5" width="{svg_w - 1}" height="{svg_h - 1}" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    for i, line in enumerate(art):
        out.append(f'<text x="{ART_X}" y="{ART_Y0 + i * ART_LINE}" font-size="{ART_FONT}px" fill="{p["art"]}" xml:space="preserve">{html.escape(line)}</text>')
    out.append(f'<rect x="{info_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="{p["bg"]}" stroke="{p["border"]}"/>')
    for i, row in enumerate(rows):
        if not row:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in row)
        out.append(
            f'<text x="{info_x + INFO_PAD_X}" '
            f'y="{box_y + INFO_PAD_Y + INFO_FONT + i * INFO_LINE}" '
            f'font-size="{INFO_FONT}px" '
            f'xml:space="preserve">{spans}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    stats = fetch_stats()
    print("stats:", stats)
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("wrote dark_mode.svg, light_mode.svg")
