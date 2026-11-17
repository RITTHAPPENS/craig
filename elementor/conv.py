"""Prototype HTML -> Elementor V4 atomic composition (XML + configs).

Usage: from conv import Conv; c = Conv(media, slugmap); xml = c.fragment(nodes)
c.cfg / c.cls / c.style / c.meta are keyed by configuration-id.
"""
import re, html, json
from bs4 import NavigableString, Tag, Comment

INLINE = {'b', 'strong', 'em', 'i', 'u', 's', 'sub', 'sup', 'br', 'a', 'span', 'del', 'small', 'abbr', 'mark'}
INLINE_CLS = {'req', 'nowrap', 'br-desk'}            # classed spans allowed inside text (class moved to parent as has-*)
DIVTAGS = {'div', 'header', 'section', 'article', 'aside', 'footer', 'main', 'nav'}
KEEP_ATTR = re.compile(r'^(role|aria-.*|data-.*|hidden|tabindex|title|style|type|for|value|min|max|step)$')


def esc(s):
    return html.escape(s, quote=True)


class Conv:
    def __init__(self, media, link_fn, asset_fn):
        self.media = media          # 'assets/..' -> {id,url}
        self.link = link_fn         # href -> new href
        self.asset = asset_fn       # '../assets/..' -> url
        self.cfg, self.cls, self.style, self.meta = {}, {}, {}, {}
        self.labels = set()
        self.n = 0

    # ---------- helpers
    def cid(self, node, kind):
        self.n += 1
        c = node.get('class', []) if isinstance(node, Tag) else []
        base = (node.name if isinstance(node, Tag) else 'text') + ('.' + c[0] if c else '')
        return f'{base} {self.n}'

    def classes(self, node, extra=()):
        c = list(node.get('class', [])) + list(extra)
        out = []
        for x in c:
            if x not in out:
                out.append(x)
        self.labels.update(out)
        return out

    def keep_attrs(self, node, cid, skip=()):
        a = {}
        for k, v in node.attrs.items():
            if k in skip or k == 'class' or k == 'id':
                continue
            if KEEP_ATTR.match(k):
                if isinstance(v, list):
                    v = ' '.join(v)
                if k.startswith('data-src') or k == 'data-src':
                    v = self.asset(v)
                a[k] = v
        if a:
            self.meta.setdefault(cid, {})['attrs'] = a
        if 'hidden' in a:
            self.cls.setdefault(cid, []).append('x-hidden')

    def set_id(self, node, cid):
        if node.get('id'):
            self.cfg.setdefault(cid, {})['_cssid'] = node['id']

    def text_like(self, node):
        for d in node.descendants:
            if isinstance(d, Tag):
                if d.name not in INLINE:
                    return False
                c = set(d.get('class', []))
                if c and not c <= INLINE_CLS:
                    return False
                if d.name == 'a' and (d.find('svg') or d.find('img')):
                    return False
        return True

    def inner(self, node, parent_cid, allow_a=True):
        """Serialize inline content with allowed tags only."""
        out = []
        for ch in node.children:
            if isinstance(ch, Comment):
                continue
            if isinstance(ch, NavigableString):
                out.append(esc(str(ch)))
                continue
            name = ch.name
            c = set(ch.get('class', []))
            for x in c & INLINE_CLS:
                self.cls.setdefault(parent_cid, []).append('has-' + x)
                self.labels.add('has-' + x)
            if name == 'br':
                for x in c & INLINE_CLS:
                    pass
                out.append('<br>')
                continue
            if name == 'i':
                name = 'em'
            if name in ('small', 'abbr', 'mark'):
                name = 'span'
            body = self.inner(ch, parent_cid, allow_a)
            if name == 'a':
                if not allow_a:
                    out.append(body)
                    continue
                href = self.link(ch.get('href', '#'))
                tb = ' target="_blank" rel="noopener"' if ch.get('target') == '_blank' else ''
                out.append(f'<a href="{esc(href)}"{tb}>{body}</a>')
            else:
                out.append(f'<{name}>{body}</{name}>')
        return ''.join(out)

    @staticmethod
    def norm(s):
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    def linkcfg(self, node):
        d = {'destination': self.link(node.get('href', '#')), 'tag': 'a'}
        if node.get('target') == '_blank':
            d['isTargetBlank'] = True
        return d

    # ---------- main
    def fragment(self, nodes):
        return ''.join(self.node(n) for n in nodes)

    def children(self, node):
        out = []
        for ch in node.children:
            if isinstance(ch, Comment):
                continue
            if isinstance(ch, NavigableString):
                t = self.norm(str(ch))
                if t:
                    cid = self.cid(ch, 'text')
                    self.cfg[cid] = {'tag': 'span', 'paragraph': esc(t)}
                    self.cls[cid] = ['x-t']
                    out.append(f'<e-paragraph configuration-id="{cid}"></e-paragraph>')
                continue
            out.append(self.node(ch))
        return ''.join(out)

    def container(self, node, tag='div', extra=(), link=None):
        cid = self.cid(node, 'div')
        cfg = {}
        if tag != 'div':
            cfg['tag'] = tag
        if link:
            cfg['link'] = link
        self.cfg[cid] = cfg
        self.set_id(node, cid)
        self.cls[cid] = self.classes(node, extra)
        self.keep_attrs(node, cid, skip=('href', 'target', 'rel'))
        inner = self.children(node)
        return f'<e-div-block configuration-id="{cid}">{inner}</e-div-block>'

    def placeholder(self, node, html_str):
        """Element that cannot be built natively: empty div, shim replaces it with real markup."""
        cid = self.cid(node, 'ph')
        self.cfg[cid] = {}
        self.cls[cid] = self.classes(node, ['x-ph'])
        self.meta.setdefault(cid, {})['replace'] = html_str
        return f'<e-div-block configuration-id="{cid}"></e-div-block>'

    # ---------- form (native Elementor form so mails are sent)
    def form(self, f):
        self.in_form = True
        fid = self.cid(f, 'form')
        self.cfg[fid] = {'form-name': 'Projektanfrage',
                         'actions-after-submit': ['email', 'collect-submissions'],
                         'email': {'to': ['info@bauservice-craig.de'],
                                   'subject': 'Neue Projektanfrage über bauservice-craig.de',
                                   'message': '[all-fields]', 'send-as': 'html',
                                   'from-name': 'Website Bauservice Craig', 'from': 'noreply@bauservice-craig.de'}}
        self.cls[fid] = self.classes(f)
        parts = []
        for ch in f.children:
            if isinstance(ch, Tag):
                parts.append(self.form_node(ch))
        sm, em = self.cid(f, 'ok'), self.cid(f, 'err')
        t1, t2 = self.cid(f, 't'), self.cid(f, 't')
        self.cfg[t1] = {'paragraph': 'Danke, Ihre Anfrage ist bei uns angekommen. Wir melden uns persönlich bei Ihnen.'}
        self.cfg[t2] = {'paragraph': 'Das hat leider nicht geklappt. Bitte rufen Sie uns an: 0160 7625394.'}
        self.cls[sm] = ['form-msg', 'form-ok']
        self.cls[em] = ['form-msg', 'form-err']
        self.labels.update(['form-msg', 'form-ok', 'form-err'])
        hp = self.cid(f, 'hp')
        parts.append(f'<e-form-honeypot configuration-id="{hp}"></e-form-honeypot>')
        parts.append(f'<e-form-success-message configuration-id="{sm}"><e-paragraph configuration-id="{t1}"></e-paragraph></e-form-success-message>')
        parts.append(f'<e-form-error-message configuration-id="{em}"><e-paragraph configuration-id="{t2}"></e-paragraph></e-form-error-message>')
        self.in_form = False
        return f'<e-form configuration-id="{fid}">' + ''.join(parts) + '</e-form>'

    def form_node(self, n):
        if isinstance(n, NavigableString):
            return self.node(n)
        name = n.name
        if name == 'label':
            cid = self.cid(n, 'label')
            txt = self.norm(self.inner(n, cid))
            self.cfg[cid] = {'text': txt}
            if n.get('for'):
                self.cfg[cid]['input-id'] = n['for']
            self.cls[cid] = self.classes(n) + self.cls.get(cid, [])
            return f'<e-form-label configuration-id="{cid}"></e-form-label>'
        if name == 'input':
            t = n.get('type', 'text')
            cid = self.cid(n, 'in')
            if t == 'checkbox':
                self.cfg[cid] = {'name': n.get('name', ''), 'value': 'ja', 'required': n.has_attr('required')}
                self.cls[cid] = self.classes(n)
                if n.get('id'):
                    self.meta.setdefault(cid, {}).setdefault('attrs', {})['id'] = n['id']
                return f'<e-form-checkbox configuration-id="{cid}"></e-form-checkbox>'
            self.cfg[cid] = {'type': t if t in ('text', 'email', 'number', 'tel', 'password', 'url') else 'text',
                             'required': n.has_attr('required'), 'autocomplete': n.has_attr('autocomplete')}
            if n.get('id'):
                self.cfg[cid]['_cssid'] = n['id']
            if n.get('placeholder'):
                self.cfg[cid]['placeholder'] = n['placeholder']
            self.cls[cid] = self.classes(n)
            if n.get('autocomplete'):
                self.meta.setdefault(cid, {})['attrs'] = {'autocomplete': n['autocomplete']}
            return f'<e-form-input configuration-id="{cid}"></e-form-input>'
        if name == 'select':
            cid = self.cid(n, 'sel')
            opts = []
            for o in n.find_all('option'):
                v = o.get('value', o.get_text(strip=True))
                opts.append({'key': o.get_text(strip=True), 'value': v})
            self.cfg[cid] = {'name': n.get('name', ''), 'options': opts, 'required': n.has_attr('required')}
            sel = n.find('option', selected=True)
            if sel:
                self.cfg[cid]['has-default-value'] = True
                self.cfg[cid]['value'] = sel.get_text(strip=True)
            self.cls[cid] = self.classes(n)
            if n.get('id'):
                self.meta.setdefault(cid, {}).setdefault('attrs', {})['id'] = n['id']
            return f'<e-form-select configuration-id="{cid}"></e-form-select>'
        if name == 'textarea':
            cid = self.cid(n, 'ta')
            self.cfg[cid] = {'required': n.has_attr('required'), 'rows': int(n.get('rows', 5))}
            if n.get('id'):
                self.cfg[cid]['_cssid'] = n['id']
            self.cls[cid] = self.classes(n)
            return f'<e-form-textarea configuration-id="{cid}"></e-form-textarea>'
        if name == 'button' and n.get('type') == 'submit':
            cid = self.cid(n, 'submit')
            self.cfg[cid] = {'text': self.norm(n.get_text(' ', strip=True))}
            ic = n.find('use')
            extra = ['x-submit']
            if ic:
                extra.append('after-' + ic.get('href', '').lstrip('#'))
            self.cls[cid] = self.classes(n, extra)
            return f'<e-form-submit-button configuration-id="{cid}"></e-form-submit-button>'
        if name == 'p' and 'form-status' in n.get('class', []):
            cid = self.cid(n, 'st')
            self.cfg[cid] = {}
            self.cls[cid] = self.classes(n, ['tg-p'])
            return f'<e-div-block configuration-id="{cid}"></e-div-block>'
        # generic container inside form: recurse with form handling
        cid = self.cid(n, 'div')
        tag = n.name if n.name in DIVTAGS else 'div'
        self.cfg[cid] = {} if tag == 'div' else {'tag': tag}
        extra = [] if n.name in DIVTAGS else ['tg-' + n.name]
        self.cls[cid] = self.classes(n, extra)
        self.keep_attrs(n, cid)
        if self.text_like(n) and n.name in ('p', 'span') and n.get_text(strip=True):
            return self.node(n)
        inner = ''.join(self.form_node(ch) if isinstance(ch, Tag) else self.node(ch) for ch in n.children)
        return f'<e-div-block configuration-id="{cid}">{inner}</e-div-block>'

    def node(self, n):
        if isinstance(n, NavigableString):
            t = self.norm(str(n))
            if not t:
                return ''
            cid = self.cid(n, 'text')
            self.cfg[cid] = {'tag': 'span', 'paragraph': esc(t)}
            self.cls[cid] = ['x-t']
            return f'<e-paragraph configuration-id="{cid}"></e-paragraph>'
        name = n.name
        if name in ('script', 'style', 'source', 'template'):
            return ''
        if name == 'br':
            return ''
        if name == 'svg':
            use = n.find('use')
            ic = use.get('href', use.get('xlink:href', '')).lstrip('#') if use else 'x'
            cid = self.cid(n, 'svg')
            self.cfg[cid] = {}
            self.cls[cid] = self.classes(n, ['tg-svg', ic])
            self.keep_attrs(n, cid)
            return f'<e-div-block configuration-id="{cid}"></e-div-block>'
        if name == 'img':
            src = re.sub(r'\?.*', '', n.get('src', '')).replace('../', '')
            m = self.media.get(src)
            cid = self.cid(n, 'img')
            if m:
                self.cfg[cid] = {'image': {'src': {'id': m['id']}, 'size': 'full'}}
            else:
                self.cfg[cid] = {'image': {'src': {'url': self.asset(n.get('src'))}, 'size': 'full'}}
            self.cls[cid] = self.classes(n)
            if n.get('style'):
                self.style[cid] = n['style']
            self.keep_attrs(n, cid, skip=('style',))
            if n.get('loading') == 'lazy':
                self.meta.setdefault(cid, {}).setdefault('attrs', {})['loading'] = 'lazy'
            return f'<e-image configuration-id="{cid}"></e-image>'
        if name == 'picture':
            img = n.find('img')
            return self.node(img) if img else ''
        if name in ('video', 'input', 'select', 'textarea', 'iframe'):
            h = str(n)
            h = re.sub(r'(src|poster|data-src[\w-]*)="([^"]+)"', lambda m: f'{m.group(1)}="{self.asset(m.group(2))}"', h)
            return self.placeholder(n, h)

        empty = not n.get_text(strip=True) and not n.find(['img', 'svg', 'video', 'input'])
        tl = self.text_like(n)

        # headings / paragraphs / spans
        if name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') and tl and not empty:
            cid = self.cid(n, 'h')
            self.cfg[cid] = {'tag': name}
            self.cfg[cid]['title'] = self.norm(self.inner(n, cid))
            self.set_id(n, cid)
            self.cls[cid] = self.classes(n) + self.cls.get(cid, [])
            self.keep_attrs(n, cid)
            return f'<e-heading configuration-id="{cid}"></e-heading>'
        if name in ('p', 'span') and tl and not empty:
            cid = self.cid(n, 'p')
            self.cfg[cid] = {'paragraph': self.norm(self.inner(n, cid))}
            if name == 'span':
                self.cfg[cid]['tag'] = 'span'
            self.set_id(n, cid)
            self.cls[cid] = self.classes(n) + self.cls.get(cid, [])
            self.keep_attrs(n, cid)
            return f'<e-paragraph configuration-id="{cid}"></e-paragraph>'
        if name == 'a' and tl and not empty:
            cid = self.cid(n, 'a')
            self.cfg[cid] = {'text': self.norm(self.inner(n, cid, allow_a=False)), 'link': self.linkcfg(n)}
            self.set_id(n, cid)
            self.cls[cid] = self.classes(n, ['x-a']) + self.cls.get(cid, [])
            self.keep_attrs(n, cid, skip=('href', 'target', 'rel'))
            return f'<e-button configuration-id="{cid}"></e-button>'
        if name == 'button' and tl and not empty:
            cid = self.cid(n, 'btn')
            self.cfg[cid] = {'text': self.norm(self.inner(n, cid, allow_a=False))}
            self.set_id(n, cid)
            self.cls[cid] = self.classes(n, ['x-btn']) + self.cls.get(cid, [])
            self.keep_attrs(n, cid)
            return f'<e-button configuration-id="{cid}"></e-button>'

        if name == 'form':
            return self.form(n)
        if n.get('data-shortcode'):
            cid = self.cid(n, 'sc')
            self.cfg[cid] = {}
            self.cls[cid] = self.classes(n, ['x-ti'])
            return f'<e-div-block configuration-id="{cid}"></e-div-block>'

        # containers
        if name == 'a':
            return self.container(n, 'a', ['x-a'], link=self.linkcfg(n))
        if name == 'button':
            return self.container(n, 'button', ['x-btn'])
        if name in DIVTAGS:
            return self.container(n, name)
        # every other tag: div with tg-<tag> marker class (CSS is rewritten to match it)
        return self.container(n, 'div', ['tg-' + name])
