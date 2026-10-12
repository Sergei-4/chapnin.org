#!/usr/bin/env python3
"""Build /media/ (EN) and /ru/media/ (RU) from the single list _tools/media.json.

Edit only media.json, then run from the repo root:
    python3 _tools/build_media.py && python3 _tools/sync_shared.py
Each entry: yt (YouTube id) or audio (URL), date (event/air date), pub (YouTube publish date),
min, lang (ru|en), kind, outlet_en/ru, title_en/ru, optional start (seconds), note_en/ru,
page (organizer's page), feature_en / feature_ru (order among the featured cards).
Titles of third-party channels are neutral descriptions of the topic, not the channel's headline.
"""
import json, html, re, datetime

D = json.load(open('_tools/media.json', encoding='utf-8'))
E = lambda s: html.escape(s, quote=True)
EN_MON = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
RU_MON = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
KIND = {'interview': ('Interview', 'Интервью'), 'broadcast': ('Broadcast', 'Эфир'), 'podcast': ('Podcast', 'Подкаст'),
        'panel': ('Panel', 'Панель'), 'webinar': ('Webinar', 'Вебинар'), 'lecture': ('Lecture', 'Лекция')}
TODAY = datetime.date.today().isoformat()


def fdate(iso, lang):
    y, m, d = map(int, iso.split('-'))
    return f'{d} {EN_MON[m]} {y}' if lang == 'en' else f'{d} {RU_MON[m]} {y}'


def watch_url(x):
    if 'yt' in x:
        return f"https://www.youtube.com/watch?v={x['yt']}" + (f"&t={x['start']}s" if x.get('start') else '')
    return x['audio']


def meta(x, L):
    parts = [E(x['outlet_' + L])]
    if x.get('min'):
        parts.append(f"{x['min']} min" if L == 'en' else f"{x['min']} мин")
    if x['lang'] != L:
        parts.append('<span class="m-lang">' + ('in Russian' if L == 'en' else 'на английском') + '</span>')
    return ' · '.join(parts)


def actions(x, L):
    a = []
    if 'yt' in x:
        a.append(f'<button type="button" class="m-play" data-yt="{x["yt"]}" data-start="{x.get("start", 0)}">'
                 + ('▶ Watch here' if L == 'en' else '▶ Смотреть здесь') + '</button>')
        a.append(f'<a class="m-ext" href="{E(watch_url(x))}" target="_blank" rel="noopener">YouTube ↗</a>')
    else:
        a.append(f'<a class="m-ext" href="{E(x["audio"])}" target="_blank" rel="noopener">' + ('Listen ↗' if L == 'en' else 'Слушать ↗') + '</a>')
    if x.get('page'):
        a.append(f'<a class="m-ext" href="{E(x["page"])}" target="_blank" rel="noopener">' + ('Event page ↗' if L == 'en' else 'Страница события ↗') + '</a>')
    return '<div class="m-actions">' + ' '.join(a) + '</div>'


def item(x, L, card=False):
    t = x['title_' + L]
    tl = '' if x['lang'] == L or (L == 'ru' and x['lang'] == 'en' and t == x['title_en']) and False else ''
    lang_attr = f' lang="{x["lang"]}"' if t == x['title_' + x['lang']] and x['lang'] != L else ''
    note = f'<div class="m-note">{E(x["note_" + L])}</div>' if x.get('note_' + L) else ''
    kind = KIND[x['kind']][0 if L == 'en' else 1]
    if card:
        return (f'<article class="m-card"><div class="m-kind">{kind} · {fdate(x["date"], L)}</div>'
                f'<h3 class="m-title"{lang_attr}>{E(t)}</h3><div class="m-meta">{meta(x, L)}</div>{note}{actions(x, L)}'
                f'<div class="m-frame" hidden></div></article>')
    return (f'<div class="m-item"><div class="m-date">{fdate(x["date"], L)}</div><div class="m-body">'
            f'<span class="m-kind">{kind}</span><div class="m-title"{lang_attr}>{E(t)}</div>'
            f'<div class="m-meta">{meta(x, L)}</div>{note}{actions(x, L)}<div class="m-frame" hidden></div></div></div>')


def jsonld(L, url, name):
    vids = []
    for i, x in enumerate(sorted(D, key=lambda x: x['date'], reverse=True)):
        o = {"@type": "ListItem", "position": i + 1}
        if 'yt' in x:
            o["item"] = {"@type": "VideoObject", "name": x['title_' + x['lang']], "description": x['title_' + L] + '. ' + x['outlet_' + L],
                         "uploadDate": x['pub'], "duration": f"PT{x['min']}M", "inLanguage": x['lang'],
                         "thumbnailUrl": f"https://i.ytimg.com/vi/{x['yt']}/hqdefault.jpg",
                         "contentUrl": watch_url(x), "embedUrl": f"https://www.youtube-nocookie.com/embed/{x['yt']}"}
        else:
            o["item"] = {"@type": "PodcastEpisode", "name": x['title_en'], "url": x['audio'], "datePublished": x['date'], "inLanguage": x['lang']}
        vids.append(o)
    return json.dumps([{"@context": "https://schema.org", "@type": "CollectionPage", "url": url, "name": name, "inLanguage": L,
                        "about": {"@type": "Person", "@id": "https://chapnin.org/#person", "name": "Sergei Chapnin", "url": "https://chapnin.org/"},
                        "mainEntity": {"@type": "ItemList", "numberOfItems": len(vids), "itemListElement": vids}},
                       {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                           {"@type": "ListItem", "position": 1, "name": "Home" if L == 'en' else "Главная", "item": "https://chapnin.org/" if L == 'en' else "https://chapnin.org/ru/"},
                           {"@type": "ListItem", "position": 2, "name": name, "item": url}]}], ensure_ascii=False, indent=1)


def base_css():
    s = open('talks/index.html', encoding='utf-8').read()
    m = re.search(r'<noscript><link rel="stylesheet"[^\n]*\n\s*\n\s*<style>\n(.*?)</style>', s, re.S)
    keep = [l for l in m.group(1).split('\n') if not re.search(r'\.talk|announce|\.year|\.yr\b|years-', l)]
    return '\n'.join(keep)


MEDIA_CSS = """
    .lang-switch { display: flex; gap: 0.5rem; margin-bottom: 1.2rem; }
    .lang-switch .lang-pill { font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; color: #8B0000; border: 1px solid #E3C9C9; border-radius: 3px; padding: 0.12rem 0.6rem; text-decoration: none; white-space: nowrap; }
    .lang-switch .lang-pill:hover, .lang-switch .lang-pill.active { background: #8B0000; color: #fff; border-color: #8B0000; }
    .page-sub { font-size: 15.5px; color: #4A4A4A; max-width: 68ch; margin: 0.4rem 0 2.2rem; }
    .page-sub a { color: #8B0000; text-decoration: none; font-weight: 600; }
    .m-featured { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 3rem; }
    .m-card { background: #fff; border: 1px solid #E2D8C9; border-top: 3px solid #8B0000; border-radius: 4px; padding: 1.2rem 1.3rem 1.1rem; display: flex; flex-direction: column; }
    .m-card .m-kind { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: #8B0000; font-weight: 700; margin-bottom: 0.5rem; }
    .m-card .m-title { font-family: 'Playfair Display', serif; font-size: 19px; line-height: 1.3; font-weight: 700; color: #2C2C2C; margin-bottom: 0.5rem; }
    .m-card .m-actions { margin-top: auto; padding-top: 0.8rem; }
    .m-h2 { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: #2C2C2C; border-left: 4px solid #8B0000; padding-left: 1rem; margin: 0 0 0.6rem; }
    .m-yr { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #2C2C2C; margin: 1.6rem 0 0.2rem; padding-bottom: 0.3rem; border-bottom: 1px solid #E2D8C9; }
    .m-item { display: grid; grid-template-columns: 8.5rem 1fr; column-gap: 1.1rem; padding: 0.8rem 0; border-bottom: 1px solid #EFE7DB; }
    .m-date { font-size: 12.5px; color: #735E44; font-weight: 600; padding-top: 3px; font-variant-numeric: tabular-nums; }
    .m-item .m-kind { display: inline-block; color: #8B0000; border: 1px solid #E3C9C9; padding: 0.05rem 0.45rem; font-size: 10px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; margin-bottom: 0.3rem; }
    .m-item .m-title { font-family: 'Playfair Display', serif; font-size: 16px; font-weight: 600; line-height: 1.35; color: #2C2C2C; }
    .m-meta { font-size: 12.5px; color: #735E44; margin-top: 0.15rem; line-height: 1.5; }
    .m-lang { font-style: italic; }
    .m-note { font-size: 12.5px; color: #6B5A45; margin-top: 0.25rem; line-height: 1.5; }
    .m-actions { margin-top: 0.45rem; display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; align-items: center; }
    .m-play { background: #8B0000; color: #fff; border: 0; border-radius: 3px; padding: 0.3rem 0.75rem; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
    .m-play:hover { background: #6E0000; }
    .m-ext { font-size: 12.5px; color: #8B0000; text-decoration: none; font-weight: 600; }
    .m-ext:hover { text-decoration: underline; }
    .m-frame { position: relative; width: 100%; aspect-ratio: 16 / 9; margin-top: 0.8rem; background: #2C2C2C; border-radius: 3px; overflow: hidden; }
    .m-frame iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
    @media (max-width: 760px) { .m-featured { grid-template-columns: 1fr; } }
    @media (max-width: 560px) { .m-item { grid-template-columns: 1fr; row-gap: 0.15rem; } }
"""

JS = """<script>
  (function () {
    document.addEventListener('click', function (e) {
      var b = e.target.closest('.m-play'); if (!b) return;
      var box = b.parentNode.parentNode.querySelector('.m-frame');
      if (!box.hidden) { box.hidden = true; box.innerHTML = ''; return; }
      var s = parseInt(b.getAttribute('data-start') || '0', 10);
      box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-yt') + '?autoplay=1&rel=0' + (s ? '&start=' + s : '') +
        '" title="YouTube video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen loading="lazy"></iframe>';
      box.hidden = false;
      if (window.gtag) gtag('event', 'video_play', { video_id: b.getAttribute('data-yt') });
    });
  })();
</script>
"""

T = {
 'en': dict(url='https://chapnin.org/media/', alt='/ru/media/', name='Media & Video',
            title='Media & Video — Interviews, Broadcasts, Recorded Talks | Sergei Chapnin',
            desc='Video and audio of Sergei Chapnin: interviews, broadcasts, and recorded talks on the Russian Orthodox Church, church–state relations, the war against Ukraine, and religious persecution in Russia.',
            h1='Media & Video', sub='Recorded talks, interviews, and broadcasts, newest first. Most of the interviews are in Russian. Full list of talks: <a href="/talks/">Talks &amp; Lectures</a>.',
            feat='Selected recordings', all='All recordings', locale='en_US', home='/'),
 'ru': dict(url='https://chapnin.org/ru/media/', alt='/media/', name='Эфиры и видео',
            title='Эфиры и видео — интервью, эфиры, записи выступлений | Сергей Чапнин',
            desc='Видео и аудио Сергея Чапнина: интервью, эфиры и записи выступлений о Русской православной церкви, Церкви и государстве, войне против Украины и религиозных преследованиях в России.',
            h1='Эфиры и видео', sub='Интервью, эфиры и записи выступлений, сначала новые. Полный список выступлений — <a href="/talks/" hreflang="en">Talks &amp; Lectures</a> (по-английски).',
            feat='Главное', all='Все записи', locale='ru_RU', home='/ru/'),
}


def page(L):
    t = T[L]
    other = 'ru' if L == 'en' else 'en'
    feats = sorted([x for x in D if x.get('feature_' + L)], key=lambda x: x['feature_' + L])
    rows, yr = [], None
    for x in sorted(D, key=lambda x: x['date'], reverse=True):
        y = x['date'][:4]
        if y != yr:
            rows.append(f'<div class="m-yr">{y}</div>'); yr = y
        rows.append(item(x, L))
    pills = (f'<div class="lang-switch"><a class="lang-pill{" active" if L == "en" else ""}" href="/media/"{"" if L == "en" else " hreflang=" + chr(34) + "en" + chr(34) + " lang=" + chr(34) + "en" + chr(34)}>English</a>'
             f'<a class="lang-pill{" active" if L == "ru" else ""}" href="/ru/media/"{"" if L == "ru" else " hreflang=" + chr(34) + "ru" + chr(34) + " lang=" + chr(34) + "ru" + chr(34)}>Русский</a></div>')
    head = f"""<!DOCTYPE html>
<html lang="{L}">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-D5K3GDSNQ0"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-D5K3GDSNQ0');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Sergei Chapnin">
  <title>{E(t['title'])}</title>
  <meta name="description" content="{E(t['desc'])}">
  <link rel="canonical" href="{t['url']}">
  <link rel="alternate" hreflang="en" href="https://chapnin.org/media/">
  <link rel="alternate" hreflang="ru" href="https://chapnin.org/ru/media/">
  <link rel="alternate" hreflang="x-default" href="https://chapnin.org/media/">
  <meta property="og:site_name" content="Sergei Chapnin">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{E(t['name'])} | {'Sergei Chapnin' if L == 'en' else 'Сергей Чапнин'}">
  <meta property="og:description" content="{E(t['desc'])}">
  <meta property="og:url" content="{t['url']}">
  <meta property="og:image" content="https://chapnin.org/images/og/og-home.png">
  <meta property="og:image:alt" content="Sergei Chapnin">
  <meta property="og:locale" content="{t['locale']}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="https://chapnin.org/images/og/og-home.png">
  <meta name="twitter:image:alt" content="Sergei Chapnin">
  <link rel="apple-touch-icon" href="/images/apple-touch-icon.png?v=2">
  <link rel="icon" type="image/png" sizes="32x32" href="/images/favicon.png?v=2">
  <link rel="icon" type="image/x-icon" href="/images/favicon.ico?v=2">
  <meta name="theme-color" content="#F5EFE7">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400;1,600;1,700&family=Lato:wght@400;600&display=swap" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400;1,600;1,700&family=Lato:wght@400;600&display=swap"></noscript>
  <style>
{base_css()}
{MEDIA_CSS}  </style>
  <script type="application/ld+json">
{jsonld(L, t['url'], t['name'])}
  </script>
<!-- shared:navcss -->
<!-- /shared:navcss -->
</head>
<body>
<!-- shared:nav lang={L} active=- alt={t['alt']} -->
<!-- /shared:nav -->

<div class="container">
  {pills}
  <h1 class="page-title">{t['h1']}</h1>
  <p class="page-sub">{t['sub']}</p>

  <h2 class="m-h2">{t['feat']}</h2>
  <div class="m-featured">
{chr(10).join('    ' + item(x, L, card=True) for x in feats)}
  </div>

  <h2 class="m-h2">{t['all']}</h2>
  <div class="m-list">
{chr(10).join('    ' + r for r in rows)}
  </div>

  <!-- shared:footer lang={L} updated={TODAY} -->
  <!-- /shared:footer -->
</div>

{JS}<!-- shared:navjs -->
<!-- /shared:navjs -->
</body>
</html>
"""
    return head


if __name__ == '__main__':
    import os
    for L, path in (('en', 'media/index.html'), ('ru', 'ru/media/index.html')):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
        new = page(L)
        m = re.search(r'<!-- shared:footer lang=\w+ updated=(\S+) -->', old)
        if m:  # keep the page's own date unless content changed
            new = new.replace(f'updated={TODAY}', f'updated={m.group(1)}')
        open(path, 'w', encoding='utf-8').write(new)
        for s in re.findall(r'<script type="application/ld\+json">\n(.*?)\n  </script>', new, re.S):
            json.loads(s)
    print(f'{len(D)} recordings -> media/, ru/media/')
