#!/usr/bin/env python3
"""Build the press/review blocks of the book page from the single list _tools/reviews.json.

Run from the repo root:  python3 _tools/build_reviews.py
Writes between markers (never edit inside them by hand):
  books/religious-communities-under-pressure/index.html
    <!-- reviews:trust --> … <!-- /reviews:trust -->   trust line under the title (reviews.json "trust_bar")
    <!-- reviews:press --> … <!-- /reviews:press -->   "In the Press": featured cards, then the compact "Also reviewed" list
  press/index.html
    <!-- reviews:coverage --> … <!-- /reviews:coverage -->   review rows in "Selected coverage" (cites with a "press" object)

reviews.json → "cards": one card per reviewer, in display order.
  featured: true = full card; false = compact line in "Also reviewed" (uses "short" if given, else "quote").
  cites[]: one per source. quote (HTML, no outer quotes), who, role, outlet, url, date (as printed),
           note (e.g. "in Russian"; printed in brackets), short (compact-list quote),
           orig + orig_lang + orig_label: original-language text shown in a collapsible line under the cite,
           press: {title, gloss} → row on /press/.
Typography rule: cites are never bold (font-weight 400).
"""
import json, html, re, sys

D = json.load(open('_tools/reviews.json', encoding='utf-8'))
A = 'target="_blank" rel="noopener" style="color:#8B0000;text-decoration:none;"'


def cite(c):
    who = c['who'] + (', ' + c['role'] if c.get('role') else '')
    note = f" ({c['note']})" if c.get('note') else ''
    return f'— {who} &nbsp;·&nbsp; <a href="{c["url"]}" {A}><em>{c["outlet"]}</em></a>, {c["date"]}{note}'


def orig(c, ind):
    if not c.get('orig'):
        return ''
    return (f'\n{ind}<details class="press-orig"><summary>{c.get("orig_label", "Original")}</summary>'
            f'<p lang="{c["orig_lang"]}">„{c["orig"]}“</p></details>')


def press_block():
    out, more = [], []
    for card in D['cards']:
        if card.get('featured', True):
            rows = []
            for i, c in enumerate(card['cites']):
                st = ' style="margin-top:1.4rem;"' if i else ''
                rows.append(f'      <div class="press-quote"{st}>"{c["quote"]}"</div>\n'
                            f'      <div class="press-cite">{cite(c)}</div>{orig(c, "      ")}')
            out.append('    <div class="press-block">\n' + '\n'.join(rows) + '\n    </div>')
        else:
            for c in card['cites']:
                more.append(f'      <div class="press-more-item"><div class="press-more-quote">"{c.get("short") or c["quote"]}"</div>'
                            f'<div class="press-cite">{cite(c)}</div>{orig(c, "")}</div>')
    if more:
        out.append('    <div class="press-more">\n      <div class="press-more-label">Also reviewed</div>\n'
                   + '\n'.join(more) + '\n    </div>')
    return '\n'.join(out)


def coverage():
    rows = []
    for card in D['cards']:
        for c in card['cites']:
            p = c.get('press')
            if not p:
                continue
            rev = f' ({c["who"]})' if c.get('who') else ''
            note = f' ({c["note"]})' if c.get('note') else ''
            rows.append(f'  <div class="cov-item"><span class="cov-outlet">{p.get("outlet", c["outlet"])}</span> '
                        f'<a href="{c["url"]}" target="_blank" rel="noopener">{p["title"]}{rev}</a> '
                        f'<span class="cov-meta">{c["date"]}{note}</span><span class="cov-gloss">{p["gloss"]}</span></div>')
    return '\n'.join(rows)


def put(path, name, body, inline=False):
    s = open(path, encoding='utf-8').read()
    o, c = f'<!-- reviews:{name} -->', f'<!-- /reviews:{name} -->'
    if o not in s:
        sys.exit(f'marker {o} missing in {path}')
    i, j = s.index(o) + len(o), s.index(c)
    new = body if inline else '\n' + body + '\n'
    s2 = s[:i] + new + s[j:] if inline else s[:i] + new + s[j:].replace(c, c, 1)
    if s2 != s:
        open(path, 'w', encoding='utf-8').write(s2)
        print('updated', path, name)


BOOK = 'books/religious-communities-under-pressure/index.html'
put(BOOK, 'trust', D['trust_bar'], inline=True)
put(BOOK, 'press', press_block())
if '<!-- reviews:coverage -->' in open('press/index.html', encoding='utf-8').read():
    put('press/index.html', 'coverage', coverage())
