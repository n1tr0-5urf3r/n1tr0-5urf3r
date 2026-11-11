#!/usr/bin/env python3
"""Render a GitHub stats card in the FI Circuit palette (dark + light SVG).

Usage:
  GITHUB_TOKEN=... stats.py USER OUT_DIR          fetch via GraphQL and render
  stats.py --from-json data.json OUT_DIR          render from saved numbers
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

QUERY = """
query($login: String!) {
  user(login: $login) {
    prOpened: pullRequests { totalCount }
    prMerged: pullRequests(states: MERGED) { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) { nodes { stargazerCount } }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
  }
}
"""

THEMES = {
    'dark': dict(bg='#0D1613', border='#1A7B50', title='#7DDFB1', label='#E2EEE8',
                 value='#7DDFB1', node='#5CC799', hole='#0D1613', trace='#359D73'),
    'light': dict(bg='#F4FBF8', border='#0B5A40', title='#0B5A40', label='#10231C',
                  value='#0B5A40', node='#0B5A40', hole='#F4FBF8', trace='#2E8B62'),
}
FONT = "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
W, H = 495, 195


def fetch(login, token):
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': login}}).encode(),
        headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if 'errors' in body:
        sys.exit(f"GraphQL error: {body['errors']}")
    u = body['data']['user']
    cc = u['contributionsCollection']
    return {
        'commits': cc['totalCommitContributions'] + cc['restrictedContributionsCount'],
        'stars': sum(n['stargazerCount'] for n in u['repositories']['nodes']),
        'pr_opened': u['prOpened']['totalCount'],
        'pr_merged': u['prMerged']['totalCount'],
        'issues': u['issues']['totalCount'],
        'contributed': u['repositoriesContributedTo']['totalCount'],
    }


def fmt(n):
    return f'{n / 1000:.1f}k'.replace('.0k', 'k') if n >= 1000 else str(n)


def render(d, t):
    rows = [
        ('Commits (1y)', d['commits']), ('Stars earned', d['stars']),
        ('PRs opened', d['pr_opened']), ('PRs merged', d['pr_merged']),
        ('Issues opened', d['issues']), ('Contributed to', d['contributed']),
    ]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="GitHub stats">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}" stroke-opacity="0.5"/>',
        # circuit traces in the corner, like the boot theme
        f'<g fill="none" stroke="{t["trace"]}" stroke-width="1.5" stroke-opacity="0.45">'
        f'<path d="M{W - 120} 0 V14 l14 14 H{W}"/><path d="M{W - 82} 0 V8 l10 10 H{W}"/></g>',
        f'<g fill="{t["trace"]}" fill-opacity="0.6"><circle cx="{W - 120}" cy="14" r="3"/><circle cx="{W - 82}" cy="8" r="3"/></g>',
        f'<text x="25" y="38" font-family="{FONT}" font-size="17" font-weight="600" fill="{t["title"]}">GitHub Stats</text>',
        f'<line x1="25" y1="50" x2="150" y2="50" stroke="{t["trace"]}" stroke-width="1.5" stroke-opacity="0.6"/>',
        f'<circle cx="150" cy="50" r="2.5" fill="{t["trace"]}"/>',
    ]
    col_x, row_y = (25, 260), (85, 122, 159)
    for i, (label, value) in enumerate(rows):
        x, y = col_x[i % 2], row_y[i // 2]
        out += [
            f'<circle cx="{x + 6}" cy="{y - 5}" r="5" fill="{t["node"]}"/>',
            f'<circle cx="{x + 6}" cy="{y - 5}" r="2" fill="{t["hole"]}"/>',
            f'<text x="{x + 20}" y="{y}" font-family="{FONT}" font-size="13" fill="{t["label"]}">{label}</text>',
            f'<text x="{x + 210}" y="{y}" text-anchor="end" font-family="{FONT}" font-size="14" '
            f'font-weight="700" fill="{t["value"]}">{fmt(value)}</text>',
        ]
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    args = sys.argv[1:]
    if args[0] == '--from-json':
        data, out = json.loads(Path(args[1]).read_text()), Path(args[2])
    else:
        token = os.environ.get('GITHUB_TOKEN') or sys.exit('GITHUB_TOKEN not set')
        data, out = fetch(args[0], token), Path(args[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        (out / f'stats-{name}.svg').write_text(render(data, theme))
    print(json.dumps(data))


if __name__ == '__main__':
    main()
