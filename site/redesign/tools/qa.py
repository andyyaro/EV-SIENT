import re, sys, os, glob, html.parser
EM_DASH = '\u2014'
R = sys.argv[1]; problems = []
pages = sorted(glob.glob(R + '/*.html'))
def rel(p): return os.path.relpath(p, R)
class P(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.refs=[]; s.inline=[]; s.h1=0; s.ids=[]; s.ext=[]; s.handlers=[]; s.cur=None
    def handle_starttag(s, t, a):
        a = dict(a)
        if 'id' in a: s.ids.append(a['id'])
        if t == 'h1': s.h1 += 1
        for k in ('href', 'src'):
            v = a.get(k)
            if not v: continue
            if v.startswith(('http://', 'https://', '//')): s.ext.append((t, v))
            elif not v.startswith(('#', 'mailto:', 'data:', 'javascript:')): s.refs.append(v)
        if t == 'script' and not a.get('src') and a.get('type') not in ('application/json', 'application/ld+json'): s.cur = 'script'
        for k in a:
            if k.startswith('on'): s.handlers.append((t, k))
    def handle_data(s, d):
        if s.cur == 'script' and d.strip(): s.inline.append(d.strip()[:60])
    def handle_endtag(s, t):
        if t == 'script': s.cur = None
for p in pages:
    src = open(p, encoding='utf-8').read(); x = P(); x.feed(src)
    if x.h1 != 1 and not p.endswith('_template.html'): problems.append(f'{rel(p)}: {x.h1} h1 elements')
    for r in x.refs:
        f = r.split('#')[0].split('?')[0]
        if f and not os.path.exists(os.path.join(R, f)): problems.append(f'{rel(p)}: broken ref {r}')
    for i in x.inline: problems.append(f'{rel(p)}: inline script (blocked by CSP): {i!r}')
    for h in x.handlers: problems.append(f'{rel(p)}: inline handler {h} (blocked by CSP)')
    for t, v in x.ext:
        if t in ('script', 'link', 'img', 'iframe') : problems.append(f'{rel(p)}: external resource <{t}> {v}')
    if 'noindex' not in src: problems.append(f'{rel(p)}: missing noindex meta')
    dup = {i for i in x.ids if x.ids.count(i) > 1}
    if dup: problems.append(f'{rel(p)}: duplicate ids {sorted(dup)}')
for f in glob.glob(R + '/**/*', recursive=True):
    if os.path.isdir(f) or not f.endswith(('.html', '.css', '.js', '.json')) or f.endswith(('icons.js','hig.css','tokens.css','base.css')) or 'BRIEF' in f: continue
    s = open(f, encoding='utf-8').read()
    for m in re.finditer(EM_DASH, s): problems.append(f'{rel(f)}: em dash near {s[max(0,m.start()-40):m.start()+20]!r}')
    if re.search('[\U0001F300-\U0001FAFF☀-➿]', s): problems.append(f'{rel(f)}: emoji or dingbat character')
    if f.endswith('.css'):
        for m in re.finditer(r'#[0-9a-fA-F]{3,8}\b|rgba?\(', s):
            line = s[s.rfind('\n',0,m.start())+1:s.find('\n',m.start())]
            if 'var(' not in line: problems.append(f'{rel(f)}: hard-coded color: {line.strip()[:90]}')
    if f.endswith(('.html', '.js')):
        for m in re.finditer(r'class="[^"]*(card|hig-list|notice|section)[^"]*hig-glass|hig-glass[^"]*(card|hig-list|notice)', s): problems.append(f'{rel(f)}: glass on content: {m.group(0)[:80]}')
        if re.search(r'fetch\(\s*[\'"]https?://', s): problems.append(f'{rel(f)}: external fetch')
print('\n'.join(problems) if problems else 'QA: no problems found'); print(len(problems), 'problems in', len(pages), 'pages')
