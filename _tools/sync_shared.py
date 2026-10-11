#!/usr/bin/env python3
"""Keep the shared parts of every page identical: menu, footer, mobile menu CSS and JS.

The parts live once in _tools/partials/. On each page they sit between markers:

  <!-- shared:nav lang=en active=/bio/ alt=/ru/bio/ -->  ...  <!-- /shared:nav -->
  <!-- shared:footer lang=en updated=2026-09-26 -->      ...  <!-- /shared:footer -->
  <!-- shared:navcss -->  ...  <!-- /shared:navcss -->
  <!-- shared:navjs -->   ...  <!-- /shared:navjs -->

The marker line is the page's settings: menu language, the active menu item,
where the language link (Русский / English) leads, and the page's own
"Last updated" date. Change a partial or a marker, then run from the repo root:

    python3 _tools/sync_shared.py          # rewrite pages
    python3 _tools/sync_shared.py --check  # report pages that are out of sync

A new page only needs the four marker pairs (empty inside); the script fills them.
Pages without markers are migrated once: the existing blocks are found and wrapped.
"""
import re, sys, glob, datetime

PART = '_tools/partials/'
EN_MON = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
RU_MON = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
          'августа', 'сентября', 'октября', 'ноября', 'декабря']

NAV_RE = r'<div class="navbar">.*?\n</div>\n'
FOOT_RE = r'<div class="footer-divider">.*?\n  </div>\n'
CSS_RE = r'<style>\s*/\* mobile hamburger nav \*/.*?</style>\n?'
JS_RE = r"<script>\s*\(function \(\) \{\s*var t = document.querySelector\('\.nav-toggle'\).*?</script>\n?"


def part(name):
    return open(PART + name, encoding='utf-8').read()


def block(name, d, s):
    m = re.search(r'<!-- shared:%s((?: [^>]*?)?) -->\n(.*?)<!-- /shared:%s -->' % (name, name), s, re.S)
    return m


def attrs(txt):
    return dict(re.findall(r'(\w+)=(\S+)', txt))


def fmt_date(iso, lang):
    y, m, d = map(int, iso.split('-'))
    return f'{EN_MON[m]} {d}, {y}' if lang == 'en' else f'{d} {RU_MON[m]} {y}'


def render_nav(a):
    html = part('nav-%s.html' % a['lang']).replace('{alt}', a['alt'])
    act = a.get('active')
    if act and act != '-':
        html, n = re.subn(r'<a href="%s"( class="nav-cta)?"?' % re.escape(act),
                          lambda m: f'<a href="{act}" class="nav-cta active"' if m.group(1) else f'<a href="{act}" class="active"',
                          html, count=1)
        assert n == 1, 'active item not in menu: ' + act
    return html


def render_footer(a):
    return part('footer-%s.html' % a['lang']).replace('{updated}', fmt_date(a['updated'], a['lang']))


# ---------- one-time migration of a page without markers ----------
def migrate(s, f):
    m = re.search(NAV_RE, s, re.S)
    nav = m.group(0)
    lang = 'ru' if 'Сергей Чапнин</a>' in nav else 'en'
    act = re.search(r'<a href="([^"]*)" class="(?:nav-cta )?active"', nav)
    alt = re.search(r'<a href="([^"]*)" class="nav-cta nav-lang"', nav).group(1)
    s = s.replace(nav, f'<!-- shared:nav lang={lang} active={act.group(1) if act else "-"} alt={alt} -->\n'
                       + nav + '<!-- /shared:nav -->\n', 1)
    m = re.search(FOOT_RE, s, re.S)
    ft = m.group(0)
    d = re.search(r'Last updated: (\w+) (\d+), (\d{4})', ft)
    if d:
        iso = f'{d.group(3)}-{EN_MON.index(d.group(1)):02d}-{int(d.group(2)):02d}'
    else:
        d = re.search(r'Обновлено: (\d+) (\S+) (\d{4})', ft)
        iso = f'{d.group(3)}-{RU_MON.index(d.group(2)):02d}-{int(d.group(1)):02d}'
    s = s.replace(ft, f'<!-- shared:footer lang={lang} updated={iso} -->\n' + ft + '  <!-- /shared:footer -->\n', 1)
    m = re.search(CSS_RE, s, re.S)
    if m:
        css = m.group(0)
        std = part('nav-mobile-css.html')
        extra = ''
        if css.rstrip('\n') != std.rstrip('\n'):          # page-specific rules appended inside the block
            head, tail = std.rstrip('\n')[:-len('  </style>')], css
            assert tail.startswith(head), f + ': unexpected mobile CSS'
            extra = '<style>\n' + tail[len(head):].replace('  </style>', '').rstrip() + '\n  </style>\n'
        s = s.replace(css, '<!-- shared:navcss -->\n' + css + '<!-- /shared:navcss -->\n' + extra, 1)
    else:
        s = s.replace('</head>', '<!-- shared:navcss -->\n<!-- /shared:navcss -->\n</head>', 1)
    m = re.search(JS_RE, s, re.S)
    if m:
        s = s.replace(m.group(0), '<!-- shared:navjs -->\n' + m.group(0) + '<!-- /shared:navjs -->\n', 1)
    else:
        s = s.replace('</body>', '<!-- shared:navjs -->\n<!-- /shared:navjs -->\n</body>', 1)
    return s


def sync(s):
    def sub(name, render):
        nonlocal s
        m = block(name, None, s)
        assert m, 'missing marker ' + name
        a = attrs(m.group(1))
        new = f'<!-- shared:{name}{m.group(1)} -->\n' + render(a) + ('  ' if name == 'footer' else '') + f'<!-- /shared:{name} -->'
        s = s[:m.start()] + new + s[m.end():]
    sub('nav', render_nav)
    sub('footer', render_footer)
    sub('navcss', lambda a: part('nav-mobile-css.html'))
    sub('navjs', lambda a: part('nav-toggle-js.html'))
    return s


def pages():
    return sorted(f for f in glob.glob('**/index.html', recursive=True) if not f.startswith('_tools'))


def touch(path, iso=None):
    """Set a page's 'Last updated' date (default: today)."""
    iso = iso or datetime.date.today().isoformat()
    s = open(path, encoding='utf-8').read()
    s = re.sub(r'(<!-- shared:footer [^>]*updated=)\S+( -->)', r'\g<1>' + iso + r'\2', s, count=1)
    open(path, 'w', encoding='utf-8').write(sync(s))


def main():
    check = '--check' in sys.argv
    bad = changed = 0
    for f in pages():
        s0 = open(f, encoding='utf-8').read()
        s = s0 if '<!-- shared:nav ' in s0 else migrate(s0, f)
        s = sync(s)
        if s != s0:
            if check:
                print('out of sync:', f); bad += 1
            else:
                open(f, 'w', encoding='utf-8').write(s); changed += 1
    print(f'{len(pages())} pages, {"%d out of sync" % bad if check else "%d rewritten" % changed}')
    sys.exit(1 if check and bad else 0)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--touch':
        for p in sys.argv[2:]:
            touch(p)
    else:
        main()
