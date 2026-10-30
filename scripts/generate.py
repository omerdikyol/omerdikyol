"""Generate assets/stats.svg, assets/languages.svg and README.md for the profile."""
import json, os, subprocess, urllib.request
from collections import Counter
from datetime import date

USER = "omerdikyol"
SKIP_LANGS = {"TeX", "HTML", "CSS", "Shell", "Makefile", "Jupyter Notebook", "Dockerfile", "ShaderLab", "HLSL"}
# One repo can contribute at most this many bytes per language, so big Unity projects count but cannot drown the rest.
REPO_CAP = 300_000
COLORS = ["#e5484d", "#f76b15", "#f5d90a", "#30a46c", "#3e63dd", "#8e4ec6"]

def token():
    return os.environ.get("GITHUB_TOKEN") or subprocess.check_output(["gh", "auth", "token"], text=True).strip()

def api(path, query=None):
    body = json.dumps({"query": query}).encode() if query else None
    req = urllib.request.Request(
        "https://api.github.com/" + path, data=body,
        headers={"Authorization": f"Bearer {token()}", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req))

STYLE = """<style>
text{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;fill:#57606a}
.big{fill:#24292f;font-weight:600} .rule{stroke:#d0d7de}
@media (prefers-color-scheme:dark){text{fill:#8b949e} .big{fill:#e6edf3} .rule{stroke:#30363d}}
</style>"""

def collect():
    repos = [r for r in api(f"users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    langs = Counter()
    for r in repos:
        for lang, n in api(f"repos/{USER}/{r['name']}/languages").items():
            if lang not in SKIP_LANGS:
                langs[lang] += min(n, REPO_CAP)
    total = sum(langs.values())
    cc = api("graphql", '{user(login:"%s"){contributionsCollection{totalCommitContributions contributionCalendar{totalContributions}}}}' % USER)["data"]["user"]["contributionsCollection"]
    years = date.today().year - int(api(f"users/{USER}")["created_at"][:4])
    stats = [
        (cc["contributionCalendar"]["totalContributions"], "contributions, last year"),
        (cc["totalCommitContributions"], "commits, last year"),
        (len(repos), "public repos"),
        (len(langs), "languages used"),
        (years, "years on GitHub"),
    ]
    return stats, [(l, n / total) for l, n in langs.most_common(6)]

def stats_svg(stats):
    w, h = 880, 90
    step = w / len(stats)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">', STYLE]
    for i, (n, label) in enumerate(stats):
        x = step * i + step / 2
        out.append(f'<text class="big" x="{x:.0f}" y="44" text-anchor="middle" font-size="34">{n:,}</text>')
        out.append(f'<text x="{x:.0f}" y="68" text-anchor="middle" font-size="12">{label}</text>')
        if i:
            out.append(f'<line class="rule" x1="{step*i:.0f}" y1="18" x2="{step*i:.0f}" y2="74"/>')
    return "\n".join(out) + "</svg>"

def languages_svg(langs):
    w, h, bx, bw = 880, 84, 20, 840
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">', STYLE,
           f'<clipPath id="r"><rect x="{bx}" y="14" width="{bw}" height="12" rx="6"/></clipPath><g clip-path="url(#r)">']
    x = bx
    for (_, share), c in zip(langs, COLORS):
        seg = bw * share / sum(s for _, s in langs)
        out.append(f'<rect x="{x:.1f}" y="14" width="{seg:.1f}" height="12" fill="{c}"/>')
        x += seg
    out.append("</g>")
    step = bw / len(langs)
    for i, ((lang, share), c) in enumerate(zip(langs, COLORS)):
        lx = bx + step * i
        out.append(f'<circle cx="{lx+5:.0f}" cy="56" r="5" fill="{c}"/>')
        out.append(f'<text class="big" x="{lx+16:.0f}" y="60" font-size="13">{lang}</text>')
        out.append(f'<text x="{lx+16:.0f}" y="76" font-size="12">{share:.0%}</text>')
    return "\n".join(out) + "</svg>"

README = """<h1 align="center">Ömer Dikyol</h1>

<p align="center">
Software engineer & researcher in Istanbul, Turkey.<br/>
3+ years across backend systems, applied AI and telecom.<br/>
M.Sc. Computer Engineering at Istanbul Technical University.
</p>

<p align="center"><img src="assets/stats.svg" alt="GitHub numbers"/></p>

<p align="center"><img src="assets/languages.svg" alt="Languages used"/></p>

<p align="center">
<a href="https://omerdikyol.com">website</a> ·
<a href="https://www.linkedin.com/in/omerdikyol">linkedin</a> ·
<a href="https://x.com/omercodes">x</a> ·
<a href="mailto:omerdikyol02@gmail.com">email</a>
</p>

<p align="center"><sub>open to work</sub></p>
"""

if __name__ == "__main__":
    stats, langs = collect()
    open("assets/stats.svg", "w").write(stats_svg(stats))
    open("assets/languages.svg", "w").write(languages_svg(langs))
    open("README.md", "w").write(README)
