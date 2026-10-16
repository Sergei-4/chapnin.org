#!/usr/bin/env python3
"""One RSS feed for the whole site, all languages: /feed.xml

Built from data that already exists, so it needs no upkeep of its own:
  - /writings/ rows (date from data-year="YYYY.MMDD"; title and link in the original language)
  - /talks/ Event JSON-LD (only talks already held)
  - _tools/media.json (recordings; skipped when a talk on the same date is already in)
  - /religious-persecution-russia/ (one item per update, keyed by dateModified)

Items are ordered by PUBLICATION date, not by the date a row was added, so old texts
returned to the bibliography never show up as news. The newest MAX items go in.
lastBuildDate = newest item date, so rerunning without new items changes nothing.

Run from the repo root (build_ru_writings.py and build_media.py call it at the end):
    python3 _tools/build_feed.py
"""
import re, json, html, datetime
import xml.etree.ElementTree as ET
from email.utils import format_datetime

SITE = 'https://chapnin.org'
MAX = 30
TODAY = datetime.date.today()
LANG_NAME = {}  # filled from the pills themselves


def absu(u):
    return u if u.startswith('http') else SITE + u


def rfc822(d):
    return format_datetime(datetime.datetime(d.year, d.month, d.day, 12, 0, tzinfo=datetime.timezone.utc))


def writings():
    s = open('writings/index.html', encoding='utf-8').read()
    out = []
    for m in re.finditer(r'<div class="writing-item" data-type="(\w+)" data-year="([\d.]+)"[^>]*>(.*?)\n    </div>', s, re.S):
        typ, yr, body = m.groups()
        y, _, md = yr.partition('.')
        if len(md) != 4:
            continue                      # year-only rows cannot be dated
        try:
            d = datetime.date(int(y), int(md[:2]), int(md[2:]))
        except ValueError:
            continue
        tattrs = re.search(r'<div class="writing-title"([^>]*)>', body).group(1)
        orig = re.search(r'data-orig="(\w+)"', tattrs).group(1)
        title = html.unescape(re.search(r'data-title-%s="([^"]*)"' % orig, tattrs).group(1))
        pills = re.findall(r'<a class="pill( orig)?" data-lang="(\w+)" href="([^"]+)"[^>]*>([^<]+)</a>', body)
        link = next((h for o, l, h, n in pills if o), pills[0][2] if pills else '/writings/')
        src = re.search(r'<div class="writing-source"[^>]*>(.*?)</div>', body, re.S)
        src = re.sub(r'<[^>]+>', '', html.unescape(src.group(1))).strip() if src else ''
        ttag = re.search(r'<span class="writing-type-tag">([^<]+)</span>', body)
        kind = html.unescape(ttag.group(1)) if ttag else typ.title()
        others = [f'<a href="{html.escape(absu(h))}">{html.escape(html.unescape(n))}</a>' for o, l, h, n in pills if not o]
        desc = html.escape(f'{kind} · {src}' if src else kind)
        if others:
            desc += '<br>Also in: ' + ' · '.join(others)
        out.append(dict(date=d, title=title, link=absu(link), guid=absu(link), desc=desc, lang=orig, cat=kind))
    return out


def talks():
    s = open('talks/index.html', encoding='utf-8').read()
    ld = json.loads(re.search(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "CollectionPage".*?)</script>', s, re.S).group(1))
    out = []
    for li in ld['mainEntity']['itemListElement']:
        e = li['item']
        d = datetime.date.fromisoformat(e['startDate'][:10])
        if d > TODAY:
            continue
        kind = e.get('description', 'Talk').split(' by ')[0]
        where = e.get('location', {}).get('name', '')
        desc = html.escape(e.get('description', ''))
        link = e.get('url') or SITE + '/talks/'
        title = e['name'] if e['name'].lower().startswith(kind.lower()) else f'{kind}: {e["name"]}'
        slug = re.sub(r'[^a-z0-9]+', '-', e['name'].lower()).strip('-')[:40]
        out.append(dict(date=d, title=title, link=link,
                        guid=f'{SITE}/talks/#{d.isoformat()}-{slug}', desc=desc, lang=None, cat=kind, where=where))
    return out


def media(talk_dates):
    out = []
    for x in json.load(open('_tools/media.json', encoding='utf-8')):
        d = datetime.date.fromisoformat(x['date'])
        if d in talk_dates:
            continue
        ru = x['lang'] == 'ru'
        title = x['title_ru'] if ru else x['title_en']
        outlet = x['outlet_ru'] if ru else x['outlet_en']
        page = SITE + ('/ru/media/' if ru else '/media/')
        desc = html.escape(f'{"Видео" if ru else "Video"} · {outlet}') + \
            f'<br><a href="https://www.youtube.com/watch?v={x["yt"]}">YouTube</a>'
        out.append(dict(date=d, title=title, link=page, guid=f'{page}#{x["yt"]}', desc=desc,
                        lang=x['lang'], cat='Video'))
    return out


def key_figures():
    s = open('religious-persecution-russia/index.html', encoding='utf-8').read()
    d = datetime.date.fromisoformat(re.search(r'"dateModified": "([\d-]+)"', s).group(1))
    title = html.unescape(re.search(r'<title>(.*?)</title>', s).group(1))
    desc = html.escape(html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s).group(1)))
    u = SITE + '/religious-persecution-russia/'
    return [dict(date=d, title=f'Updated: {title}', link=u, guid=f'{u}#{d.isoformat()}', desc=desc, lang='en', cat='Data')]


def build():
    T = talks()
    items = writings() + T + media({t['date'] for t in T}) + key_figures()
    items.sort(key=lambda i: i['date'], reverse=True)
    items = items[:MAX]
    newest = items[0]['date']
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">',
         '<channel>',
         '  <title>Sergei Chapnin — new writings, talks and recordings</title>',
         f'  <link>{SITE}/</link>',
         f'  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>',
         '  <description>New publications, talks, recordings and data updates by Sergei Chapnin '
         'on the Russian Orthodox Church, church and state, and religious persecution in Russia. '
         'Items appear in the language of the original.</description>',
         f'  <lastBuildDate>{rfc822(newest)}</lastBuildDate>',
         '  <image>',
         f'    <url>{SITE}/images/icon-512.png</url>',
         '    <title>Sergei Chapnin — new writings, talks and recordings</title>',
         f'    <link>{SITE}/</link>',
         '  </image>']
    for i in items:
        x += ['  <item>',
              f'    <title>{html.escape(i["title"], quote=False)}</title>',
              f'    <link>{html.escape(i["link"])}</link>',
              f'    <guid isPermaLink="false">{html.escape(i["guid"])}</guid>',
              f'    <pubDate>{rfc822(i["date"])}</pubDate>',
              f'    <category>{html.escape(i["cat"], quote=False)}</category>',
              f'    <dc:creator>Sergei Chapnin</dc:creator>']
        if i.get('lang'):
            x.append(f'    <dc:language>{i["lang"]}</dc:language>')
        x += [f'    <description><![CDATA[{i["desc"]}]]></description>', '  </item>']
    x += ['</channel>', '</rss>', '']
    out = '\n'.join(x)
    ET.fromstring(out.encode('utf-8'))          # must be well-formed
    open('feed.xml', 'w', encoding='utf-8').write(out)
    print(f'feed.xml: {len(items)} items, {items[-1]["date"]} … {newest}')


if __name__ == '__main__':
    build()
