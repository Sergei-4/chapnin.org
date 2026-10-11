#!/usr/bin/env python3
"""Build /ru/writings/ from the single database on /writings/.

/writings/index.html is the only place where publications are entered.
This script takes every row that has a Russian version (data-langs contains
"ru") and regenerates the list, tabs and JSON-LD on /ru/writings/index.html
between the RU-LIST / RU-LD markers. Run from the repository root after any
change to /writings/:  python3 _tools/build_ru_writings.py
"""
import re, html, json, sys

SRC, DST = 'writings/index.html', 'ru/writings/index.html'
MON = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
       'августа', 'сентября', 'октября', 'ноября', 'декабря']
MON_NOM = ['', 'январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль',
           'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
EN = {m: i for i, m in enumerate(['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
                                  'August', 'September', 'October', 'November', 'December']) if m}
SEASON = {'Spring': 'весна', 'Summer': 'лето', 'Fall': 'осень', 'Autumn': 'осень', 'Winter': 'зима'}
TYPE_TAG = {'Essay': 'Эссе', 'Article': 'Статья', 'Column': 'Колонка', 'Interview': 'Интервью',
            'Academic Article': 'Научная статья', 'Open Letter': 'Открытое письмо', 'Letter': 'Письмо',
            'Foreword': 'Предисловие', 'Commentary': 'Комментарий', 'Policy Paper': 'Аналитическая записка',
            'Conversation': 'Беседа', 'Book Review': 'Рецензия'}
TABS = [('all', 'Все'), ('essay', 'Эссе и статьи'), ('column', 'Колонки'), ('policy', 'Аналитика'),
        ('academic', 'Научные статьи'), ('interview', 'Интервью'), ('misc', 'Разное'),
        ('letter', 'Открытые письма')]
# source segments that describe other-language versions, not the Russian text
DROP = re.compile(r'translation|transl\.|vert\.|reprint|^with |Двери на Православието|превод|източник|'
                  r'переклад|ИноСМИ|eISSN', re.I)


def ru_date(s):
    s = s.strip()
    m = re.fullmatch(r'(\d{1,2}) (\w+) (\d{4})', s)
    if m and m.group(2) in EN:
        return f'{int(m.group(1))} {MON[EN[m.group(2)]]}'
    m = re.fullmatch(r'(\w+)[–-](\w+) (\d{4})', s)
    if m and m.group(1) in EN and m.group(2) in EN:
        return f'{MON_NOM[EN[m.group(1)]]}–{MON_NOM[EN[m.group(2)]]}'
    m = re.fullmatch(r'(\w+) (\d{4})', s)
    if m and m.group(1) in EN:
        return MON_NOM[EN[m.group(1)]]
    if m and m.group(1) in SEASON:
        return SEASON[m.group(1)]
    if s == 'Undated':
        return 'б/д'
    return ''


LANG_RU = {'en': 'английском', 'bg': 'болгарском', 'uk': 'украинском', 'pl': 'польском', 'el': 'греческом',
           'nl': 'нидерландском', 'de': 'немецком', 'it': 'итальянском', 'fr': 'французском',
           'sr': 'сербском', 'es': 'испанском', 'cs': 'чешском'}
LANG_ORDER = ['en', 'uk', 'pl', 'bg', 'el', 'de', 'fr', 'it', 'nl', 'sr', 'cs', 'es']


def pills(b, skip):
    """(lang, native label, href) for each language button of a row, except `skip`."""
    return [(l, html.unescape(t), html.unescape(h)) for h, l, t in
            [(m.group(2), m.group(1), m.group(3)) for m in
             re.finditer(r'<a class="pill(?: orig)?" data-lang="([a-z]+)" href="([^"]*)"[^>]*>([^<]*)</a>', b)]
            if l != skip]


def link(href, text, lang=None, cls=''):
    e = lambda x: html.escape(x, quote=True)
    ext = href.startswith('http')
    return (f'<a{" class=" + chr(34) + cls + chr(34) if cls else ""} href="{e(href)}"' + (f' lang="{lang}" hreflang="{lang}"' if lang else '')
            + (' target="_blank" rel="noopener"' if ext else '') + f'>{html.escape(text, quote=False)}</a>')


def also_line(also):
    if not also:
        return ''
    return '<div class="ru-also">Другие языки: ' + ' · '.join(link(h, t, l) for l, t, h in also) + '</div>'


def others():
    """Rows with no Russian version, grouped by original language."""
    s = open(SRC, encoding='utf-8').read()
    by = {}
    for b in re.findall(r'<div class="writing-item"(.*?)\n    </div>', s, re.S):
        langs = re.search(r'data-langs="([^"]*)"', b).group(1).split()
        if 'ru' in langs:
            continue
        g = lambda p: (re.search(p, b, re.S) or [None, ''])[1]
        o = g(r'data-orig="([a-z]+)"') or langs[0]
        ps = pills(b, skip=None)
        main = [p for p in ps if p[0] == o] or ps[:1]
        src_div = re.search(r'<div class="writing-source"[^>]*>(.*?)</div>', b, re.S)
        src = html.unescape(re.sub(r'<[^>]+>', '', src_div.group(1))) if src_div else ''
        yr = g(r'data-year="([^"]*)"')
        by.setdefault(o, []).append(dict(year=yr, title=html.unescape(g(r'data-title-%s="([^"]*)"' % o)),
                                         href=main[0][2], src=src, also=[p for p in ps if p[0] != o]))
    for v in by.values():
        v.sort(key=lambda r: -float(r['year']))
    return by


def rows():
    s = open(SRC, encoding='utf-8').read()
    out = []
    for b in re.findall(r'<div class="writing-item"(.*?)\n    </div>', s, re.S):
        langs = re.search(r'data-langs="([^"]*)"', b).group(1).split()
        if 'ru' not in langs:
            continue
        g = lambda p: (re.search(p, b, re.S) or [None, ''])[1]
        title = html.unescape(g(r'data-title-ru="([^"]*)"'))
        if not title:
            sys.exit('Row without data-title-ru: ' + g(r'data-year="([^"]*)"'))
        href = html.unescape(g(r'<a class="pill(?: orig)?" data-lang="ru" href="([^"]*)"'))
        src_div = re.search(r'<div class="writing-source"([^>]*)>(.*?)</div>', b, re.S)
        if src_div and 'data-src-ru' in src_div.group(1):
            src = html.unescape(re.search(r'data-src-ru="([^"]*)"', src_div.group(1)).group(1))
        elif src_div:
            segs = [x for x in html.unescape(re.sub(r'<[^>]+>', '', src_div.group(2))).split(' · ')
                    if x.strip() and not DROP.search(x)]
            src = ' · '.join(segs)
        else:
            src = ''
        tt = html.unescape(g(r'writing-type-tag">([^<]*)'))
        out.append(dict(also=pills(b, skip='ru'), year=g(r'data-year="([^"]*)"'), type=g(r'data-type="([^"]*)"'),
                        date=ru_date(html.unescape(g(r'writing-date">([^<]*)'))),
                        title=title, href=href, src=src, kind=TYPE_TAG.get(tt, tt)))
    out.sort(key=lambda r: -float(r['year']))
    return out


def build():
    R = rows()
    e = lambda x: html.escape(x, quote=True)
    items = []
    for r in R:
        ext = r['href'].startswith('http')
        a = link(r['href'], r['title'], cls='ru-title')
        meta = ' · '.join(x for x in (r['kind'], r['src']) if x)
        items.append(f'<div class="ru-item" data-type="{r["type"]}" data-year="{r["year"]}"><div class="ru-date">{r["date"]}</div>'
                     f'<div>{a}<div class="ru-src">{html.escape(meta, quote=False)}</div>{also_line(r["also"])}</div></div>')
    present = {r['type'] for r in R}
    tabs = ''.join(f'<button class="submenu-tab{" active" if k == "all" else ""}" data-filter="{k}">{lab}</button>'
                   for k, lab in TABS if k == 'all' or k in present)
    years = [int(float(r['year'])) for r in R if float(r['year']) >= 1]
    span = f'{min(years)}–{max(years)}'
    block = (f'<!-- RU-LIST:START (generated by _tools/build_ru_writings.py from /writings/ — do not edit by hand) -->\n'
             f'    <div class="submenu" role="tablist" aria-label="Разделы">{tabs}</div>\n'
             f'    <div class="ru-toolbar"><span class="ru-count" aria-live="polite"></span>'
             f'<label class="ru-sort-l">Порядок <select id="ru-sort"><option value="newest">Сначала новые</option>'
             f'<option value="oldest">Сначала старые</option></select></label></div>\n'
             f'    <div class="ru-list">\n' + '\n'.join(items) + '\n    </div>\n    <!-- RU-LIST:END -->')
    O = others()
    n_other = sum(len(v) for v in O.values())
    groups = []
    for l in sorted(O, key=lambda k: (LANG_ORDER.index(k) if k in LANG_ORDER else 99)):
        li = []
        for r in O[l]:
            y = int(float(r['year']))
            li.append(f'<div class="ru-item"><div class="ru-date">{y if y >= 1 else "б/д"}</div>'
                      f'<div>{link(r["href"], r["title"], l, "ru-title")}<div class="ru-src">{html.escape(r["src"], quote=False)}</div>{also_line(r["also"])}</div></div>')
        groups.append(f'<details class="lang-group"><summary class="lang-head"><span class="year-num">На {LANG_RU.get(l, l)}</span>'
                      f'<span class="year-count">{len(O[l])}</span></summary>\n<div class="lang-body">\n' + '\n'.join(li) + '\n</div></details>')
    other = (f'<!-- RU-OTHER:START (generated by _tools/build_ru_writings.py — do not edit by hand) -->\n'
             f'    <section class="ru-other" id="other-languages" aria-labelledby="other-h">\n'
             f'    <h2 class="ru-other-h" id="other-h">На других языках</h2>\n'
             f'    <p class="ru-other-note">{n_other} текстов, которых нет по-русски. Названия даны на языке оригинала; '
             f'полная база всех публикаций — <a href="/writings/" hreflang="en">на английской странице</a>.</p>\n'
             + '\n'.join(groups) + '\n    </section>\n    <!-- RU-OTHER:END -->')
    def url(h): return h if h.startswith('http') else 'https://chapnin.org' + h
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Публикации на русском",
          "inLanguage": "ru", "url": "https://chapnin.org/ru/writings/",
          "about": {"@type": "Person", "@id": "https://chapnin.org/#person", "name": "Sergei Chapnin", "url": "https://chapnin.org/"},
          "mainEntity": {"@type": "ItemList", "numberOfItems": len(R),
                         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": r['title'], "url": url(r['href'])}
                                             for i, r in enumerate(R)]}}
    ldtxt = json.dumps(ld, ensure_ascii=False, indent=2)
    d = open(DST, encoding='utf-8').read()
    d = re.sub(r'<!-- RU-LIST:START.*?<!-- RU-LIST:END -->', lambda m: block, d, flags=re.S)
    d = re.sub(r'(<script type="application/ld\+json" id="ru-ld">\n).*?(\n  </script>)', lambda m: m.group(1) + ldtxt + m.group(2), d, flags=re.S)
    d = re.sub(r'<!-- RU-OTHER:START.*?<!-- RU-OTHER:END -->', lambda m: other, d, flags=re.S)
    d = re.sub(r'<span class="ru-span">[^<]*</span>', f'<span class="ru-span">{span}</span>', d)
    open(DST, 'w', encoding='utf-8').write(d)
    json.loads(ldtxt)
    print(f'{len(R)} Russian texts, {span}; {n_other} texts in other languages')


if __name__ == '__main__':
    build()
